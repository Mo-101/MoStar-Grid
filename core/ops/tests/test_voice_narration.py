from __future__ import annotations

import wave
from pathlib import Path

from voice.voice_api import concat_wavs, wav_duration_ms


def _write_silence(path: Path, frames: int, rate: int = 8_000) -> None:
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(b"\x00\x00" * frames)


def test_wav_duration_and_concatenation_are_measured_from_frames(tmp_path: Path):
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    joined = tmp_path / "joined.wav"
    _write_silence(first, 4_000)
    _write_silence(second, 2_000)

    concat_wavs([first, second], joined)

    assert wav_duration_ms(first) == 500
    assert wav_duration_ms(second) == 250
    assert wav_duration_ms(joined) == 750
