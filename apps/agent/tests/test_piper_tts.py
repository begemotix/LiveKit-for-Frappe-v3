"""Unit tests for the local Piper HTTP TTS adapter.

We exercise ``PiperTTS`` with a local aiohttp fake so no real Piper
server is required and we don't need a new dev dependency. The scope:
correct HTTP payload shape, WAV→PCM unwrap with the native sample rate,
error translation to LiveKit API error types, and the non-streaming
capability flag (so the StreamAdapter still wraps the adapter the same
way it wraps Voxtral).
"""
from __future__ import annotations

import io
import struct
import wave
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from src.piper_tts import PiperTTS, _unwrap_wav


def _build_wav(samples: list[int], *, sample_rate: int = 22050) -> bytes:
    """Construct a tiny 16-bit mono WAV byte blob for use as a server mock
    response. The Piper HTTP server always emits mono 16-bit PCM WAV; our
    adapter must parse this exact shape."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


class _FakeResponse:
    """Lightweight aiohttp-response stand-in that supports `async with`."""

    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = body

    async def read(self) -> bytes:
        return self._body

    async def text(self) -> str:
        return self._body.decode(errors="replace")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _FakeSession:
    """Lightweight aiohttp-session stand-in. Captures the last post call
    for request-shape assertions."""

    def __init__(self, response: _FakeResponse):
        self._response = response
        self.last_post_url: str | None = None
        self.last_post_json: dict | None = None

    def post(self, url, *, headers=None, json=None):
        self.last_post_url = url
        self.last_post_json = json
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@contextmanager
def _fake_aiohttp(*, status: int = 200, body: bytes = b""):
    """Patch `aiohttp.ClientSession` inside src.piper_tts so its post()
    returns our controlled response. Yields the FakeSession so tests
    can introspect the request shape."""
    session = _FakeSession(_FakeResponse(status, body))
    with patch("src.piper_tts.aiohttp.ClientSession", return_value=session):
        yield session


# ---------------------------------------------------------------------------
# Capability / identity
# ---------------------------------------------------------------------------

def test_piper_tts_declares_non_streaming():
    t = PiperTTS(voice="de_DE-thorsten-high")
    # Must mirror Voxtral's flag so LiveKit wraps Piper with StreamAdapter.
    assert t.capabilities.streaming is False


def test_piper_tts_provider_and_model_labels():
    t = PiperTTS(voice="de_DE-thorsten-high", sample_rate=22050)
    assert t.provider == "Piper"
    assert t.model == "de_DE-thorsten-high"


def test_piper_tts_model_falls_back_when_voice_unset():
    t = PiperTTS()
    assert t.model == "piper-default"


# ---------------------------------------------------------------------------
# WAV unwrap
# ---------------------------------------------------------------------------

def test_unwrap_wav_extracts_pcm_and_metadata():
    wav = _build_wav([0, 100, -100, 32767, -32768], sample_rate=22050)
    pcm, sr, ch = _unwrap_wav(wav)
    assert sr == 22050
    assert ch == 1
    # 5 samples x 2 bytes
    assert len(pcm) == 10


def test_unwrap_wav_rejects_non_16bit_input():
    """Piper only emits 16-bit WAV. If a future server config ever returns
    8-bit or 32-bit we want to fail loudly, not silently produce drift."""
    from livekit.agents import APIConnectionError

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)  # 8-bit
        w.setframerate(22050)
        w.writeframes(b"\x00\x10\x20")

    with pytest.raises(APIConnectionError):
        _unwrap_wav(buf.getvalue())


# ---------------------------------------------------------------------------
# HTTP round-trip through ChunkedStream._run
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_piper_chunked_stream_posts_text_and_pushes_pcm():
    tts = PiperTTS(
        voice="de_DE-thorsten-high",
        base_url="http://127.0.0.1:5000",
        sample_rate=22050,
    )
    wav_bytes = _build_wav([0, 1000, -1000], sample_rate=22050)

    # Capture what the AudioEmitter receives; we care that the payload
    # after WAV-unwrap is the 6-byte PCM chunk (3 samples x 2 bytes).
    emitter = MagicMock()
    captured_pushes: list[bytes] = []
    emitter.push.side_effect = lambda data: captured_pushes.append(data)

    with _fake_aiohttp(status=200, body=wav_bytes) as session:
        stream = tts.synthesize("Guten Tag.")
        try:
            await stream._run(emitter)
        finally:
            await stream.aclose()

    assert session.last_post_url == "http://127.0.0.1:5000/"
    assert session.last_post_json == {"text": "Guten Tag.", "voice": "de_DE-thorsten-high"}

    emitter.initialize.assert_called_once()
    init_kwargs = emitter.initialize.call_args.kwargs
    assert init_kwargs["sample_rate"] == 22050
    assert init_kwargs["num_channels"] == 1
    assert init_kwargs["mime_type"] == "audio/pcm"

    assert captured_pushes == [wav_bytes[-6:]]  # the last 6 bytes are the raw PCM frames
    emitter.flush.assert_called_once()


@pytest.mark.asyncio
async def test_piper_chunked_stream_omits_voice_when_unset():
    """Without a voice, the body must omit the key entirely so the server
    falls back to whatever -m it was started with."""
    tts = PiperTTS(base_url="http://127.0.0.1:5000")
    wav_bytes = _build_wav([0], sample_rate=22050)
    emitter = MagicMock()

    with _fake_aiohttp(status=200, body=wav_bytes) as session:
        stream = tts.synthesize("Hallo.")
        try:
            await stream._run(emitter)
        finally:
            await stream.aclose()

    assert session.last_post_json == {"text": "Hallo."}


@pytest.mark.asyncio
async def test_piper_chunked_stream_translates_http_500_to_api_status_error():
    from livekit.agents import APIStatusError

    tts = PiperTTS(voice="de_DE-thorsten-high", base_url="http://127.0.0.1:5000")
    emitter = MagicMock()

    with _fake_aiohttp(status=500, body=b"boom"):
        stream = tts.synthesize("Fail.")
        try:
            with pytest.raises(APIStatusError) as exc_info:
                await stream._run(emitter)
        finally:
            await stream.aclose()

    assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# base_url normalisation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_piper_chunked_stream_strips_trailing_slash_on_base_url():
    tts = PiperTTS(base_url="http://127.0.0.1:5000/")
    wav_bytes = _build_wav([0], sample_rate=22050)
    emitter = MagicMock()

    with _fake_aiohttp(status=200, body=wav_bytes) as session:
        stream = tts.synthesize("x")
        try:
            await stream._run(emitter)
        finally:
            await stream.aclose()

    # One slash total, not two.
    assert session.last_post_url == "http://127.0.0.1:5000/"
