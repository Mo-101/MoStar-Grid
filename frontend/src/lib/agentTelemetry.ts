import type { AgentTelemetry } from "@/hooks/useGridTelemetry";

export type AgentTone = "active" | "idle" | "alert";

export function toStrengthPercent(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  const normalized = value <= 1 ? value * 100 : value;
  if (!Number.isFinite(normalized)) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round(normalized)));
}

export function formatAgentStatus(value?: string | null) {
  if (!value) {
    return "Unknown";
  }
  const clean = value.replace(/[_-]+/g, " ").toLowerCase();
  return clean.replace(/\b\w/g, (char) => char.toUpperCase());
}

export function resolveAgentTone(value?: string | null): AgentTone {
  const normalized = value?.toUpperCase() ?? "UNKNOWN";
  if (["MONITORING", "ACTIVE", "ENGAGED"].includes(normalized)) {
    return "active";
  }
  if (["IDLE", "STANDBY", "PAUSED"].includes(normalized)) {
    return "idle";
  }
  return "alert";
}

export const agentFallbackRoster: AgentTelemetry[] = [
  {
    id: "fallback-ifa",
    name: "If� Oracle Alpha",
    status: "MONITORING",
    manifestationStrength: 0.86,
    capabilities: ["Divination", "Protocol Synthesis"],
  },
  {
    id: "fallback-verdict",
    name: "Verdict Renderer",
    status: "ACTIVE",
    manifestationStrength: 0.77,
    capabilities: ["Verdict Engine", "Audit"],
  },
  {
    id: "fallback-memory",
    name: "Ancestral Memory",
    status: "IDLE",
    manifestationStrength: 0.65,
    capabilities: ["Knowledge System", "Lore Binding"],
  },
  {
    id: "fallback-guardian",
    name: "Guardian Weave",
    status: "ACTIVE",
    manifestationStrength: 0.71,
    capabilities: ["Security Mesh", "Guard"],
  },
];
