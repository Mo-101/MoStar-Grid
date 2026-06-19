/**
 * gridApiClient — talks to the MoStar Grid API (:41010).
 *
 * Endpoint contract (server-owned):
 *   GET /api/status            -> full system status (mindgraph, dcx, queue, density)
 *   GET /api/mindgraph/status  -> live graph stats (node/relationship counts, labels)
 *   GET /api/memory/recent     -> recent grid events + woo utterances
 *   GET /api/semantic/advisors -> the live council of soul advisors
 *
 * In preview (LIVE_GRID_SERVICES=false) these return null/empty so callers
 * can fall back to placeholder UI rather than crash.
 */
import { GRID_SERVICES, LIVE_GRID_SERVICES } from "@/config/gridServices";

const TIMEOUT_MS = 8_000;

async function withTimeout<T>(p: Promise<T>, ms = TIMEOUT_MS): Promise<T> {
  return await Promise.race([
    p,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`Grid API request timed out after ${ms}ms`)), ms),
    ),
  ]);
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await withTimeout(fetch(`${GRID_SERVICES.api}${path}`));
  if (!res.ok) throw new Error(`Grid API ${path} ${res.status}: ${await res.text()}`);
  return (await res.json()) as T;
}

export type MindgraphStatus = {
  nodes: number;
  relationships: number;
  labels: string[];
  status: string;
};

export type GridStatus = {
  grid: string;
  cluster_id: string;
  cluster_name: string;
  cluster_region: string;
  mindgraph: MindgraphStatus;
  dcx: { connected: boolean; models: Record<string, string> };
  density: {
    timestamp: string;
    total_nodes: number;
    total_relationships: number;
    label_distribution: Record<string, number>;
  };
  queue: {
    pending: number;
    approved_uncommitted: number;
    committed_today: number;
    rejected_today: number;
  };
};

export type RecentMemory = {
  events: { type: string; cluster: string; content: string; created_at: string }[];
  utterances: { content: string; created_at: string }[];
  retrieved_at: string;
};

export type Advisor = { specialty: string[]; trigger_sample: string[] };
export type AdvisorMap = Record<string, Advisor>;

export async function getGridStatus(): Promise<GridStatus | null> {
  if (!LIVE_GRID_SERVICES) return null;
  try {
    return await getJSON<GridStatus>("/api/status");
  } catch {
    return null;
  }
}

export async function getMindgraphStatus(): Promise<MindgraphStatus | null> {
  if (!LIVE_GRID_SERVICES) return null;
  try {
    return await getJSON<MindgraphStatus>("/api/mindgraph/status");
  } catch {
    return null;
  }
}

export async function getRecentMemory(limit = 10): Promise<RecentMemory | null> {
  if (!LIVE_GRID_SERVICES) return null;
  try {
    return await getJSON<RecentMemory>(`/api/memory/recent?limit=${limit}`);
  } catch {
    return null;
  }
}

export async function getAdvisors(): Promise<AdvisorMap | null> {
  if (!LIVE_GRID_SERVICES) return null;
  try {
    const data = await getJSON<{ ok: boolean; advisors: AdvisorMap }>("/api/semantic/advisors");
    return data.advisors;
  } catch {
    return null;
  }
}
