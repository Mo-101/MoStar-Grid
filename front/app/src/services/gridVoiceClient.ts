/**
 * gridVoiceClient — talks to MoStar Voice Service (Piper, :41071).
 *
 * ROLE
 *   Voice projects what the Grid has already decided to say. It is not
 *   state, not authority, not truth. A voice may disappear; the Grid
 *   must continue. Silence is a valid, deliberate output — not an error.
 *
 * WHAT CHANGED (this pass)
 *   1. Timeout now covers the full exchange, not just headers. The
 *      previous fetchWithTimeout cleared its timer as soon as fetch()
 *      resolved — which happens once headers arrive — so a response
 *      that stalled mid-body could hang indefinitely past its stated
 *      budget. fetchWithinBudget keeps the abort armed until the body
 *      has actually been consumed.
 *   2. Narration validation is now real validation, not a shape guess.
 *      audio_ms / synthesis_ms must be finite and non-negative; every
 *      segment needs string text, finite non-negative start/end with
 *      start <= end <= audio_ms; segments must be monotonic and
 *      non-overlapping. Anything else collapses to silent continuity
 *      rather than being trusted because it happened to parse.
 *   3. speak() failure handling is explicit. Invalid JSON and an
 *      invalid response shape now throw clear, named errors instead of
 *      an uncaught parse exception or a blind `as` cast on untrusted
 *      fields. speak() still throws on failure by design: it's a
 *      direct, single request a caller explicitly made and should know
 *      failed. narrate() is the one required to degrade to silence,
 *      because it drives continuity of a running ceremony — that
 *      asymmetry is intentional, not an oversight.
 *   4. `duration_ms` (legacy) is still accepted, but only ever lands in
 *      synthesis_ms. It measured how long Piper took to think, not how
 *      long the audio runs, and never gets promoted into audio_ms.
 */

import { GRID_SERVICES, GRID_VOICE_NAME, LIVE_GRID_SERVICES } from "@/config/gridServices";
import { silentSegmentPlan } from "@/lib/gridSnapshot";

export type Mood = "stable" | "ceremonial" | "alert" | "reflective" | "prophecy" | "whisper";

export type SpeakRequest = {
  text: string;
  mood?: Mood;
  persona?: string;
  voice?: string;
  format?: "wav" | "mp3" | "ogg";
};

export type VoiceOption = {
  id: string;
  label: string;
  status: "available" | "missing";
};

export type SpeakResponse = {
  audio_url?: string;
  audio_base64?: string;
  /** Measured length of the audio. Null when the server did not report it. */
  audio_ms: number | null;
  /** What synthesis cost us. Never a substitute for audio_ms. */
  synthesis_ms: number | null;
  persona: string;
  engine: string;
  request_id: string;
  mock?: boolean;
};

export type NarrationSegment = { text: string; start_ms: number; end_ms: number };

export type NarrationResponse = {
  /** Null means: proceed in silence. Not an error. */
  audio_url: string | null;
  audio_ms: number;
  synthesis_ms: number | null;
  segments: NarrationSegment[];
  silent: boolean;
};

export type HealthResponse = {
  status: "healthy" | "degraded" | "down";
  engine?: string;
  voice?: string;
  detail?: string;
  mock?: boolean;
};

const SPEAK_TIMEOUT_MS = 180_000; // long-form console synthesis
const NARRATE_TIMEOUT_MS = 12_000; // boot ceremony — must not hang the screen
const PROBE_TIMEOUT_MS = 3_000;

/**
 * Runs one request/response transaction inside a single timeout budget.
 * The abort stays armed until `consume` has finished reading the body,
 * so a stall after headers is still caught — not just a stall before
 * them.
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
      throw new Error(`Voice request aborted after ${ms}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function fetchJsonWithinBudget<T>(
  input: string,
  init: RequestInit = {},
  ms = SPEAK_TIMEOUT_MS,
): Promise<{ response: Response; data: T }> {
  return fetchWithinBudget(input, init, ms, async (response) => ({
    response,
    data: (await response.json()) as T,
  }));
}

function fetchTextWithinBudget(
  input: string,
  init: RequestInit = {},
  ms = SPEAK_TIMEOUT_MS,
): Promise<{ response: Response; text: string }> {
  return fetchWithinBudget(input, init, ms, async (response) => ({
    response,
    text: await response.text(),
  }));
}

function absolutise(url: string): string {
  return url.startsWith("/") ? `${GRID_SERVICES.voice}${url}` : url;
}

/** Finite, non-negative — the only shape a real duration can have. */
function isFiniteNonNegative(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function mockSpeak(req: SpeakRequest): SpeakResponse {
  return {
    audio_ms: null, // a mock has no audio, so it claims no length
    synthesis_ms: 0,
    persona: req.persona ?? GRID_VOICE_NAME,
    engine: "mock",
    request_id: crypto.randomUUID(),
    mock: true,
  };
}

/**
 * Reads either the corrected shape or the legacy one. A legacy
 * `duration_ms` is treated as synthesis cost — which is what it always
 * actually was — and audio_ms stays null rather than inheriting the
 * lie. Every field is checked before use; nothing is cast on faith.
 */
function readSpeak(data: Record<string, unknown>, fallbackPersona: string): SpeakResponse {
  const audioMs = isFiniteNonNegative(data.audio_ms) ? data.audio_ms : null;
  const synthesisMs = isFiniteNonNegative(data.synthesis_ms)
    ? data.synthesis_ms
    : isFiniteNonNegative(data.duration_ms)
      ? data.duration_ms
      : null;

  return {
    audio_ms: audioMs,
    synthesis_ms: synthesisMs,
    persona: typeof data.persona === "string" ? data.persona : fallbackPersona,
    engine: typeof data.engine === "string" ? data.engine : "piper",
    request_id: typeof data.request_id === "string" ? data.request_id : crypto.randomUUID(),
    audio_url: typeof data.audio_url === "string" ? absolutise(data.audio_url) : undefined,
    audio_base64: typeof data.audio_base64 === "string" ? data.audio_base64 : undefined,
  };
}

/**
 * speak() throws on failure by design — see WHAT CHANGED §3. Every
 * failure mode gets a clear, named error rather than an uncaught
 * exception, but it is still a throw: the caller asked for a specific
 * utterance and should know if it didn't happen.
 */
export async function speak(req: SpeakRequest): Promise<SpeakResponse> {
  if (!LIVE_GRID_SERVICES) return mockSpeak(req);

  const body = {
    text: req.text,
    mood: req.mood ?? "stable",
    persona: req.persona ?? GRID_VOICE_NAME,
    voice: req.voice ?? GRID_VOICE_NAME,
    format: req.format ?? "wav",
  };

  const { response, text } = await fetchTextWithinBudget(
    `${GRID_SERVICES.voice}/speak`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    },
    SPEAK_TIMEOUT_MS,
  );

  if (!response.ok) {
    throw new Error(`Voice /speak ${response.status}: ${text}`);
  }

  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("Voice /speak returned invalid JSON");
  }

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Voice /speak returned invalid response shape");
  }

  return readSpeak(data as Record<string, unknown>, body.persona);
}

/**
 * Real validation, not a shape guess. Rejects NaN/Infinity/negative
 * timing, missing segment text, out-of-order or overlapping segments,
 * and anything that claims to end after the narration's own audio_ms.
 * Unknown or malformed shape returns false — the caller falls back to
 * silentNarration rather than trusting a partial match.
 */
function isNarrationShape(data: unknown): data is {
  audio_url: string;
  audio_ms: number;
  synthesis_ms?: number;
  segments: NarrationSegment[];
} {
  if (!data || typeof data !== "object" || Array.isArray(data)) return false;
  const o = data as Record<string, unknown>;

  if (typeof o.audio_url !== "string") return false;
  if (!isFiniteNonNegative(o.audio_ms)) return false;
  if (o.synthesis_ms !== undefined && !isFiniteNonNegative(o.synthesis_ms)) return false;
  if (!Array.isArray(o.segments)) return false;

  let previousEnd = 0;
  for (const raw of o.segments) {
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return false;
    const segment = raw as Record<string, unknown>;

    if (typeof segment.text !== "string") return false;
    if (!isFiniteNonNegative(segment.start_ms) || !isFiniteNonNegative(segment.end_ms)) return false;
    if (segment.start_ms > segment.end_ms) return false;
    if (segment.end_ms > o.audio_ms) return false;
    if (segment.start_ms < previousEnd) return false; // overlap or out of order

    previousEnd = segment.end_ms;
  }

  return true;
}

/** A plan the conductor can run with no audio at all. Not an error state. */
export function silentNarration(segments: string[]): NarrationResponse {
  const plan = silentSegmentPlan(segments);
  return {
    audio_url: null,
    audio_ms: plan.length ? plan[plan.length - 1].end_ms : 0,
    synthesis_ms: null,
    segments: plan,
    silent: true,
  };
}

/**
 * narrate() never throws to its caller. Every failure mode — timeout,
 * bad status, invalid JSON, malformed shape — collapses to
 * silentNarration(). The ceremony continues; only the acoustic layer
 * is absent. This is the asymmetry with speak() described in WHAT
 * CHANGED §3, and it is intentional.
 */
export async function narrate(segments: string[], mood: Mood = "ceremonial"): Promise<NarrationResponse> {
  if (!LIVE_GRID_SERVICES) return silentNarration(segments);

  let data: unknown;
  try {
    const result = await fetchJsonWithinBudget<unknown>(
      `${GRID_SERVICES.voice}/narrate`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ segments, mood, voice: GRID_VOICE_NAME }),
      },
      NARRATE_TIMEOUT_MS,
    );
    if (!result.response.ok) return silentNarration(segments);
    data = result.data;
  } catch {
    // Voice failed, timed out, or the body never resolved within budget.
    return silentNarration(segments);
  }

  if (!isNarrationShape(data)) {
    // Old contract, or garbage. Do not guess cue points from it.
    return silentNarration(segments);
  }

  return {
    audio_url: absolutise(data.audio_url),
    audio_ms: data.audio_ms,
    synthesis_ms: data.synthesis_ms ?? null,
    segments: data.segments,
    silent: false,
  };
}

export async function voiceHealth(): Promise<HealthResponse> {
  if (!LIVE_GRID_SERVICES) {
    return { status: "healthy", engine: "mock", voice: GRID_VOICE_NAME, mock: true };
  }
  try {
    const { response, data } = await fetchJsonWithinBudget<HealthResponse>(
      `${GRID_SERVICES.voice}/health`,
      {},
      PROBE_TIMEOUT_MS,
    );
    if (!response.ok) return { status: "degraded", detail: `HTTP ${response.status}` };
    return data;
  } catch (err) {
    return { status: "down", detail: (err as Error).message };
  }
}

export async function listVoices(): Promise<VoiceOption[]> {
  if (!LIVE_GRID_SERVICES) {
    return [{ id: GRID_VOICE_NAME, label: "Mock voice (preview)", status: "available" }];
  }
  try {
    const { response, data } = await fetchJsonWithinBudget<{ voices?: VoiceOption[] }>(
      `${GRID_SERVICES.voice}/voices`,
      {},
      PROBE_TIMEOUT_MS,
    );
    if (!response.ok) return [];
    return Array.isArray(data.voices) ? data.voices : [];
  } catch {
    return [];
  }
}