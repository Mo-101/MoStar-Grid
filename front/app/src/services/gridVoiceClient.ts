/**
 * gridVoiceClient — talks to MoStar Voice Service (Piper, :41071).
 *
 * Endpoint contract (server-owned, back/services/voice/voice_api.py):
 *   POST /speak  { text, mood, voice, persona, ... } -> { audio_url, ... }
 *   GET  /voices -> { default, voices: [{ id, label, status }] }
 *   GET  /health -> { status, engine, voice, ... }
 *
 * `voice` selects a registered voice_id (see GET /voices); unknown ids fall
 * back to the server's default. `mood` controls pacing — "ceremonial" (the
 * server default) is deliberately slow/dramatic; use "stable" for plain,
 * clear narration.
 *
 * In Lovable preview (LIVE_GRID_SERVICES=false) this client returns a
 * deterministic mock so the UI can be built without a backend. After
 * export, flipping the env flag activates real calls.
 */
import {
  GRID_SERVICES,
  GRID_VOICE_NAME,
  LIVE_GRID_SERVICES,
} from "@/config/gridServices";

export type SpeakRequest = {
  text: string;
  mood?: "stable" | "ceremonial" | "alert" | "reflective" | "prophecy" | "whisper";
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
  duration_ms: number;
  persona: string;
  engine: string;
  request_id: string;
  mock?: boolean;
};

export type HealthResponse = {
  status: "healthy" | "degraded" | "down";
  engine?: string;
  voice?: string;
  detail?: string;
  mock?: boolean;
};

const TIMEOUT_MS = 180_000;

async function withTimeout<T>(p: Promise<T>, ms = TIMEOUT_MS): Promise<T> {
  return await Promise.race([
    p,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`Voice request timed out after ${ms}ms`)), ms),
    ),
  ]);
}

function mockSpeak(req: SpeakRequest): SpeakResponse {
  return {
    duration_ms: Math.max(1200, req.text.length * 55),
    persona: req.persona ?? GRID_VOICE_NAME,
    engine: "mock",
    request_id: crypto.randomUUID(),
    mock: true,
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
  const res = await withTimeout(
    fetch(`${GRID_SERVICES.voice}/speak`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
  if (!res.ok) throw new Error(`Voice /speak ${res.status}: ${await res.text()}`);
  const data = (await res.json()) as Partial<SpeakResponse> & { audio_url?: string };
  // Resolve relative /audio/... paths against the voice base URL.
  if (data.audio_url && data.audio_url.startsWith("/")) {
    data.audio_url = `${GRID_SERVICES.voice}${data.audio_url}`;
  }
  return {
    duration_ms: data.duration_ms ?? 0,
    persona: data.persona ?? body.persona,
    engine: data.engine ?? "piper",
    request_id: data.request_id ?? crypto.randomUUID(),
    audio_url: data.audio_url,
    audio_base64: data.audio_base64,
  };
}

export async function voiceHealth(): Promise<HealthResponse> {
  if (!LIVE_GRID_SERVICES) {
    return { status: "healthy", engine: "mock", voice: GRID_VOICE_NAME, mock: true };
  }
  try {
    const res = await withTimeout(fetch(`${GRID_SERVICES.voice}/health`), 5_000);
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
    const res = await withTimeout(fetch(`${GRID_SERVICES.voice}/voices`), 5_000);
    if (!res.ok) return [];
    const data = (await res.json()) as { voices?: VoiceOption[] };
    return data.voices ?? [];
  } catch {
    return [];
  }
}
