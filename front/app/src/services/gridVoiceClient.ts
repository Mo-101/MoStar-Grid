/**
 * gridVoiceClient — talks to MoStar Voice Service (Piper, :41071).
 *
 * WHAT CHANGED
 *   1. `duration_ms` is gone. It measured how long Piper took to think and
 *      published it as if it were the length of the utterance. Replaced by
 *      `synthesis_ms` (cost) and `audio_ms` (what the ear hears). Legacy
 *      servers are read defensively — see readSpeak().
 *   2. `narrate()` no longer throws in preview. It returns a silent plan
 *      with audioUrl: null, so the boot conductor takes the silent path by
 *      design rather than by exception.
 *   3. Timeouts abort the request. The old withTimeout rejected the promise
 *      but left the fetch running — a 180-second orphan holding a socket.
 *   4. narrate() gets its own short budget. A boot screen cannot wait three
 *      minutes for a ceremony.
 *   5. The response shape is validated. An old server returning the /speak
 *      shape to /narrate used to crash on data.segments.map.
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

/** Aborts the underlying request, not just the promise wrapping it. */
async function fetchWithTimeout(
  input: string,
  init: RequestInit = {},
  ms = SPEAK_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new Error(`Voice request aborted after ${ms}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function absolutise(url: string): string {
  return url.startsWith("/") ? `${GRID_SERVICES.voice}${url}` : url;
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
 * Reads either the corrected shape or the legacy one. A legacy `duration_ms`
 * is treated as synthesis cost — which is what it always actually was — and
 * audio_ms stays null rather than inheriting the lie.
 */
function readSpeak(data: Record<string, unknown>, fallbackPersona: string): SpeakResponse {
  const audioMs = typeof data.audio_ms === "number" ? data.audio_ms : null;
  const synthMs =
    typeof data.synthesis_ms === "number"
      ? data.synthesis_ms
      : typeof data.duration_ms === "number"
        ? data.duration_ms
        : null;

  return {
    audio_ms: audioMs,
    synthesis_ms: synthMs,
    persona: (data.persona as string) ?? fallbackPersona,
    engine: (data.engine as string) ?? "piper",
    request_id: (data.request_id as string) ?? crypto.randomUUID(),
    audio_url: data.audio_url ? absolutise(data.audio_url as string) : undefined,
    audio_base64: data.audio_base64 as string | undefined,
  };
}

export async function speak(req: SpeakRequest): Promise<SpeakResponse> {
  if (!LIVE_GRID_SERVICES) return mockSpeak(req);

  const body = {
    text: req.text,
    mood: req.mood ?? "stable",
    persona: req.persona ?? GRID_VOICE_NAME,
    voice: req.voice ?? GRID_VOICE_NAME,
    format: req.format ?? "wav",
  };

  const res = await fetchWithTimeout(
    `${GRID_SERVICES.voice}/speak`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    },
    SPEAK_TIMEOUT_MS,
  );

  if (!res.ok) throw new Error(`Voice /speak ${res.status}: ${await res.text()}`);
  return readSpeak(await res.json(), body.persona);
}

function isNarrationShape(d: unknown): d is {
  audio_url: string;
  audio_ms: number;
  synthesis_ms?: number;
  segments: NarrationSegment[];
} {
  const o = d as Record<string, unknown>;
  return (
    !!o &&
    typeof o.audio_url === "string" &&
    typeof o.audio_ms === "number" &&
    Array.isArray(o.segments) &&
    o.segments.every(
      (s: unknown) =>
        typeof (s as NarrationSegment)?.start_ms === "number" &&
        typeof (s as NarrationSegment)?.end_ms === "number",
    )
  );
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

export async function narrate(
  segments: string[],
  mood: Mood = "ceremonial",
): Promise<NarrationResponse> {
  if (!LIVE_GRID_SERVICES) return silentNarration(segments);

  let data: unknown;
  try {
    const res = await fetchWithTimeout(
      `${GRID_SERVICES.voice}/narrate`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ segments, mood, voice: GRID_VOICE_NAME }),
      },
      NARRATE_TIMEOUT_MS,
    );
    if (!res.ok) throw new Error(`Voice /narrate ${res.status}`);
    data = await res.json();
  } catch {
    return silentNarration(segments); // voice failed; the ceremony continues
  }

  if (!isNarrationShape(data)) {
    // Server is on the old contract. Do not guess cue points from it.
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
    const res = await fetchWithTimeout(`${GRID_SERVICES.voice}/health`, {}, PROBE_TIMEOUT_MS);
    if (!res.ok) return { status: "degraded", detail: `HTTP ${res.status}` };
    return (await res.json()) as HealthResponse;
  } catch (err) {
    return { status: "down", detail: (err as Error).message };
  }
}

export async function listVoices(): Promise<VoiceOption[]> {
  if (!LIVE_GRID_SERVICES) {
    return [{ id: GRID_VOICE_NAME, label: "Mock voice (preview)", status: "available" }];
  }
  try {
    const res = await fetchWithTimeout(`${GRID_SERVICES.voice}/voices`, {}, PROBE_TIMEOUT_MS);
    if (!res.ok) return [];
    const data = (await res.json()) as { voices?: VoiceOption[] };
    return data.voices ?? [];
  } catch {
    return [];
  }
}
