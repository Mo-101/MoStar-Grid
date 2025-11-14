import { useEffect, useState } from "react";

export type MomentRecord = {
  initiator: string;
  receiver: string;
  description: string;
  trigger_type: string;
  resonance_score: number;
  timestamp: string;
  quantum_id: string;
};

export type AgentTelemetry = {
  id: string;
  name: string;
  status: string;
  manifestationStrength: number;
  capabilities: string[];
};

export type BackendStatus = {
  ok: boolean;
  data?: {
    system?: string;
    neo4j?: string;
    tts_language?: string;
    ollama_model?: string;
  };
  error?: string;
};

export type GraphSummary = {
  ok: boolean;
  stats?: {
    totalMoments: number;
    avgResonance: number | null;
    distinctInitiators: number;
  };
  latest?: MomentRecord[];
  agents?: AgentTelemetry[];
  agentWarning?: string;
  error?: string;
};

export type TelemetryPayload = {
  backend: BackendStatus;
  graph: GraphSummary;
  log: {
    entries: MomentRecord[];
    path: string;
  };
  generatedAt: string;
};

export function useGridTelemetry(pollInterval = 6000) {
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const fetchTelemetry = async () => {
      try {
        const response = await fetch("/api/grid-telemetry", {
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error(`Telemetry fetch failed: ${response.status}`);
        }
        const payload = (await response.json()) as TelemetryPayload;
        if (active) {
          setTelemetry(payload);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchTelemetry();
    const id = setInterval(fetchTelemetry, pollInterval);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [pollInterval]);

  return { telemetry, error, loading };
}
