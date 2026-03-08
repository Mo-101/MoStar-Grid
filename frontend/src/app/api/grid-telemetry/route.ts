import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { driver } from "../../../lib/neo4j";

function neoToNumber(v: unknown): number {
  const maybe = v as { toNumber?: () => number } | null;
  if (maybe && typeof maybe.toNumber === "function") return maybe.toNumber();
  const n = Number(v as number);
  return Number.isNaN(n) ? 0 : n;
}

async function fetchBackendStatus(base: string) {
  try {
    const r = await fetch(`${base}/api/v1/status`, { cache: "no-store", signal: AbortSignal.timeout(20000) });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

async function fetchBackendTelemetry(base: string) {
  try {
    const r = await fetch(`${base}/api/v1/telemetry`, { cache: "no-store", signal: AbortSignal.timeout(20000) });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

export async function GET() {
  const ingestion_run_id = randomUUID();
  const timestamp = new Date().toISOString();
  const GRID_API = process.env.GRID_API_BASE || "http://localhost:8001";

  const [backendStatus, backendTelemetry] = await Promise.all([
    fetchBackendStatus(GRID_API),
    fetchBackendTelemetry(GRID_API),
  ]);

  // Preferred path: real backend telemetry + real backend status
  if (backendTelemetry) {
    const gridState = backendTelemetry?.gridState || {};
    const agentsList = backendTelemetry?.agents || [];

    return NextResponse.json({
      backend: {
        ok: true,
        data: {
          ...(backendStatus || {}),
          system: backendStatus?.system || "MoStar Grid API",
          neo4j: backendStatus?.neo4j || "unknown",
          ollama_model: backendStatus?.model || "Mostar/mostar-ai:latest",
        },
      },
      graph: {
        ok: true,
        stats: {
          totalMoments: gridState.totalMoments ?? 0,
          avgResonance: gridState.resonance ?? 0,
          distinctInitiators: gridState.distinctInitiators ?? 0,
          totalAgents: agentsList.length ?? 0,
          totalNodes: gridState.totalNodes ?? 0,
          totalRelationships: gridState.totalRelationships ?? 0,
          moments24h: gridState.moments24h ?? 0,
          totalArtifacts: gridState.totalArtifacts ?? 0,
          graphDensity: gridState.graphDensity ?? 0,
        },
        latest: backendTelemetry?.moments?.recent || [],
        agents: agentsList,
        layer_nodes: backendTelemetry?.layer_nodes || {},
        relationship_types: backendTelemetry?.relationship_types || {},
      },
      log: {
        entries: backendTelemetry?.moments?.recent || [],
        path: "neo4j://database/canonical",
      },
      generatedAt: timestamp,
    });
  }

  // Direct Neo4j fallback: still real data, no simulated constants
  if (!process.env.NEO4J_URI || !process.env.NEO4J_USER || !process.env.NEO4J_PASSWORD) {
    return NextResponse.json(
      {
        error: "Backend telemetry unavailable and Neo4j not configured for direct fallback",
        generatedAt: timestamp,
      },
      { status: 503 }
    );
  }

  const session = driver.session();
  try {
    const momentsCountRes = await session.run("MATCH (m:MoStarMoment) RETURN count(m) AS c");
    const momentsRes = await session.run("MATCH (m:MoStarMoment) RETURN m ORDER BY m.timestamp DESC LIMIT 15");
    const agentsRes = await session.run("MATCH (a:Agent) RETURN a LIMIT 1000");
    const countsRes = await session.run(
      "MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS rels"
    );
    const activityCountRes = await session.run(
      "MATCH (m:MoStarMoment) WHERE datetime(m.timestamp) > datetime() - duration('P1D') RETURN count(m) AS c"
    );
    const layerRes = await session.run(
      "CALL db.labels() YIELD label MATCH (n) WHERE label IN labels(n) RETURN label, count(n) AS c ORDER BY c DESC LIMIT 20"
    );
    const relTypesRes = await session.run(
      "CALL db.relationshipTypes() YIELD relationshipType MATCH ()-[r]->() WHERE type(r)=relationshipType RETURN relationshipType, count(r) AS c ORDER BY c DESC LIMIT 20"
    );
    const artifactsRes = await session.run("MATCH (a:KnowledgeArtifact) RETURN count(a) AS c");

    const totalMoments = neoToNumber(momentsCountRes.records[0]?.get("c"));
    const totalNodes = neoToNumber(countsRes.records[0]?.get("nodes"));
    const totalRelationships = neoToNumber(countsRes.records[0]?.get("rels"));
    const moments24h = neoToNumber(activityCountRes.records[0]?.get("c"));
    const totalArtifacts = neoToNumber(artifactsRes.records[0]?.get("c"));
    const density = totalNodes > 1 ? totalRelationships / (totalNodes * (totalNodes - 1)) : 0;

    const latestMoments = momentsRes.records.map((r) => {
      const props = r.get("m").properties;
      return {
        ...props,
        resonance_score: neoToNumber(props.resonance_score),
        quantum_id: props.quantum_id || randomUUID(),
        timestamp: props.timestamp || timestamp,
      };
    });

    const layer_nodes: Record<string, number> = {};
    for (const rec of layerRes.records) {
      const label = String(rec.get("label"));
      const c = neoToNumber(rec.get("c"));
      if (c > 0) layer_nodes[label] = c;
    }

    const relationship_types: Record<string, number> = {};
    for (const rec of relTypesRes.records) {
      relationship_types[String(rec.get("relationshipType"))] = neoToNumber(rec.get("c"));
    }

    const agents = agentsRes.records.map((r) => {
      const p = r.get("a").properties;
      return {
        ...p,
        id: p.agent_id || p.id || r.get("a").elementId,
      };
    });

    return NextResponse.json({
      backend: {
        ok: Boolean(backendStatus),
        data: backendStatus || { system: "MoStar Grid API", neo4j: "online" },
      },
      graph: {
        ok: true,
        stats: {
          totalMoments,
          avgResonance:
            latestMoments.length > 0
              ? latestMoments.reduce((a: number, m: any) => a + (Number(m.resonance_score) || 0), 0) / latestMoments.length
              : 0,
          distinctInitiators: new Set(latestMoments.map((m: any) => m.initiator).filter(Boolean)).size,
          totalAgents: agents.length,
          totalNodes,
          totalRelationships,
          moments24h,
          totalArtifacts,
          graphDensity: density,
        },
        latest: latestMoments,
        agents,
        layer_nodes,
        relationship_types,
      },
      log: {
        entries: latestMoments,
        path: "neo4j://direct",
      },
      generatedAt: timestamp,
      provenance: {
        source: "neo4j_direct",
        ingestion_run_id,
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: String(error),
        generatedAt: timestamp,
      },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}

