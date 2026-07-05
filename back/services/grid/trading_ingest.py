"""
MoStar Sovereign Trading Ingest — POST /api/trading/ingest

Receives HMAC-authenticated tick payloads from the Idimikang feed
collector and commits them to the MindGraph as TradingTick nodes.

Authentication : HMAC-SHA256 via X-Sovereign-Signature header.
Privacy        : Timestamps rounded to nearest 100 ms on write.
Residency      : All data stays on the sovereign Dell node.
"""
import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from grid.config import NEO4J_DATABASE

logger = logging.getLogger("trading_ingest")

router = APIRouter(prefix="/api/trading", tags=["trading"])

_SECRET = os.getenv("CONDUIT_SHARED_SECRET", "")


# ── Auth ───────────────────────────────────────────────────────────

def _verify(body: bytes, sig: str) -> bool:
    if not _SECRET:
        logger.warning("CONDUIT_SHARED_SECRET not set — all ingest requests will be rejected")
        return False
    expected = hmac.new(_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


# ── Schema ─────────────────────────────────────────────────────────

class TickData(BaseModel):
    bid_price:        Optional[float] = None
    ask_price:        Optional[float] = None
    bid_qty:          float = 0.0
    ask_qty:          float = 0.0
    last_trade_price: float
    last_trade_qty:   float = 0.0
    volume_24h:       float = 0.0
    volatility_index: float = 0.0


class ComplianceMeta(BaseModel):
    jurisdiction:          str
    anonymization_salt_hash: str
    regime:         Optional[str] = None
    gate:           Optional[str] = None
    side:           Optional[str] = None
    logic_version:  Optional[str] = None
    config_version: Optional[str] = None


class TickPayload(BaseModel):
    timestamp:       int
    venue_id:        str = Field(..., min_length=1, max_length=64)
    symbol:          str = Field(..., min_length=1, max_length=32)
    data:            TickData
    compliance_meta: ComplianceMeta


# ── Ingest endpoint ────────────────────────────────────────────────

@router.post("/ingest")
async def ingest_tick(request: Request):
    # Read raw body first — Pydantic parsing consumes the stream
    body = await request.body()

    # 1. HMAC gate
    sig = request.headers.get("X-Sovereign-Signature", "")
    if not sig or not _verify(body, sig):
        raise HTTPException(status_code=401, detail="invalid_signature")

    # 2. Parse
    try:
        payload = TickPayload.model_validate_json(body)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 3. Privacy — round timestamp to nearest 100 ms
    ts_private = (payload.timestamp // 100) * 100

    tick_id  = f"TICK-{uuid.uuid4().hex[:12].upper()}"
    iso_now  = datetime.now(timezone.utc).isoformat()

    # 4. Commit to MindGraph
    orch = getattr(request.app.state, "orchestrator", None)
    if orch and orch.mindgraph.connected and orch.mindgraph._driver:
        try:
            async with orch.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
                await session.run(
                    """
                    CREATE (t:TradingTick {
                        id:                  $id,
                        timestamp_ms:        $ts,
                        venue_id:            $venue,
                        symbol:              $symbol,
                        last_trade_price:    $price,
                        volatility_index:    $vol,
                        volume_24h:          $vol24,
                        jurisdiction:        $jurisdiction,
                        regime:              $regime,
                        gate:                $gate,
                        side:                $side,
                        logic_version:       $logic_v,
                        config_version:      $config_v,
                        ingested_at:         $now,
                        source:              'idimikang_collector'
                    })
                    """,
                    id=tick_id,
                    ts=ts_private,
                    venue=payload.venue_id,
                    symbol=payload.symbol,
                    price=payload.data.last_trade_price,
                    vol=payload.data.volatility_index,
                    vol24=payload.data.volume_24h,
                    jurisdiction=payload.compliance_meta.jurisdiction,
                    regime=payload.compliance_meta.regime or "",
                    gate=payload.compliance_meta.gate or "",
                    side=payload.compliance_meta.side or "",
                    logic_v=payload.compliance_meta.logic_version or "",
                    config_v=payload.compliance_meta.config_version or "",
                    now=iso_now,
                )
        except Exception as exc:
            # Log and continue — don't block the collector on graph issues
            logger.warning("MindGraph write failed for %s: %s", tick_id, exc)
    else:
        logger.warning("MindGraph unavailable — tick %s not persisted", tick_id)

    logger.info(
        "INGEST  %s  %s  %s  gate=%s  price=%s",
        tick_id, payload.symbol,
        payload.compliance_meta.side or "—",
        payload.compliance_meta.gate or "—",
        payload.data.last_trade_price,
    )

    return {
        "ok":          True,
        "tick_id":     tick_id,
        "symbol":      payload.symbol,
        "venue_id":    payload.venue_id,
        "ts_private":  ts_private,
        "ingested_at": iso_now,
    }


# ── Recent ticks (read) ────────────────────────────────────────────

@router.get("/ticks")
async def recent_ticks(request: Request, symbol: Optional[str] = None, limit: int = 50):
    orch = getattr(request.app.state, "orchestrator", None)
    if not orch or not orch.mindgraph.connected or not orch.mindgraph._driver:
        raise HTTPException(503, "MindGraph not connected")

    query = """
        MATCH (t:TradingTick)
        WHERE $symbol IS NULL OR t.symbol = $symbol
        RETURN t
        ORDER BY t.timestamp_ms DESC
        LIMIT $limit
    """
    try:
        async with orch.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, symbol=symbol, limit=limit)
            records = await result.data()
        return {"ticks": [dict(r["t"]) for r in records], "count": len(records)}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.get("/ticks/summary")
async def tick_summary(request: Request):
    """Aggregate stats across all ingested ticks — per symbol."""
    orch = getattr(request.app.state, "orchestrator", None)
    if not orch or not orch.mindgraph.connected or not orch.mindgraph._driver:
        raise HTTPException(503, "MindGraph not connected")

    query = """
        MATCH (t:TradingTick)
        RETURN
            t.symbol     AS symbol,
            count(t)     AS total,
            avg(t.last_trade_price) AS avg_price,
            max(t.last_trade_price) AS max_price,
            min(t.last_trade_price) AS min_price,
            max(t.timestamp_ms)     AS last_seen_ms,
            collect(DISTINCT t.gate)[0..5] AS gates_seen
        ORDER BY total DESC
    """
    try:
        async with orch.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query)
            records = await result.data()
        return {"symbols": records}
    except Exception as exc:
        raise HTTPException(500, str(exc))
