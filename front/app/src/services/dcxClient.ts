/**
 * dcxClient — DCX Trinity router (Mind / Soul / Body) backed by Ollama.
 *
 * - DCX0 / MIND  — analytical, technical
 * - DCX1 / SOUL  — cultural, Ibibio, philosophical
 * - DCX2 / BODY  — execution, operations
 *
 * The browser sends queries to the DCX backend; routing happens on the
 * server. Mock mode returns a stub response so the console works in preview.
 */
import { GRID_SERVICES, LIVE_GRID_SERVICES } from "@/config/gridServices";

export type DCXLayer = "dcx0" | "dcx1" | "dcx2";

export type DCXRequest = {
  query: string;
  layer?: DCXLayer; // optional override; otherwise server routes
  conversation_history?: { role: "user" | "assistant"; content: string }[];
};

export type DCXResponse = {
  layer: DCXLayer;
  model: string;
  content: string;
  context_used: number;
  tokens?: number;
  mock?: boolean;
};

const ROUTING_HINTS: Record<DCXLayer, string[]> = {
  dcx1: ["ibibio", "ifá", "ifa", "ubuntu", "spirit", "soul", "culture", "identity", "mostar"],
  dcx2: ["deploy", "execute", "run", "build", "install", "script", "docker", "pm2", "server"],
  dcx0: [],
};

function localRoute(q: string): DCXLayer {
  const lower = q.toLowerCase();
  for (const layer of ["dcx1", "dcx2"] as DCXLayer[]) {
    if (ROUTING_HINTS[layer].some((s) => lower.includes(s))) return layer;
  }
  return "dcx0";
}

function mockThink(req: DCXRequest): DCXResponse {
  const layer = req.layer ?? localRoute(req.query);
  const flavor: Record<DCXLayer, string> = {
    dcx0: "Analytical pass — claim treated as a claim until verified.",
    dcx1: "Soul layer — Ibibio root, Ifá logic, sovereign cadence.",
    dcx2: "Body layer — operational. Action first, theory after.",
  };
  return {
    layer,
    model: { dcx0: "phi-4", dcx1: "qwen", dcx2: "mistral" }[layer],
    content: `${flavor[layer]} (mock reply to: "${req.query.slice(0, 120)}")`,
    context_used: 0,
    mock: true,
  };
}

export async function dcxThink(req: DCXRequest): Promise<DCXResponse> {
  if (!LIVE_GRID_SERVICES) return mockThink(req);
  const res = await fetch(`${GRID_SERVICES.dcx}/api/think`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query: req.query, layer: req.layer }),
  });
  if (!res.ok) throw new Error(`DCX /api/think ${res.status}: ${await res.text()}`);
  return (await res.json()) as DCXResponse;
}

export async function dcxHealth() {
  if (!LIVE_GRID_SERVICES) return { status: "healthy" as const, mock: true };
  try {
    const res = await fetch(`${GRID_SERVICES.dcx}/api/health`);
    if (!res.ok) return { status: "degraded" as const, detail: `HTTP ${res.status}` };
    return (await res.json()) as { status: "healthy" | "degraded" | "down"; detail?: string };
  } catch (err) {
    return { status: "down" as const, detail: (err as Error).message };
  }
}

export async function ollamaHealth() {
  if (!LIVE_GRID_SERVICES) return { status: "healthy" as const, mock: true };
  try {
    const res = await fetch(`${GRID_SERVICES.ollama}/api/tags`);
    if (!res.ok) return { status: "degraded" as const, detail: `HTTP ${res.status}` };
    return { status: "healthy" as const };
  } catch (err) {
    return { status: "down" as const, detail: (err as Error).message };
  }
}
