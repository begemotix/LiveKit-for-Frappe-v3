"""Unit tests for the filler-audio prewarm resampling path.

Why this exists
---------------
LiveKit's ``BackgroundAudioPlayer`` hardcodes 48 kHz for its internal
``rtc.AudioSource`` and ``rtc.AudioMixer``. Piper's thorsten-high voice
outputs at 22.05 kHz. When the two are joined directly, playback speeds
up by 48000/22050 ≈ 2.18x — the production deploy on 2026-04-24 19:34
showed exactly this: the filler played for ~1 s instead of ~2.5 s and
was unintelligible.

``_collect_filler_frames_pool_async`` is responsible for resampling the
Piper frames to 48 kHz *at cache time* so every ``.play(frames)`` call
at runtime hits the right rate without further work. This test pins
that contract: whatever the TTS native rate, the cached frames come
out at 48 kHz.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

import agent as agent_module


@dataclass
class _FakeFrame:
    """Minimal stand-in for rtc.AudioFrame: we only touch the two fields
    the resample path reads (sample_rate, num_channels). The real
    AudioResampler wants bytes too, but we mock AudioResampler itself
    so the fake can stay this small."""

    sample_rate: int
    num_channels: int = 1


class _FakeResampler:
    """Replaces rtc.AudioResampler for the duration of the test. Records
    the (input_rate, output_rate) pair so the test can assert we hand
    off the right rates, and returns frames stamped with the output
    rate so the downstream assertions have something to look at."""

    # Shared registry of instances per test; reset by the autouse fixture.
    instances: list = []  # noqa: RUF012

    def __init__(self, *, input_rate: int, output_rate: int, num_channels: int = 1):
        self.input_rate = input_rate
        self.output_rate = output_rate
        self.num_channels = num_channels
        self.pushed: list[_FakeFrame] = []
        _FakeResampler.instances.append(self)

    def push(self, frame):
        self.pushed.append(frame)
        # Emit one resampled frame per input frame — matches the
        # contract closely enough for shape assertions.
        return [_FakeFrame(sample_rate=self.output_rate, num_channels=self.num_channels)]

    def flush(self):
        return []


class _FakeTTSStream:
    """Async context manager that yields a fixed list of
    SynthesizedAudio-like objects. The collect helper only reads
    ``.frame`` from each item, so we shape the stand-in accordingly."""

    def __init__(self, frames):
        self._frames = frames

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def __aiter__(self):
        async def _gen():
            for f in self._frames:
                yield type("SA", (), {"frame": f})()

        return _gen()


class _FakeTTS:
    def __init__(self, sample_rate: int, frames_per_phrase: int = 3):
        self._sample_rate = sample_rate
        self._frames_per_phrase = frames_per_phrase

    def synthesize(self, text: str):
        frames = [
            _FakeFrame(sample_rate=self._sample_rate)
            for _ in range(self._frames_per_phrase)
        ]
        return _FakeTTSStream(frames)


@pytest.fixture(autouse=True)
def _reset_fake_resampler():
    _FakeResampler.instances.clear()
    yield
    _FakeResampler.instances.clear()


@pytest.mark.asyncio
async def test_filler_pool_resamples_piper_22050_to_48000(monkeypatch):
    """The 22.05 kHz case — the actual production bug. Every phrase
    must come out as 48 kHz frames, and the resampler must be
    instantiated with the expected (input, output) rates."""
    from livekit import rtc

    monkeypatch.setattr(rtc, "AudioResampler", _FakeResampler)

    tts = _FakeTTS(sample_rate=22050)
    phrases = ["A", "B", "C"]

    pool = await agent_module._collect_filler_frames_pool_async(tts, phrases)

    assert set(pool.keys()) == {"A", "B", "C"}
    for phrase, frames in pool.items():
        assert frames, f"phrase {phrase!r} produced no frames"
        assert all(f.sample_rate == 48000 for f in frames), (
            f"phrase {phrase!r}: expected every cached frame at 48000 Hz "
            f"but got {[f.sample_rate for f in frames]}"
        )

    # One resampler per phrase; each constructed with the correct rates.
    assert len(_FakeResampler.instances) == 3
    for inst in _FakeResampler.instances:
        assert inst.input_rate == 22050
        assert inst.output_rate == 48000


@pytest.mark.asyncio
async def test_filler_pool_skips_resample_when_tts_already_48k(monkeypatch):
    """If the TTS happens to emit 48 kHz natively (hypothetical future
    voice), we must not build a resampler at all — that would be a
    wasted round-trip through sox and could introduce tiny artifacts."""
    from livekit import rtc

    monkeypatch.setattr(rtc, "AudioResampler", _FakeResampler)

    tts = _FakeTTS(sample_rate=48000)
    pool = await agent_module._collect_filler_frames_pool_async(tts, ["X"])

    assert pool["X"], "empty pool for a single-phrase input"
    assert all(f.sample_rate == 48000 for f in pool["X"])
    # No resampler was built — the fast path is taken.
    assert _FakeResampler.instances == []


@pytest.mark.asyncio
async def test_filler_pool_drops_phrases_that_produced_no_frames(monkeypatch):
    """If Piper returns zero frames for a phrase (upstream error, weird
    input), the phrase must be omitted from the cache entirely rather
    than cached as an empty list. The runtime path treats 'phrase not
    in pool' as the fallback trigger — keep that contract clean."""
    from livekit import rtc

    monkeypatch.setattr(rtc, "AudioResampler", _FakeResampler)

    class _EmptyTTS:
        def synthesize(self, _text: str):
            return _FakeTTSStream([])

    pool = await agent_module._collect_filler_frames_pool_async(
        _EmptyTTS(), ["Y"]
    )
    assert "Y" not in pool
