#!/usr/bin/env python3
"""
reconcile_moments.py — MoStarMoment canon reconciliation

Ruling: live nodes with no canonical match → provenance="imported", not culled.
        live nodes missing required fields  → archived=true, not deleted.
        live nodes matching a canonical id  → provenance confirmed, event_id set.

Run order:
  1. Fetches all MoStarMoment nodes from Neo4j Aura.
  2. Computes deterministic_id() for each node using same hash logic as the schema.
  3. Matches against the canonical ~70 event_ids.
  4. Writes provenance tags and event_ids back to the graph.
  5. Prints three-bucket report: confirmed / imported / archived.

Usage:
  python3 reconcile_moments.py [--dry-run]
"""
import sys
import json
import hashlib
from pathlib import Path

# ── load .env ─────────────────────────────────────────────────────────────────
GRID_ROOT = Path(__file__).resolve().parents[3]
try:
    from dotenv import dotenv_values
    _env = dotenv_values(GRID_ROOT / ".env")
except ImportError:
    import os
    _env = dict(os.environ)

NEO4J_URI      = _env.get("NEO4J_URI", "")
NEO4J_USER     = _env.get("NEO4J_USERNAME", _env.get("NEO4J_USER", "neo4j"))
NEO4J_PASSWORD = _env.get("NEO4J_PASSWORD", "")

if not NEO4J_URI or not NEO4J_PASSWORD:
    sys.exit("ERROR: NEO4J_URI and NEO4J_PASSWORD must be set in .env")

DRY_RUN = "--dry-run" in sys.argv


# ── same deterministic_id as the schema ───────────────────────────────────────

def deterministic_id(payload: dict) -> str:
    canonical = "|".join(
        str(payload.get(k, ""))
        for k in [
            "timestamp",
            "initiator",
            "receiver",
            "description",
            "trigger_type",
            "resonance_score",
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── required fields (must all be present and non-empty for import-eligible) ───

REQUIRED = ("timestamp", "initiator", "receiver", "description", "trigger_type")


def is_sludge(props: dict) -> tuple[bool, str]:
    for f in REQUIRED:
        v = props.get(f)
        if not v or (isinstance(v, str) and not v.strip()):
            return True, f"missing or empty field: {f!r}"
    rs = props.get("resonance_score")
    if rs is None:
        return True, "missing resonance_score"
    try:
        if not (0.0 <= float(rs) <= 1.0):
            return True, f"resonance_score out of range: {rs}"
    except (TypeError, ValueError):
        return True, f"resonance_score not numeric: {rs}"
    return False, ""


# ── load canonical event_ids from the schema ──────────────────────────────────

def load_canonical_ids() -> dict[str, dict]:
    """
    Import MoStarMoments from the canonical schema and return
    {event_id: moment_dict} for fast lookup.

    The schema file lives at back/services/mostar_moments/ or similar.
    We import it directly so the canonical list is always the source of truth.
    """
    # Try to import from wherever the schema landed in the project
    import importlib.util, os

    candidates = [
        GRID_ROOT / "back" / "services" / "moments" / "moments.py",
        GRID_ROOT / "back" / "services" / "mostar_moments" / "moments.py",
        GRID_ROOT / "back" / "data" / "moments.py",
        GRID_ROOT / "core" / "moments.py",
    ]
    # Also search the whole tree for a file containing MoStarMoments
    schema_file = None
    for c in candidates:
        if c.exists():
            schema_file = c
            break

    if schema_file is None:
        # Walk limited depth for a file exporting CANONICAL_MOMENTS
        for p in GRID_ROOT.rglob("*.py"):
            if p.name.startswith("_"):
                continue
            try:
                if b"CANONICAL_MOMENTS" in p.read_bytes():
                    schema_file = p
                    break
            except Exception:
                pass

    if schema_file is None:
        print("[WARN] canonical moments schema not found on disk — "
              "canonical match will be skipped, all nodes tagged 'imported'")
        return {}

    spec = importlib.util.spec_from_file_location("_moments_schema", schema_file)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    canonical = getattr(mod, "CANONICAL_MOMENTS", None)
    if not canonical:
        print(f"[WARN] CANONICAL_MOMENTS not found in {schema_file}")
        return {}

    result = {}
    for m in canonical:
        d = m.to_dict() if hasattr(m, "to_dict") else vars(m)
        eid = d.get("event_id") or deterministic_id(d)
        result[eid] = d
    print(f"[INFO] loaded {len(result)} canonical moment ids from {schema_file.relative_to(GRID_ROOT)}")
    return result


# ── neo4j interaction ─────────────────────────────────────────────────────────

def fetch_live_nodes(driver) -> list[dict]:
    with driver.session() as session:
        result = session.run(
            "MATCH (n:MoStarMoment) "
            "RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS props"
        )
        return [{"eid": r["eid"], "props": dict(r["props"])} for r in result]


def apply_tags(driver, updates: list[dict]) -> None:
    """
    updates: list of {eid, set_props} where set_props is a dict of properties to SET.
    """
    if not updates:
        return
    with driver.session() as session:
        for u in updates:
            session.run(
                "MATCH (n) WHERE elementId(n) = $eid "
                "SET n += $props",
                eid=u["eid"], props=u["set_props"]
            )


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        from neo4j import GraphDatabase
    except ImportError:
        sys.exit("ERROR: neo4j driver not installed — pip install neo4j")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # verify connection
    with driver.session() as s:
        s.run("RETURN 1").single()
    print("[INFO] connected to Neo4j Aura")

    canonical_ids = load_canonical_ids()
    live_nodes    = fetch_live_nodes(driver)
    print(f"[INFO] fetched {len(live_nodes)} MoStarMoment nodes from graph")

    confirmed  = []
    imported_  = []
    archived   = []

    updates = []

    for node in live_nodes:
        eid   = node["eid"]
        props = node["props"]

        # check sludge first
        sludge, reason = is_sludge(props)
        if sludge:
            archived.append({"eid": eid, "reason": reason, "props": props})
            updates.append({
                "eid": eid,
                "set_props": {
                    "archived":        True,
                    "archive_reason":  reason,
                    "provenance":      props.get("provenance", "unknown"),
                }
            })
            continue

        # compute deterministic id from live node's own fields
        computed_id = deterministic_id(props)

        if computed_id in canonical_ids:
            confirmed.append({"eid": eid, "event_id": computed_id, "props": props})
            updates.append({
                "eid": eid,
                "set_props": {
                    "event_id":   computed_id,
                    "provenance": canonical_ids[computed_id].get("provenance", "recorded"),
                    "reconciled": True,
                }
            })
        else:
            # valid fields, no canonical match → imported
            existing_id = props.get("event_id")
            assigned_id = existing_id or computed_id
            imported_.append({"eid": eid, "event_id": assigned_id, "props": props})
            updates.append({
                "eid": eid,
                "set_props": {
                    "event_id":   assigned_id,
                    "provenance": props.get("provenance", "imported"),
                    "reconciled": True,
                }
            })

    # ── report ────────────────────────────────────────────────────────────────
    print()
    print("─── RECONCILIATION RESULT ───────────────────────────────")
    print(f"  confirmed  (matches canonical spine)  : {len(confirmed):>6}")
    print(f"  imported   (valid, no canonical match): {len(imported_):>6}")
    print(f"  archived   (missing required fields)  : {len(archived):>6}")
    print(f"  total live nodes                      : {len(live_nodes):>6}")
    print()

    if archived:
        print("── archived nodes (sludge) ──")
        for a in archived[:20]:
            print(f"  {a['eid'][:40]}  reason={a['reason']}")
        if len(archived) > 20:
            print(f"  … and {len(archived) - 20} more")
        print()

    if DRY_RUN:
        print("[DRY RUN] no writes made to graph")
        print(f"          would apply {len(updates)} updates")
    else:
        print(f"[WRITE] applying {len(updates)} provenance tags …")
        apply_tags(driver, updates)
        print("[DONE]")

    driver.close()

    # write JSON report
    report_path = GRID_ROOT / "core" / "ops" / "scripts" / "reconcile_moments_report.json"
    report = {
        "confirmed_count":  len(confirmed),
        "imported_count":   len(imported_),
        "archived_count":   len(archived),
        "total":            len(live_nodes),
        "dry_run":          DRY_RUN,
        "archived_sample":  [{"eid": a["eid"], "reason": a["reason"]} for a in archived[:50]],
        "confirmed_sample": [{"eid": c["eid"], "event_id": c["event_id"]} for c in confirmed[:10]],
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"[INFO] report written to {report_path.relative_to(GRID_ROOT)}")


if __name__ == "__main__":
    main()
