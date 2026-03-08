/**
 * Executor Status API
 * -------------------
 * Returns the live state of the Mo Executor from Neo4j.
 *
 * Data comes from two real sources:
 *   1. ExecutorHeartbeat node — written by mo_executor.py on every cycle
 *   2. ExecutionEvent nodes   — written by mo_executor.py per processed moment
 *
 * If the heartbeat is older than 60s, Mo is considered STALLED.
 * If no heartbeat node exists, Mo has NEVER run.
 */

import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { driver } from "../../../lib/neo4j";

function neoToNumber(v: unknown): number {
    const maybe = v as { toNumber?: () => number } | null;
    if (maybe && typeof maybe.toNumber === "function") return maybe.toNumber();
    const n = Number(v);
    return Number.isNaN(n) ? 0 : n;
}

function neoToString(v: unknown): string {
    if (v == null) return "";
    if (typeof v === "object" && "toString" in (v as object)) {
        return (v as { toString(): string }).toString();
    }
    return String(v);
}

export async function GET() {
    const ingestion_run_id = randomUUID();
    const now = new Date();
    const timestamp = now.toISOString();

    if (
        !process.env.NEO4J_URI ||
        !process.env.NEO4J_USER ||
        !process.env.NEO4J_PASSWORD
    ) {
        return NextResponse.json(
            {
                executor: null,
                provenance: {
                    source: "error",
                    timestamp,
                    ingestion_run_id,
                    error: "Neo4j not configured",
                },
            },
            { status: 503 }
        );
    }

    const session = driver.session();
    try {
        const heartbeatResult = await session.run(`
            MATCH (hb:ExecutorHeartbeat)
            RETURN
              hb.executor_id      AS executor_id,
              hb.last_heartbeat   AS last_heartbeat,
              hb.cycle_count      AS cycle_count,
              hb.total_processed  AS total_processed,
              hb.status           AS status
            LIMIT 1
          `);

        const eventsResult = await session.run(`
            MATCH (e:ExecutionEvent)
            RETURN
              e.id              AS id,
              e.executor_id     AS executor_id,
              e.processed_at    AS processed_at,
              e.action          AS action,
              e.reasoning_summary AS reasoning_summary
            ORDER BY e.processed_at DESC
            LIMIT 10
          `);

        const pendingResult = await session.run(`
            MATCH (m:MoStarMoment)
            WHERE m.mo_processed IS NULL
            RETURN count(m) AS pending_count
          `);

        // Parse heartbeat
        const hbRecord = heartbeatResult.records[0] ?? null;
        let executorAlive = false;
        let stalledMs = 0;

        const heartbeat = hbRecord
            ? {
                executor_id: neoToString(hbRecord.get("executor_id")),
                last_heartbeat: neoToString(hbRecord.get("last_heartbeat")),
                cycle_count: neoToNumber(hbRecord.get("cycle_count")),
                total_processed: neoToNumber(hbRecord.get("total_processed")),
                status: neoToString(hbRecord.get("status")),
            }
            : null;

        if (heartbeat?.last_heartbeat) {
            const lastBeat = new Date(heartbeat.last_heartbeat);
            stalledMs = now.getTime() - lastBeat.getTime();
            executorAlive = stalledMs < 60_000; // alive if beat within last 60s
        }

        // Parse execution events
        const events = eventsResult.records.map((r) => ({
            id: neoToString(r.get("id")),
            executor_id: neoToString(r.get("executor_id")),
            processed_at: neoToString(r.get("processed_at")),
            action: neoToString(r.get("action")),
            reasoning_summary: neoToString(r.get("reasoning_summary")),
        }));

        const pendingCount = neoToNumber(
            pendingResult.records[0]?.get("pending_count") ?? 0
        );

        // Determine status label
        let executorStatus: string;
        if (!heartbeat) {
            executorStatus = "NEVER_RUN";
        } else if (executorAlive) {
            executorStatus = "ALIVE";
        } else {
            executorStatus = "STALLED";
        }

        return NextResponse.json({
            executor: {
                status: executorStatus,
                is_alive: executorAlive,
                stalled_ms: stalledMs,
                heartbeat,
                recent_events: events,
                pending_moments: pendingCount,
            },
            provenance: {
                source: "neo4j",
                timestamp,
                ingestion_run_id,
            },
        });
    } catch (error) {
        return NextResponse.json(
            {
                executor: null,
                provenance: {
                    source: "error",
                    timestamp,
                    ingestion_run_id,
                    error: error instanceof Error ? error.message : "Unknown error",
                },
            },
            { status: 503 }
        );
    } finally {
        await session.close();
    }
}
