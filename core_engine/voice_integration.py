import json, os, time, platform, subprocess, asyncio, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from gtts import gTTS
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️ edge-tts not installed. Falling back to gTTS only.")

from core_engine.moment_integration import log_mostar_moment

def hash_text(text: str) -> str:
    """Deterministic hash for audio caching."""
    return hashlib.md5(text.encode()).hexdigest()

async def speak_async(text: str, voice: str = "en-US-AriaNeural") -> str:
    """Resilient TTS with caching and fallback."""
    audio_hash = hash_text(text)
    cache_dir = Path("audio_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    file_path = cache_dir / f"{audio_hash}.mp3"
    
    if file_path.exists():
        return str(file_path.absolute())

    try:
        from edge_tts import Communicate
        communicate = Communicate(text=text, voice=voice)
        await communicate.save(str(file_path))
    except Exception as e:
        print(f"⚠️ edge-tts failed: {e}. Falling back to gTTS...")
        from gtts import gTTS
        tts = gTTS(text)
        tts.save(str(file_path))
    
    return str(file_path.absolute())

class MostarVoice:
    _LANG_ALIASES = {
        "yo": ("yoruba", "yo"),
        "yoruba": ("yoruba", "yo"),
        "en": ("english", "en"),
        "english": ("english", "en"),
        "sw": ("swahili", "sw"),
        "swahili": ("swahili", "sw"),
    }
    
    # Preferred Edge-TTS voices
    _EDGE_VOICES = {
        "en": "en-US-JennyNeural",
        "yo": "en-NG-AbeoNeural",  # Proxy, as true Yoruba might not be available
        "sw": "sw-KE-ZuriNeural"
    }

    def __init__(self, lingua=None, lang_code=None, lang=None):
        self.lingua, self.lang_code = self._normalize_language_inputs(
            lingua=lingua,
            lang_code=lang_code,
            lang=lang,
        )
        self.registry = self._load_voice_manifest()
        self.voice_cache_dirs = [
             Path("data/voice_cache"),
             Path("backend/data/voice_cache")
        ]
        for cache_dir in self.voice_cache_dirs:
            cache_dir.mkdir(parents=True, exist_ok=True)
            
        self.executor = ThreadPoolExecutor(max_workers=2)
        print(f"🔊 MostarVoice initialized :: {self.lingua.upper()} [{self.lang_code}] (Edge-TTS: {EDGE_TTS_AVAILABLE})")

    def _normalize_language_inputs(self, lingua, lang_code, lang):
        if lang:
            return self._resolve_alias(lang, fallback_code=lang_code)

        if lingua:
            return self._resolve_alias(lingua, fallback_code=lang_code)

        if lang_code:
            return self._resolve_alias(lang_code, fallback_code=lang_code)

        return self._LANG_ALIASES["yoruba"]

    def _resolve_alias(self, key, fallback_code=None):
        key_lower = key.lower()
        normalized = self._LANG_ALIASES.get(key_lower)

        if normalized:
            lingua_value, code_value = normalized
        else:
            lingua_value = key_lower
            code_value = key_lower

        if fallback_code:
            code_value = fallback_code.lower()

        return lingua_value, code_value

    def _load_voice_manifest(self):
        manifest_path = os.path.join("core_engine", "voice_manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _find_voice_clip(self, key):
        lang_manifest = self.registry.get(self.lingua, {})
        filename = lang_manifest.get(key) or lang_manifest.get("fallback")
        if not filename:
            return None

        for cache_dir in self.voice_cache_dirs:
            file_path = cache_dir / filename
            if file_path.exists():
                return str(file_path.absolute())
        return None

    def _play_audio(self, file_path):
        """Cross-platform audio playback"""
        try:
            system = platform.system().lower()
            if system == "windows":
                os.startfile(file_path)
            elif system == "darwin":
                subprocess.call(["open", file_path])
            else:  # linux
                subprocess.call(["xdg-open", file_path])
            print(f"🎧 Playback initiated -> {file_path}")
        except Exception as e:
            print(f"⚠️ Audio playback failed: {e}")

    def _get_cache_path(self, text: str, voice: str) -> Path:
        """Generate a deterministic cache path."""
        h = hashlib.sha256(f"{voice}:{text}".encode()).hexdigest()
        # Use first available cache dir
        return self.voice_cache_dirs[0] / f"tts_{h}.mp3"

    async def _speak_edge_async(self, text: str, voice: str) -> str:
        """Generate audio using Edge-TTS."""
        out_path = self._get_cache_path(text, voice)
        if out_path.exists():
            return str(out_path)
            
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(out_path))
        return str(out_path)

    def _speak_gtts_sync(self, text: str, lang_code: str) -> str:
        """Generate audio using gTTS (Synchronous, run in threadpool)."""
        out_path = self._get_cache_path(text, f"gtts-{lang_code}")
        if out_path.exists():
            return str(out_path)
            
        tts = gTTS(text=text, lang=lang_code)
        tts.save(str(out_path))
        return str(out_path)

    async def speak_async(self, text: str, phrase_key: str = None) -> str:
        """
        Main async entry point for speech.
        Returns: Path to the audio file.
        """
        # 1. Check for pre-recorded clip
        file_path = self._find_voice_clip(phrase_key)
        if file_path:
            self._play_audio(file_path) # Fire and forget playback
            return file_path

        # 2. Synthesize
        voice_name = self._EDGE_VOICES.get(self.lang_code, "en-US-JennyNeural")
        
        try:
            if EDGE_TTS_AVAILABLE:
                audio_path = await self._speak_edge_async(text, voice_name)
                method = "Edge-TTS"
            else:
                raise ImportError("Edge-TTS missing")
        except Exception as e:
            print(f"⚠️ Edge-TTS failed ({e}), falling back to gTTS...")
            loop = asyncio.get_running_loop()
            audio_path = await loop.run_in_executor(
                self.executor, 
                self._speak_gtts_sync, 
                text, 
                self.lang_code
            )
            method = "gTTS"

        # 3. Play (optional, depending on use case. Here we play locally)
        self._play_audio(audio_path)
        
        # 4. Log
        log_mostar_moment(
            initiator="Voice Layer",
            receiver="Soul Layer",
            description=f"Synthesized speech via {method}: '{text[:30]}...'",
            trigger_type="voice",
            resonance_score=0.9 if method == "Edge-TTS" else 0.7
        )
        return audio_path

    def speak(self, text, phrase_key=None):
        """Sync wrapper for legacy calls."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are likely inside a FastAPI app, but this method is sync.
                # Ideally, callers should await speak_async.
                # For now, we create a task but cannot await it easily without blocking.
                # This is risky. Better to warn.
                print("⚠️ Warning: calling sync 'speak' from likely async context. Use 'speak_async'.")
                asyncio.create_task(self.speak_async(text, phrase_key))
            else:
                loop.run_until_complete(self.speak_async(text, phrase_key))
        except RuntimeError:
             # New event loop if none exists
            asyncio.run(self.speak_async(text, phrase_key))

if __name__ == "__main__":
    # Test script
    async def main():
        mv = MostarVoice("en", "en")
        await mv.speak_async("MoStar Grid is now utilizing Edge-TTS for high fidelity audio.", "test_phrase")
        
    asyncio.run(main())
