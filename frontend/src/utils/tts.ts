/**
 * ============================================================================
 * MOSTAR GRID TEXT-TO-SPEECH ENGINE
 * Woo's Voice — Sovereign, African, Ceremonial
 * ============================================================================
 *
 * Uses Web Speech API (native browser, no cloud dependency)
 * Ensures voice is deep, intentional, and ceremonial
 */

export interface TTSConfig {
  rate?: number;           // 0.1-2.0, default 1.0
  pitch?: number;          // 0-2.0, default 1.0
  volume?: number;         // 0-1.0, default 1.0
  language?: string;       // BCP 47 language tag
  voiceIndex?: number;     // Index of available voice
}

export interface TTSOptions extends TTSConfig {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: Error) => void;
}

// ─────────────────────────────────────────────────────────────────────────
// VOICE SELECTION UTILITY
// ─────────────────────────────────────────────────────────────────────────

export function getAvailableVoices(): SpeechSynthesisVoice[] {
  return window.speechSynthesis.getVoices();
}

export function selectWooVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();

  if (voices.length === 0) {
    console.warn('No TTS voices available');
    return null;
  }

  // Priority 1: Look for a deep, male English voice
  let selectedVoice = voices.find(
    (voice) =>
      voice.lang.startsWith('en') &&
      voice.name.toLowerCase().includes('male')
  );

  // Priority 2: Look for any Google US English voice (usually good quality)
  if (!selectedVoice) {
    selectedVoice = voices.find(
      (voice) =>
        voice.lang === 'en-US' &&
        voice.name.toLowerCase().includes('google')
    );
  }

  // Priority 3: Use first English voice
  if (!selectedVoice) {
    selectedVoice = voices.find((voice) => voice.lang.startsWith('en'));
  }

  // Priority 4: Use any voice
  if (!selectedVoice) {
    selectedVoice = voices[0];
  }

  console.log('Selected Woo voice:', selectedVoice?.name);
  return selectedVoice;
}

// ─────────────────────────────────────────────────────────────────────────
// MAIN TTS FUNCTION
// ─────────────────────────────────────────────────────────────────────────

export function speakWoo(text: string, options: TTSOptions = {}): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!window.speechSynthesis) {
      console.warn('Speech Synthesis not supported in this browser');
      return reject(new Error('Speech Synthesis API not available'));
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    const voice = selectWooVoice();
    if (voice) {
      utterance.voice = voice;
    }

    utterance.rate = options.rate ?? 0.85;
    utterance.pitch = options.pitch ?? 0.9;
    utterance.volume = options.volume ?? 0.9;
    utterance.lang = options.language ?? 'en-US';

    utterance.onstart = () => {
      console.log('[Woo speaks]', text.substring(0, 50) + '...');
      window.dispatchEvent(new CustomEvent('woo-speaking-start'));
      options.onStart?.();
    };

    utterance.onend = () => {
      console.log('[Woo finishes]');
      window.dispatchEvent(new CustomEvent('woo-speaking-end'));
      options.onEnd?.();
      resolve();
    };

    utterance.onerror = (event) => {
      console.error('[Woo error]', event.error);
      window.dispatchEvent(new CustomEvent('woo-speaking-end'));
      const error = new Error(`TTS Error: ${event.error}`);
      options.onError?.(error);
      reject(error);
    };

    window.speechSynthesis.speak(utterance);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// SILENT MODE & HELPERS
// ─────────────────────────────────────────────────────────────────────────

let silentMode = false;

export function setSilentMode(enabled: boolean): void {
  silentMode = enabled;
  console.log(`[TTS] Silent mode: ${enabled}`);
}

export function isSilentMode(): boolean {
  return silentMode;
}

export function speakWooOrWait(
  text: string,
  options: TTSOptions = {}
): Promise<void> {
  if (silentMode) {
    const wordCount = text.split(' ').length;
    const estimatedDuration = Math.max(2000, wordCount * 300);
    return new Promise((resolve) => {
      options.onStart?.();
      setTimeout(() => {
        options.onEnd?.();
        resolve();
      }, estimatedDuration);
    });
  }

  return speakWoo(text, options);
}

export function initializeTTS(): void {
  if (!window.speechSynthesis) {
    console.warn('Speech Synthesis not supported');
    return;
  }

  const voices = window.speechSynthesis.getVoices();
  console.log(`[TTS Init] ${voices.length} voices available`);

  window.speechSynthesis.onvoiceschanged = () => {
    const updatedVoices = window.speechSynthesis.getVoices();
    console.log(`[TTS] Voices updated: ${updatedVoices.length} available`);
  };
}

export function stopSpeech(): void {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
    console.log('[TTS] Speech stopped');
  }
}

export function isSpeaking(): boolean {
  return window.speechSynthesis?.speaking ?? false;
}
