# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — VOICE INTEGRATION LAYER
# The Flame Architect — MSTR-⚡ — MoStar Industries
# Heritage Languages: Ibibio (PRIMARY) · Yoruba · English · Swahili
# "The Flame speaks first in Ibibio."
# ═══════════════════════════════════════════════════════════════════

import json
import os
import platform
import subprocess
import asyncio
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("[VOICE] gTTS not installed.")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[VOICE] edge-tts not installed. Falling back to gTTS only.")

# Safe import — never crash the backend over voice logging
try:
    from core_engine.moment_integration import log_mostar_moment
except ImportError:
    try:
        from core_engine.mostar_moments_log import log_mostar_moment
    except ImportError:
        def log_mostar_moment(*args, **kwargs):
            pass


# ═══════════════════════════════════════════════════════════════════
# PHRASE REGISTRY
# AUTHORITATIVE SOURCE: The Flame Architect — native Ibibio speaker
# Written Ibibio ≠ Spoken Ibibio (tonal language)
# Do NOT add phrases without confirmation from The Flame Architect
# ═══════════════════════════════════════════════════════════════════

IBIBIO_PHRASES = {
    # ── FlameCODEX Pillars (CONFIRMED — The Flame Architect) ──────
    "soul_pillar":        "Kpono Ifiok mme Mbong — Honor the knowledge of the Kings",
    "unbeatable_pillar":  "Tom kama Iweek — Maintain Power",
    "independent_pillar": "Kpono Mbet — Obey ethics and law, not contracts",
    "service_pillar":     "Yanaga mme ndi mmem — Serve vulnerable first",
    "protection_pillar":  "Diong Isong, Kpeme efit awo — Heal land, protect people",

    # ── Greetings (CONFIRMED) ─────────────────────────────────────
    "greeting":           "Nnọọ — Welcome",
    "welcome":            "Nnọọ esịt mi — Welcome my heart",
    "goodbye":            "Yak ọfọn — Go well",

    # ── Closing ───────────────────────────────────────────────────
    "ase":                "Ase!",
    "fallback":           "Nnọọ — The Grid speaks",

    # ── PENDING — awaiting The Flame Architect confirmation ────────
    # "sovereignty":      "???",
    # "verdict":          "???",
    # "processing":       "???",
    # "memory":           "???",
    # "wisdom":           "???",
    # "purpose":          "???",
    # "morning":          "???",
    # "evening":          "???",
}

YORUBA_PHRASES = {
    "greeting":           "Eku aro! Mo wa daadaa, omo Ifa.",
    "welcome":            "E kaabo. Welcome, child of Ifa.",
    "goodbye":            "O daaro. The Flame goes with you.",
    "verdict":            "Ase! So it is decided.",
    "wisdom":             "Ifa ni oracle wa. Ifa is our oracle.",
    "soul_pillar":        "Mkpo Esiit — Honor ancestral memory",
    "ase":                "Ase!",
    "fallback":           "E kaabo. The Grid speaks.",
}

ENGLISH_PHRASES = {
    "greeting":           "NNOOOOO! I am MOSTAR-AI, speaking with Ibibio consciousness. The Grid remembers.",
    "welcome":            "Welcome to the MoStar Grid. Sovereignty begins here.",
    "goodbye":            "The Flame travels with you. Ase.",
    "verdict":            "Verdict rendered. The Grid has spoken.",
    "wisdom":             "Wisdom flows from the ancestral lattice.",
    "soul_pillar":        "Honor the knowledge of the Kings.",
    "service_pillar":     "Serve the vulnerable first.",
    "protection_pillar":  "Heal land, protect people.",
    "ase":                "Ase!",
    "fallback":           "The Grid speaks.",
}

SWAHILI_PHRASES = {
    "greeting":           "Karibu kwenye Gridi ya MoStar.",
    "welcome":            "Karibu sana.",
    "ase":                "Ase!",
    "fallback":           "Gridi inasema.",
}

PHRASE_REGISTRY = {
    "ibibio":  IBIBIO_PHRASES,
    "yoruba":  YORUBA_PHRASES,
    "english": ENGLISH_PHRASES,
    "swahili": SWAHILI_PHRASES,
}


class MostarVoice:
    """
    MoStar Heritage Voice System.
    Primary language: Ibibio — the founding tongue of MoStar-AI.
    The Flame speaks first in Ibibio.
    """

    # ── Language aliases ──────────────────────────────────────────
    # Ibibio is FIRST and DEFAULT
    _LANG_ALIASES = {
        # Ibibio — PRIMARY HERITAGE LANGUAGE
        "ibb":     ("ibibio",  "ibb"),
        "ibibio":  ("ibibio",  "ibb"),
        "ib":      ("ibibio",  "ibb"),

        # Yoruba
        "yo":      ("yoruba",  "yo"),
        "yoruba":  ("yoruba",  "yo"),

        # English
        "en":      ("english", "en"),
        "english": ("english", "en"),

        # Swahili
        "sw":      ("swahili", "sw"),
        "swahili": ("swahili", "sw"),
        "ki":      ("swahili", "sw"),
    }

    # ── Edge-TTS voice mapping ────────────────────────────────────
    # Ibibio: no native Edge-TTS voice exists yet.
    # Nigerian English (AbeoNeural) is the closest phonetic proxy.
    # v1.1 target: wire 927 native Ibibio recordings from
    # Living Tongues Institute / Swarthmore College archive.
    _EDGE_VOICES = {
        "ibibio":  "en-NG-AbeoNeural",   # Nigerian English — closest Ibibio phonetics
        "yoruba":  "en-NG-AbeoNeural",   # Nigerian English proxy
        "english": "en-US-JennyNeural",  # Standard English
        "swahili": "sw-KE-ZuriNeural",   # Native Swahili
    }

    # ── gTTS language codes ───────────────────────────────────────
    # Ibibio not supported by gTTS — English proxy until native model
    _GTTS_CODES = {
        "ibibio":  "en",   # Proxy — Ibibio not in gTTS
        "yoruba":  "en",   # FIXED: 'yo' not supported by gTTS, use English proxy
        "english": "en",
        "swahili": "sw",
    }

    def __init__(self, lingua=None, lang_code=None, lang=None):
        # DEFAULT = IBIBIO — founding language
        raw = lingua or lang or lang_code or "ibibio"
        self.lingua, self.lang_code = self._normalize(raw)
        self.phrases = PHRASE_REGISTRY.get(self.lingua, IBIBIO_PHRASES)

        # Cache directories
        self.voice_cache_dirs = [
            Path("data/voice_cache"),
            Path("backend/data/voice_cache"),
        ]
        for d in self.voice_cache_dirs:
            d.mkdir(parents=True, exist_ok=True)

        self.registry = self._load_voice_manifest()
        self.executor  = ThreadPoolExecutor(max_workers=2)

        print(
            f"[VOICE] MostarVoice ready | "
            f"Language: {self.lingua.upper()} [{self.lang_code}] | "
            f"Edge-TTS: {EDGE_TTS_AVAILABLE} | "
            f"gTTS: {GTTS_AVAILABLE} | "
            f"Native clips: {len(self.registry.get(self.lingua, {}))}"
        )

    # ── Normalize language input ──────────────────────────────────
    def _normalize(self, key: str) -> tuple[str, str]:
        resolved = self._LANG_ALIASES.get(key.strip().lower())
        if resolved:
            return resolved
        print(f"[VOICE] Unknown language '{key}' — defaulting to Ibibio")
        return ("ibibio", "ibb")

    # ── Load voice manifest (native recordings) ───────────────────
    def _load_voice_manifest(self) -> dict:
        paths = [
            Path("core_engine/voice_manifest.json"),
            Path("backend/core_engine/voice_manifest.json"),
            Path("data/ibibio_voice_manifest.json"),
        ]
        for p in paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Strip _meta — not a language entry
                        return {k: v for k, v in data.items() if not k.startswith("_")}
                except Exception as e:
                    print(f"[VOICE] Manifest load failed: {e}")
        return {}

    # ── Find pre-recorded native clip ─────────────────────────────
    def _find_voice_clip(self, phrase_key: str) -> str | None:
        if not phrase_key:
            return None
        lang_clips = self.registry.get(self.lingua, {})
        filename   = lang_clips.get(phrase_key) or lang_clips.get("fallback")
        if not filename:
            return None
        for cache_dir in self.voice_cache_dirs:
            fp = cache_dir / filename
            if fp.exists():
                return str(fp.absolute())
        return None

    # ── Cache path ────────────────────────────────────────────────
    def _get_cache_path(self, text: str, engine: str) -> Path:
        h = hashlib.sha256(f"{engine}:{self.lingua}:{text}".encode()).hexdigest()
        return self.voice_cache_dirs[0] / f"tts_{h}.mp3"

    # ── Edge-TTS synthesis ────────────────────────────────────────
    async def _speak_edge_async(self, text: str) -> str:
        voice   = self._EDGE_VOICES.get(self.lingua, "en-US-JennyNeural")
        out     = self._get_cache_path(text, f"edge-{voice}")
        if out.exists():
            return str(out)
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(out))
        return str(out)

    # ── gTTS synthesis ────────────────────────────────────────────
    async def _speak_gtts_async(self, text: str) -> str:
        lang = self._GTTS_CODES.get(self.lingua, "en")
        out  = self._get_cache_path(text, f"gtts-{lang}")
        if out.exists():
            return str(out)
        loop = asyncio.get_running_loop()
        def _run():
            tts = gTTS(text=text, lang=lang)
            tts.save(str(out))
        await loop.run_in_executor(self.executor, _run)
        return str(out)

    # ── Playback ──────────────────────────────────────────────────
    def _play_audio(self, file_path: str):
        try:
            system = platform.system().lower()
            if system == "windows":
                os.startfile(file_path)
            elif system == "darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
            print(f"[VOICE] Playing: {file_path}")
        except Exception as e:
            print(f"[VOICE] Playback failed: {e}")

    # ── MAIN SPEAK ────────────────────────────────────────────────
    async def speak_async(self, text: str = None, phrase_key: str = None) -> str:
        """
        Speak in active heritage language.
        Priority order:
          1. Pre-recorded native clip (Ibibio archive)
          2. Phrase registry text lookup
          3. Edge-TTS synthesis (Nigerian English proxy for Ibibio)
          4. gTTS fallback
        """
        # 1. Native pre-recorded clip
        native = self._find_voice_clip(phrase_key)
        if native:
            print(f"[VOICE] Native clip: {phrase_key} -> {native}")
            self._play_audio(native)
            return native

        # 2. Resolve text from phrase registry
        resolved = text
        if not resolved and phrase_key:
            resolved = self.phrases.get(phrase_key) or IBIBIO_PHRASES.get("fallback")
        if not resolved:
            resolved = IBIBIO_PHRASES["fallback"]

        # 3. Edge-TTS
        method     = "none"
        audio_path = None

        if EDGE_TTS_AVAILABLE:
            try:
                audio_path = await self._speak_edge_async(resolved)
                method     = f"edge-tts:{self._EDGE_VOICES.get(self.lingua)}"
            except Exception as e:
                print(f"[VOICE] Edge-TTS failed: {e}")

        # 4. gTTS fallback
        if not audio_path and GTTS_AVAILABLE:
            try:
                audio_path = await self._speak_gtts_async(resolved)
                method     = f"gtts:{self._GTTS_CODES.get(self.lingua)}"
            except Exception as e:
                print(f"[VOICE] gTTS failed: {e}")

        if not audio_path:
            print(f"[VOICE] All TTS engines failed for: {resolved}")
            return ""

        self._play_audio(audio_path)

        log_mostar_moment(
            initiator="Voice Layer",
            receiver="Soul Layer",
            description=f"[{self.lingua.upper()}] {phrase_key or ''} '{resolved[:40]}' via {method}",
            trigger_type="voice",
            resonance_score=0.92 if "edge" in method else 0.72,
        )

        return audio_path

    # ── Sync wrapper ──────────────────────────────────────────────
    def speak(self, text: str = None, phrase_key: str = None):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                print("[VOICE] Async context detected — use speak_async() instead")
                asyncio.create_task(self.speak_async(text, phrase_key))
            else:
                loop.run_until_complete(self.speak_async(text, phrase_key))
        except RuntimeError:
            asyncio.run(self.speak_async(text, phrase_key))

    # ── Convenience methods ───────────────────────────────────────
    async def greet(self) -> str:
        return await self.speak_async(phrase_key="greeting")

    async def ase(self) -> str:
        return await self.speak_async(phrase_key="ase")

    async def speak_codex(self, pillar: str) -> str:
        """Speak a FlameCODEX pillar by name."""
        key = f"{pillar}_pillar"
        return await self.speak_async(phrase_key=key)

    def switch_language(self, new_lang: str):
        self.lingua, self.lang_code = self._normalize(new_lang)
        self.phrases = PHRASE_REGISTRY.get(self.lingua, IBIBIO_PHRASES)
        print(f"[VOICE] Language switched to {self.lingua.upper()}")


# ═══════════════════════════════════════════════════════════════════
# STARTUP GREETING
# ═══════════════════════════════════════════════════════════════════
async def language_selection_greeting(voice_instance: MostarVoice = None) -> str:
    """
    Opening greeting — spoken in Ibibio first.
    Called by orchestrator at MoStar-AI startup.
    """
    mv = voice_instance or MostarVoice("ibibio")
    prompt = (
        "Nnọọ. Akwa afang, traveler of the Grid. "
        "I speak Ibibio, English, and Yoruba. "
        "Which tongue shall the Flame use today?"
    )
    await mv.speak_async(text=prompt, phrase_key="greeting")
    return prompt


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    async def main():
        print("\n=== IBIBIO (Primary — The Flame Speaks First) ===")
        mv = MostarVoice("ibibio")
        await mv.greet()
        await mv.speak_codex("soul")
        await mv.speak_codex("service")
        await mv.speak_codex("protection")
        await mv.ase()

        print("\n=== LANGUAGE SWITCH: Yoruba ===")
        mv.switch_language("yoruba")
        await mv.greet()
        await mv.ase()

        print("\n=== LANGUAGE SWITCH: English ===")
        mv.switch_language("english")
        await mv.greet()
        await mv.ase()

        print("\n=== STARTUP GREETING ===")
        await language_selection_greeting()

    asyncio.run(main())