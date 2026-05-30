/**
 * ============================================================================
 * MOSTAR VOICE CONTROLLER — THE SINGLE VOICE PATH
 * ============================================================================
 *
 * This is the ONLY way the Grid speaks. It replaces ALL browser TTS calls.
 *
 * Primary:  Sovereign Piper service (MoStar's own voice)
 * Fallback: Web Speech API (only if Piper service is unreachable)
 *
 * Rule: There is ONE voice path. Briefing → Audio Engine. Nothing else.
 *
 * Seal: 🜃∴🜂
 * ============================================================================
 */

const VOICE_API = '/api/voice';

export type Mood = 'stable' | 'ceremonial' | 'alert' | 'reflective';

interface SpeakResponse {
  ok: boolean;
  audio_url: string;
  engine: string;
  voice: string;
  cached: boolean;
}

// ─────────────────────────────────────────────────────────────────────────
// STATE — single audio element, single queue. No overlapping voices.
// ─────────────────────────────────────────────────────────────────────────

let currentAudio: HTMLAudioElement | null = null;
let serviceAvailable: boolean | null = null;

// ─────────────────────────────────────────────────────────────────────────
// HEALTH CHECK — is the sovereign voice service alive?
// ─────────────────────────────────────────────────────────────────────────

async function checkService(): Promise<boolean> {
  if (serviceAvailable !== null) return serviceAvailable;
  try {
    const res = await fetch(`${VOICE_API}/health`);
    if (!res.ok) {
      serviceAvailable = false;
      return false;
    }
    const data = await res.json();
    serviceAvailable = data.status === 'healthy';
    console.log(`[Voice] Sovereign service: ${data.status} (${data.voice})`);
    return serviceAvailable;
  } catch {
    serviceAvailable = false;
    console.warn('[Voice] Sovereign service unreachable — will use fallback');
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// STOP — silence everything immediately
// ─────────────────────────────────────────────────────────────────────────

export function stopVoice(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

// ─────────────────────────────────────────────────────────────────────────
// PRIMARY: Sovereign Piper voice
// ─────────────────────────────────────────────────────────────────────────

async function speakSovereign(text: string, mood: Mood): Promise<void> {
  const res = await fetch(`${VOICE_API}/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, mood }),
  });

  if (!res.ok) throw new Error(`Voice service returned ${res.status}`);

  const data: SpeakResponse = await res.json();
  if (!data.ok || !data.audio_url) throw new Error('Voice service returned no audio');

  return new Promise((resolve, reject) => {
    stopVoice();
    const audio = new Audio(`${VOICE_API}${data.audio_url}`);
    currentAudio = audio;

    audio.onended = () => {
      currentAudio = null;
      window.dispatchEvent(new Event("woo-speaking-end"));
      resolve();
    };
    audio.onerror = () => {
      currentAudio = null;
      window.dispatchEvent(new Event("woo-speaking-end"));
      reject(new Error('Audio playback failed'));
    };

    window.dispatchEvent(new Event("woo-speaking-start"));
    audio.play().catch(reject);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// FALLBACK: Web Speech API (only when sovereign service is down)
// ─────────────────────────────────────────────────────────────────────────

function speakFallback(text: string): Promise<void> {
  return new Promise((resolve) => {
    if (!window.speechSynthesis) {
      console.warn('[Voice] No fallback available');
      return resolve();
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    const voices = window.speechSynthesis.getVoices();
    const smooth = voices.find(v => v.name === 'Google UK English Female')
      || voices.find(v => v.name.toLowerCase().includes('google') && v.lang.startsWith('en'))
      || voices.find(v => v.lang.startsWith('en'));
    if (smooth) utterance.voice = smooth;

    utterance.rate = 0.85;
    utterance.pitch = 0.9;
    utterance.volume = 0.95;
    utterance.onend = () => {
      window.dispatchEvent(new Event("woo-speaking-end"));
      resolve();
    };
    utterance.onerror = () => {
      window.dispatchEvent(new Event("woo-speaking-end"));
      resolve();
    };

    window.dispatchEvent(new Event("woo-speaking-start"));
    window.speechSynthesis.speak(utterance);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// THE ONE PUBLIC FUNCTION — everything speaks through this
// ─────────────────────────────────────────────────────────────────────────

export async function speak(text: string, mood: Mood = 'ceremonial'): Promise<void> {
  stopVoice(); // Interrupt any ongoing speech immediately
  const cleaned = text.replace(/[🜂🜄🜁🜃∴]/g, '').trim();
  if (!cleaned) return;

  const useSovereign = await checkService();

  if (useSovereign) {
    try {
      await speakSovereign(cleaned, mood);
      return;
    } catch (err) {
      console.warn('[Voice] Sovereign voice failed, falling back:', err);
      serviceAvailable = null;
    }
  }

  await speakFallback(cleaned);
}

// ─────────────────────────────────────────────────────────────────────────
// SEQUENCE — speak multiple lines in order
// ─────────────────────────────────────────────────────────────────────────

export async function speakSequence(
  lines: string[],
  mood: Mood = 'ceremonial',
  onLineStart?: (index: number, line: string) => void
): Promise<void> {
  for (let i = 0; i < lines.length; i++) {
    onLineStart?.(i, lines[i]);
    await speak(lines[i], mood);
  }
}

export function resetServiceCheck(): void {
  serviceAvailable = null;
}
