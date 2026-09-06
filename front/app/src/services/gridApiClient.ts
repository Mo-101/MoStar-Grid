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
  const res = await withTimeout(fetch(`${GRID_SERVICES.api}${path}`, { cache: "no-store" }));
  if (!res.ok) throw new Error(`Grid API ${path} ${res.status}: ${await res.text()}`);
  return (await res.json()) as T;
}

/**
 * Mind Graph semantic accounting.
 *
 * The classification layer is owned by the backend, never derived here. The
 * conservation law is
 *
 *     total_graph_nodes = knowledge + operational + audit + system + test + unknown
 *
 * with every physical node assigned exactly once. Consumers must verify that
 * identity before speaking any class count (see isPartitionSound).
 *
 * Optional by design: the accounting layer may not be deployed yet, and its
 * absence must make the Grid quieter about knowledge scale, never more
 * confident.
 */
export type GraphSemanticAccounting = {
  total_graph_nodes: number;
  knowledge_nodes: number;
  operational_nodes: number;
  audit_nodes: number;
  system_nodes: number;
  test_nodes: number;
  unknown_nodes: number;
  classification_schema_version: string;
  measured_at: string;
  database_identity?: string;
  evidence_digest?: string;
};

export type MindgraphStatus = {
  /**
   * Raw MATCH (n) RETURN count(n). This is TOTAL graph population and is not
   * a knowledge-corpus measurement. Never surface it as "knowledge nodes" —
   * use semantic_accounting for anything that speaks about knowledge scale.
   */
  nodes: number;
  relationships: number;
  /** Present only once the backend classification layer is deployed. */
  semantic_accounting?: GraphSemanticAccounting | null;
  labels: string[];
  scope: "database";
  database: string;
  cluster: {
    cluster_id: string;
    nodes: number;
    relationships: number;
    labels: string[];
  };
  status: string;
};

export type GridStatus = {
  grid: string;
  cluster_id: string;
  cluster_name: string;
  cluster_region: string;
  mindgraph: MindgraphStatus;
  dcx: {
    /** Ollama transport reachable. NOT a claim that the trinity is sealed. */
    connected: boolean;
    /** Configured layer -> model tag. Declared, not measured. */
    models: Record<string, string>;
    /**
     * Measured trinity state. /api/status is the cheap path and can never
     * report SEALED — sealing requires live per-model validation, which only
     * the deep probe (/api/health) performs. Optional so an older server
     * degrades to UNVERIFIED rather than being guessed at.
     */
    state?: "UNREACHABLE" | "ABSENT" | "PARTIAL" | "LOADED" | "DEGRADED" | "SEALED";
    sealed?: boolean;
    expected_models?: Record<string, string>;
    present_models?: string[];
    missing_models?: string[];
    validated_models?: string[];
    failed_models?: { model: string; reason: string }[];
    checked_at?: string | null;
  };
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
  feed_state: "LIVE" | "NO_CURRENT_SIGNALS";
  freshness_window_seconds: number;
  archived_records_excluded: number;
};

export type Advisor = { specialty: string[]; trigger_sample: string[]; last_seen?: string };
export type AdvisorMap = Record<string, Advisor>;

export type EpistemicState = "CONSENSUS" | "DIVERGENT" | "PARTIAL" | "STALE" | "UNAVAILABLE";

export type AfricaWeatherLocation = {
  location_id: string;
  location: string;
  country: string;
  region: string;
  latitude?: number | null;
  longitude?: number | null;
  /** WMO code — Open-Meteo only. Absent for other providers; fall back to `summary`. */
  weather_code?: number | null;
  temperature_c: number | null;
  feels_like_c: number | null;
  humidity_pct: number | null;
  wind_kph: number | null;
  wind_direction_deg: number | null;
  precipitation_mm: number | null;
  precipitation_probability: number | null;
  summary: string;
  agreement_score: number;
  provider_count: number;
  providers_used: string[];
  epistemic_state: EpistemicState;
  temperature_spread_c: number | null;
  freshness_seconds: number | null;
  observed_at: string | null;
  retrieved_at?: string | null;
  time_basis?: "provider_observation" | "retrieval_time";
  source_observations?: Array<Record<string, unknown>>;
  forecast?: { temperature_c: number[]; precipitation_probability: Array<number | null> };
};

export type SovereigntyReport = {
  report_id: string;
  jurisdiction_id: string;
  jurisdiction: string;
  generated_at: string;
  state: "PARTIAL" | "CURRENT" | "STALE" | "CONTESTED";
  findings: Array<{
    section: string;
    statement: string;
    epistemic_type: string;
    confidence: string;
  }>;
  source_coverage: string[];
  contested: boolean;
  freshness: { state: string; generated_at: string };
  provenance_refs: string[];
};

export type AfricaSenses = {
  generated_at: string;
  served_at: string;
  cache: "HIT" | "MISS";
  scope: "Africa";
  coverage: { jurisdictions: number; weather_hubs_observed: number; regions_observed: string[] };
  weather: {
    state: string;
    providers: Record<string, string>;
    locations: AfricaWeatherLocation[];
  };
  health: {
    state: string;
    providers: Record<string, string>;
    signals: Record<string, { status: string; data?: Record<string, unknown> }>;
  };
  sovereignty: { state: string; reports: SovereigntyReport[] };
  canonical_report: {
    report_id: string;
    canonical: true;
    generated_at: string;
    segments: string[];
    text: string;
    source_digest: string;
    source_refs: string[];
  };
};

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

export async function getAfricaSenses(): Promise<AfricaSenses | null> {
  if (!LIVE_GRID_SERVICES) return null;
  try {
    return await getJSON<AfricaSenses>("/api/senses/africa");
  } catch {
    return null;
  }
}
