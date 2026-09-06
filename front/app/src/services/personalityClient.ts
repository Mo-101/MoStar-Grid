/**
 * personalityClient — talks to the MoStar Personality Engine.
 *
 * The engine picks a persona (COMMANDER, ARCHITECT, TEACHER, GUARDIAN,
 * COMPANION, ORACLE) from a semantic frame describing mission, operational
 * domain, soulprint need, human emotion, and urgency.
 *
 * In preview, a deterministic local mirror of `choose_persona` runs in the
 * browser so the UI behaves identically without a backend.
 *
 * WHAT CHANGED (matching gridVoiceClient's standard)
 *   1. Neither request had a timeout. A hung Personality Engine could
 *      hang whatever was waiting on choosePersona() or
 *      personalityHealth() indefinitely. Both now run inside a budget
 *      that stays armed through body consumption, not just headers.
 *   2. choosePersona() no longer throws on failure. Every failure mode
 *      — timeout, bad status, invalid JSON, malformed shape, or a
 *      persona value outside the six we actually know how to voice —
 *      now falls back to the same deterministic mockChoose() heuristic
 *      already used in preview. Unlike speak()/narrate(), there's no
 *      "the caller explicitly wanted this exact thing" case here: a
 *      persona choice always has a reasoned local fallback available,
 *      so degrading to it beats blocking on a subsystem hiccup.
 *   3. The live persona value is validated against PERSONAS before
 *      being trusted. Previously it was cast blindly — an unrecognized
 *      or malformed value would have silently produced an undefined
 *      voice_sample rather than being caught here.
 */

import { GRID_SERVICES, LIVE_GRID_SERVICES } from "@/config/gridServices";

export type Persona =
  | "COMMANDER" | "ARCHITECT" | "TEACHER"
  | "GUARDIAN"  | "COMPANION" | "ORACLE";

export type SemanticFrame = {
  mission?:     { priority?: string; urgency?: string };
  operational?: { domain?: string };
  soulprint?:   { need?: string };
  human?:       { emotion?: string };
};

export type PersonaChoice = {
  persona: Persona;
  voice_sample: string;
  mock?: boolean;
};

export const PERSONAS: Persona[] =
  ["COMMANDER", "ARCHITECT", "TEACHER", "GUARDIAN", "COMPANION", "ORACLE"];

// Canonical voice lines. Verbatim — not placeholders.
const PERSONA_VOICES: Record<Persona, string> = {
  COMMANDER: "We have enough information. Proceed.",
  ARCHITECT: "Let's map the dependencies before we build.",
  TEACHER:   "Here's why the model behaves this way.",
  GUARDIAN:  "This action increases risk. I recommend caution.",
  COMPANION: "You've been carrying this problem for a while. Let's simplify it.",
  ORACLE:    "The signal is incomplete. Wait for confirmation.",
};

// PERSONA_TIMEOUT_MS is a conservative starting budget for
// /api/semantic/interpret, not a measured SLA — tune against observed
// latency once real numbers exist. PROBE_TIMEOUT_MS matches the health
// budget already established in gridVoiceClient.
const PERSONA_TIMEOUT_MS = 10_000;
const PROBE_TIMEOUT_MS = 3_000;

/**
 * Runs one request/response transaction inside a single timeout budget.
 * The abort stays armed until the body has actually been consumed, not
 * just until headers arrive.
 */
async function fetchWithinBudget<T>(
  input: string,
  init: RequestInit,
  ms: number,
  consume: (response: Response) => Promise<T>,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    return await consume(response);
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new Error(`Personality request aborted after ${ms}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function fetchJsonWithinBudget<T>(
  input: string,
  init: RequestInit,
  ms: number,
): Promise<{ response: Response; data: T }> {
  return fetchWithinBudget(input, init, ms, async (response) => ({
    response,
    data: (await response.json()) as T,
  }));
}

function isValidPersona(value: unknown): value is Persona {
  return typeof value === "string" && (PERSONAS as string[]).includes(value);
}

function mockChoose(frame: SemanticFrame): PersonaChoice {
  const priority = (frame.mission?.priority ?? "").toLowerCase();
  const urgency  = (frame.mission?.urgency ?? "").toLowerCase();
  const domain   = (frame.operational?.domain ?? "").toLowerCase();
  const need     = (frame.soulprint?.need ?? "").toLowerCase();
  const emotion  = (frame.human?.emotion ?? "").toLowerCase();

  let persona: Persona = "ARCHITECT";
  if (["critical", "emergency"].includes(priority) || ["critical", "urgent"].includes(urgency))
    persona = "GUARDIAN";
  else if (priority === "high" && ["logistics", "health", "humanitarian"].includes(domain))
    persona = "GUARDIAN";
  else if (["architecture", "systems", "infrastructure", "governance", "security"].includes(domain))
    persona = "ARCHITECT";
  else if (["explanation", "understanding", "why", "learn"].includes(need))
    persona = "TEACHER";
  else if (["decision", "action", "proceed", "approve", "command"].includes(need))
    persona = "COMMANDER";
  else if (["tired", "discouraged", "overloaded", "frustrated", "lost", "worried"].includes(emotion))
    persona = "COMPANION";
  else if (["meaning", "covenant", "resonance", "philosophy"].includes(domain))
    persona = "ORACLE";

  return { persona, voice_sample: PERSONA_VOICES[persona], mock: true };
}

// The backend has no standalone "choose persona from a structured frame"
// endpoint — /api/semantic/interpret runs the full five-layer pipeline on
// raw text and derives persona as one part of that. We synthesize a text
// summary of the frame to drive it, then resolve the voice sample locally
// (the same table used for the mock) since interpret doesn't return one.
function frameToText(frame: SemanticFrame): string {
  const parts = [
    frame.mission?.priority && `priority: ${frame.mission.priority}`,
    frame.mission?.urgency && `urgency: ${frame.mission.urgency}`,
    frame.operational?.domain && `domain: ${frame.operational.domain}`,
    frame.soulprint?.need && `need: ${frame.soulprint.need}`,
    frame.human?.emotion && `emotion: ${frame.human.emotion}`,
  ].filter(Boolean);
  return parts.join(", ") || "general query";
}

/**
 * Never throws. Every failure mode falls back to mockChoose(frame) —
 * see WHAT CHANGED §2. A caller can distinguish "genuinely mocked
 * (preview)" from "live pipeline fell back" only via the same `mock`
 * flag, matching how silentNarration() covers both "never live" and
 * "live but degraded" with a single marker in gridVoiceClient.
 */
export async function choosePersona(frame: SemanticFrame): Promise<PersonaChoice> {
  if (!LIVE_GRID_SERVICES) return mockChoose(frame);

  let data: unknown;
  try {
    const result = await fetchJsonWithinBudget<unknown>(
      `${GRID_SERVICES.personality}/api/semantic/interpret`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ input: frameToText(frame), source: "event", persist: false }),
      },
      PERSONA_TIMEOUT_MS,
    );
    if (!result.response.ok) return mockChoose(frame);
    data = result.data;
  } catch {
    // Timed out, network failure, or the body never resolved within
    // budget. The Grid still needs a persona to speak as.
    return mockChoose(frame);
  }

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return mockChoose(frame);
  }

  const rawPersona = (data as Record<string, unknown>).persona;
  if (!isValidPersona(rawPersona)) {
    // Live pipeline answered, but not with one of the six personas we
    // actually know how to voice. Not trusted on faith.
    return mockChoose(frame);
  }

  return { persona: rawPersona, voice_sample: PERSONA_VOICES[rawPersona] };
}

export async function personalityHealth() {
  if (!LIVE_GRID_SERVICES) return { status: "healthy" as const, mock: true };
  try {
    const { response, data } = await fetchJsonWithinBudget<{
      status: "healthy" | "degraded" | "down";
      detail?: string;
    }>(`${GRID_SERVICES.personality}/api/health`, {}, PROBE_TIMEOUT_MS);
    if (!response.ok) return { status: "degraded" as const, detail: `HTTP ${response.status}` };
    return data;
  } catch (err) {
    return { status: "down" as const, detail: (err as Error).message };
  }
}