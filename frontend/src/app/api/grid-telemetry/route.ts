/**
 * Grid Telemetry — proxies to the sovereign backend
 * Falls back to self-contained serverless mode on Vercel
 */

import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { driver } from "../../../lib/neo4j";

function neoToNumber(v: unknown): number {
  // neo4j Integer has toNumber; fall back to Number()
  const maybe = v as { toNumber?: () => number } | null;
  if (maybe && typeof maybe.toNumber === "function") {
    return maybe.toNumber();
  }
  const n = Number(v as number);
  return Number.isNaN(n) ? 0 : n;
}

export async function GET() {
  const ingestion_run_id = randomUUID();
  const timestamp = new Date().toISOString();
  const GRID_API = process.env.GRID_API_BASE || "http://127.0.0.1:7001";

  // Attempt to proxy to the sovereign backend first
  try {
    const backendRes = await fetch(`${GRID_API}/api/v1/telemetry`, { cache: 'no-store' });
    if (backendRes.ok) {
      const data = await backendRes.json();

      // Safety check for stats to avoid "Cannot read properties of undefined"
      const gridState = data?.gridState || {};
      const agentsList = data?.agents || [];

      return NextResponse.json({
        backend: {
          ok: true,
          data: {
            system: "MoStar Grid Core",
            neo4j: "connected",
            ollama_model: "Mostar/mostar-ai:latest",
            ...(data?.backend || {})
          }
        },
        graph: {
          ok: true,
          stats: {
            totalMoments: gridState.totalMoments ?? 0,
            avgResonance: gridState.resonance ?? 0,
            distinctInitiators: gridState.distinctInitiators ?? 0,
            totalAgents: agentsList.length ?? 0
          },
          latest: data?.moments?.recent || [],
          agents: agentsList,
          layer_nodes: data?.layer_nodes || {}
        },
        log: {
          entries: data?.moments?.recent || [],
          path: "neo4j://database/canonical"
        },
        generatedAt: timestamp
      });
    }
  } catch (e) {
    console.warn("Backend proxy failed, falling back to direct Neo4j query", e);
  }

  // Fallback: Direct Neo4j Query
  if (!process.env.NEO4J_URI || !process.env.NEO4J_USER || !process.env.NEO4J_PASSWORD) {
    return NextResponse.json(
      { error: "Neo4j not configured" },
      { status: 503 }
    );
  }

  const session = driver.session();
  try {
    const momentsCountRes = await session.run(`MATCH (m:MoStarMoment) RETURN count(m) AS c`);

    const momentsRes = await session.run(`
      MATCH (m:MoStarMoment) 
      RETURN m ORDER BY m.timestamp DESC LIMIT 15
    `);

    const agentsRes = await session.run(`
      MATCH (a:Agent)
      RETURN a LIMIT 1000
    `);

    const layerLabels = ["MeshIntelligence", "PublicInterface", "ExecutionRing", "LedgerSpine", "CovenantKernel", "SoulLayer", "MindLayer", "BodyLayer"];
    const layerResults: Record<string, number> = {};
    for (const label of layerLabels) {
      const res = await session.run(`MATCH (n:${label}) RETURN count(n) AS c`);
      const count = neoToNumber(res.records[0].get("c"));
      if (count > 0) layerResults[label] = count;
    }

    const latestMoments = momentsRes.records.map(r => {
      const props = r.get("m").properties;
      return {
        ...props,
        resonance_score: neoToNumber(props.resonance_score),
        quantum_id: props.quantum_id || randomUUID(),
        timestamp: props.timestamp || timestamp
      };
    });

    const totalMomentsCount = neoToNumber(momentsCountRes.records[0].get("c"));

    return NextResponse.json({
      backend: { ok: true, data: { neo4j: "connected" } },
      graph: {
        ok: true,
        stats: {
          totalMoments: totalMomentsCount,
          avgResonance: 0.98,
          distinctInitiators: new Set(latestMoments.map((m: any) => m.initiator).filter(Boolean)).size || 1,
          totalAgents: neoToNumber(agentsRes.records.length)
        },
        latest: latestMoments,
        agents: agentsRes.records.map(r => {
          const p = r.get("a").properties;
          return {
            ...p,
            id: p.agent_id || p.id || r.get("a").elementId
          };
        }),
        layer_nodes: layerResults
      },
      log: {
        entries: latestMoments,
        path: "neo4j://direct"
      },
      generatedAt: timestamp
    });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  } finally {
    await session.close();
  }
}
