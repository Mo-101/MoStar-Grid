/**
 * Grid Telemetry — proxies to the sovereign backend
 * Fetches /api/v1/telemetry and /api/v1/status independently
 * Maps to TelemetryPayload shape for useGridTelemetry
 */

import { NextResponse } from "next/server";

const GRID_API =
  process.env.GRID_API_BASE ??
  process.env.NEXT_PUBLIC_GRID_API_BASE ??
  "http://127.0.0.1:7001";

console.log("[TELEMETRY_ROUTE] Using GRID_API:", GRID_API);

async function safeFetch(url: string, timeoutMs = 12000) {
  console.log(`[TELEMETRY_ROUTE] Fetching: ${url}`);
  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(timeoutMs),
      cache: "no-store",
    });
    if (!res.ok) {
      console.warn(`[TELEMETRY_ROUTE] Fetch failed for ${url}: ${res.status}`);
      return { ok: false, error: `HTTP ${res.status}`, data: null };
    }
    const data = await res.json();
    console.log(`[TELEMETRY_ROUTE] Success for ${url}`);
    return { ok: true, error: null, data };
  } catch (err) {
    console.error(`[TELEMETRY_ROUTE] Error fetching ${url}:`, err);
    return { ok: false, error: err instanceof Error ? err.message : String(err), data: null };
  }
}

export async function GET() {
  const [tel, status] = await Promise.all([
    safeFetch(`${GRID_API}/api/v1/telemetry`, 12000),
    safeFetch(`${GRID_API}/api/v1/status`, 12000),
  ]);

  const telData = tel.data;
  const statusData = status.data;

  // If telemetry failed but status worked, or vice versa, we still return the aggregate
  const agentsCount = Array.isArray(telData?.agents)
    ? telData.agents.length
    : (telData?.agents ?? 0);

  return NextResponse.json({
    backend: {
      ok: status.ok,
      data: statusData ?? undefined,
      error: status.ok ? undefined : status.error,
    },
    graph: {
      ok: tel.ok ?? false,
      stats: {
        totalMoments: telData?.total_moments ?? telData?.stats?.totalMoments ?? 0,
        avgResonance: telData?.avg_resonance ?? telData?.stats?.avgResonance ?? null,
        distinctInitiators: agentsCount,
      },
      latest: telData?.recent_moments ?? telData?.latest ?? [],
      agents: telData?.agents ?? [],
      layer_nodes: telData?.layer_nodes ?? {},
      layer_moments: telData?.layer_moments ?? {},
      total_nodes: telData?.total_nodes ?? 0,
      moments_24h: telData?.moments_24h ?? 0,
      agentWarning: agentsCount === 0
        ? "No agents found in graph — Neo4j may be offline"
        : undefined,
      error: tel.ok ? undefined : (telData?.error ?? tel.error ?? "Telemetry unavailable"),
    },
    log: {
      entries: telData?.recent_moments ?? telData?.latest ?? [],
      path: "neo4j://MoStarMoment",
    },
    generatedAt: telData?.timestamp ?? new Date().toISOString(),
  });
}
