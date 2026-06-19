/**
 * Grid Services — sovereign endpoint configuration.
 *
 * The browser NEVER synthesizes voice. It calls external services owned by
 * MoStar. All URLs are read from Vite env at build time so the exported
 * codebase can be pointed at real infrastructure without editing source.
 *
 * Live calls are disabled in Lovable preview by default. Set
 *   VITE_ENABLE_LIVE_GRID_SERVICES=true
 * in `.env.local` to talk to the real backends.
 */

export type BackendId = "piper" | "dcx" | "ollama" | "mock";

export const GRID_SERVICES = {
  voice:       import.meta.env.VITE_MOSTAR_VOICE_URL       ?? "http://localhost:41071",
  personality: import.meta.env.VITE_PERSONALITY_ENGINE_URL ?? "http://localhost:41072",
  dcx:         import.meta.env.VITE_DCX_TRINITY_URL        ?? "http://localhost:41073",
  ollama:      import.meta.env.VITE_OLLAMA_URL             ?? "http://localhost:11434",
  api:         import.meta.env.VITE_GRID_API_BASE          || "http://localhost:41010",
} as const;

export const LIVE_GRID_SERVICES =
  String(import.meta.env.VITE_ENABLE_LIVE_GRID_SERVICES ?? "false").toLowerCase() === "true";

export const GRID_VOICE_NAME = "mostar-sovereign-v1";

export type ServiceKey = keyof typeof GRID_SERVICES;

export const SERVICE_LABEL: Record<ServiceKey, string> = {
  voice:       "MoStar Voice Service",
  personality: "Personality Engine",
  dcx:         "DCX Trinity",
  ollama:      "Ollama",
  api:         "Grid API",
};
