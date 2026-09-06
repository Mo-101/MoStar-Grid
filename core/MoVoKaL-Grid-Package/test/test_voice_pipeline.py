import importlib.util
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class VoicePipelineTests(unittest.TestCase):
    def test_complete_utterance_and_atomic_wav(self):
        for source in [ROOT / "services/voice/voice_api.py", ROOT.parents[1] / "back/services/voice/voice_api.py"]:
            spec = importlib.util.spec_from_file_location("tested_voice", source)
            voice = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(voice)
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "speech.wav"
                def piper(command, **kwargs):
                    self.assertEqual(kwargs["input"].decode(), "Every word completes. Is it 3.14? Yes, absolutely!")
                    self.assertFalse(output.exists())
                    with wave.open(command[-1], "wb") as audio:
                        audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(22050)
                        audio.writeframes(bytes(44100))
                    return type("Result", (), {"returncode": 0})()
                with patch.object(voice, "assert_piper_ready"), patch.object(voice.subprocess, "run", side_effect=piper):
                    voice.synthesize("Every word completes. Is it 3.14?\nYes, absolutely!", "conversational", Path("model.onnx"), output)
                self.assertEqual(voice.wav_duration_ms(output), 1000)
                self.assertEqual(list(Path(directory).iterdir()), [output])

if __name__ == "__main__":
    unittest.main()
