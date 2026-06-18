/**
 * personalityClient — talks to the MoStar Personality Engine.
 *
 * The engine picks a persona (COMMANDER, ARCHITECT, TEACHER, GUARDIAN,
 * COMPANION, ORACLE) from a semantic frame describing mission, operational
 * domain, soulprint need, human emotion, and urgency.
 *
 * In preview, a deterministic local mirror of `choose_persona` runs in the
 * browser so the UI behaves identically without a backend.
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

const PERSONA_VOICES: Record<Persona, string> = {
  COMMANDER: "We have enough information. Proceed.",
  ARCHITECT: "Let's map the dependencies before we build.",
  TEACHER:   "Here's why the model behaves this way.",
  GUARDIAN:  "This action increases risk. I recommend caution.",
  COMPANION: "You've been carrying this problem for a while. Let's simplify it.",
  ORACLE:    "The signal is incomplete. Wait for confirmation.",
};

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

export async function choosePersona(frame: SemanticFrame): Promise<PersonaChoice> {
  if (!LIVE_GRID_SERVICES) return mockChoose(frame);
  const res = await fetch(`${GRID_SERVICES.personality}/api/semantic/interpret`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ input: frameToText(frame), source: "event", persist: false }),
  });
  if (!res.ok) throw new Error(`Personality /api/semantic/interpret ${res.status}`);
  const data = await res.json();
  const persona = (data.persona ?? "ARCHITECT") as Persona;
  return { persona, voice_sample: PERSONA_VOICES[persona] };
}

export async function personalityHealth() {
  if (!LIVE_GRID_SERVICES) return { status: "healthy" as const, mock: true };
  try {
    const res = await fetch(`${GRID_SERVICES.personality}/api/health`);
    if (!res.ok) return { status: "degraded" as const, detail: `HTTP ${res.status}` };
    return (await res.json()) as { status: "healthy" | "degraded" | "down"; detail?: string };
  } catch (err) {
    return { status: "down" as const, detail: (err as Error).message };
  }
}

export const PERSONAS: Persona[] =
  ["COMMANDER", "ARCHITECT", "TEACHER", "GUARDIAN", "COMPANION", "ORACLE"];
