"""LiveKit TTS adapter for a local Piper HTTP server.

Why this module exists
----------------------
The community package ``livekit-plugins-piper-tts==0.1.0`` uses a
synchronous ``requests.post`` inside an async ``_run`` and would block
the asyncio event loop for the full Piper generation time — exactly the
failure mode we just spent a week removing from the Voxtral path. This
module is a ~90-line replacement that uses ``aiohttp``, talks to Piper's
built-in HTTP server (``python -m piper.http_server``), and pushes raw
PCM at WAV-native sample rate to LiveKit's ``AudioEmitter``.

Contract
--------
- ``PiperTTS(base_url=..., voice=..., sample_rate=22050)`` constructs a
  LiveKit ``tts.TTS`` subclass that calls Piper once per sentence batch
  via POST JSON ``{"text": ..., "voice": ...}``. The HTTP server returns
  a 16-bit mono WAV, which we unwrap and hand to the AudioEmitter as
  raw PCM so the in-process WAV decoder's codepath does not need to run.
- One HTTP call per ``synthesize()`` — no intra-sentence streaming.
  LiveKit's ``StreamAdapter`` on top takes care of sentence batching,
  matching the pattern we already use for Voxtral.
- ``capabilities.streaming=False`` so LiveKit wraps the TTS exactly like
  the Voxtral path.

Out of scope
------------
- Voice cloning (Piper preset voices only).
- Per-chunk streaming from Piper (Piper's HTTP server ships the full WAV
  in one response; proper SSE streaming would need a Piper-server fork).
"""
from __future__ import annotations

import io
import logging
import wave
from dataclasses import dataclass

import aiohttp
from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    tts,
    utils,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr
from livekit.agents.utils import is_given

logger = logging.getLogger("agent")

DEFAULT_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_SAMPLE_RATE = 24000
NUM_CHANNELS = 1


@dataclass
class _TTSOptions:
    base_url: str
    voice: str | None
    sample_rate: int


class PiperTTS(tts.TTS):
    def __init__(
        self,
        *,
        voice: NotGivenOr[str] = NOT_GIVEN,
        base_url: NotGivenOr[str] = NOT_GIVEN,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
    ) -> None:
        """Args:
        voice: Piper voice name (e.g. ``de_DE-thorsten-high``). When the
            Piper HTTP server was started with ``-m <voice>`` this may be
            left unset; the server then uses the model passed on its CLI.
        base_url: URL where the Piper HTTP server is listening, e.g.
            ``http://127.0.0.1:5000``.
        sample_rate: Declared sample rate for the TTS pipeline. Defaults to
            24000 Hz for LiveKit compatibility. Piper output will be
            labeled with its native rate from the WAV header.
        """
        resolved_sr = sample_rate if is_given(sample_rate) else DEFAULT_SAMPLE_RATE
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=resolved_sr,
            num_channels=NUM_CHANNELS,
        )
        self._opts = _TTSOptions(
            base_url=(base_url if is_given(base_url) else DEFAULT_BASE_URL).rstrip("/"),
            voice=voice if is_given(voice) else None,
            sample_rate=resolved_sr,
        )

    @property
    def model(self) -> str:
        return self._opts.voice or "piper-default"

    @property
    def provider(self) -> str:
        return "Piper"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return _PiperChunkedStream(
            tts=self, input_text=text, conn_options=conn_options
        )


class _PiperChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: PiperTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: PiperTTS = tts
        self._opts = tts._opts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        payload: dict[str, str] = {"text": self.input_text}
        if self._opts.voice:
            payload["voice"] = self._opts.voice

        timeout = aiohttp.ClientTimeout(total=self._conn_options.timeout)
        try:
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.post(
                    f"{self._opts.base_url}/",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                ) as resp,
            ):
                if resp.status != 200:
                    body = await resp.text()
                    raise APIStatusError(
                        f"Piper HTTP {resp.status}: {body[:200]}",
                        status_code=resp.status,
                        body=body,
                    )
                wav_bytes = await resp.read()
        except aiohttp.ServerTimeoutError as exc:
            raise APITimeoutError() from exc
        except aiohttp.ClientError as exc:
            raise APIConnectionError() from exc

        pcm_bytes, sample_rate, channels = _unwrap_wav(wav_bytes)

        output_emitter.initialize(
            request_id=utils.shortuuid(),
            sample_rate=sample_rate,
            num_channels=channels,
            mime_type="audio/pcm",
        )

        # Chunk the PCM data into 20ms frames to keep the audio pipeline happy.
        # 20ms at sample_rate with 16-bit (2 bytes) samples.
        bytes_per_frame = int(sample_rate * 0.02) * 2 * channels
        
        frames_pushed = 0
        for i in range(0, len(pcm_bytes), bytes_per_frame):
            chunk = pcm_bytes[i : i + bytes_per_frame]
            output_emitter.push(chunk)
            frames_pushed += 1
            
        output_emitter.flush()
        logger.debug(
            "piper_tts_pushed_frames", 
            extra={"frames": frames_pushed, "sample_rate": sample_rate}
        )


def _unwrap_wav(wav_bytes: bytes) -> tuple[bytes, int, int]:
    """Return (pcm_bytes, sample_rate, num_channels) from a 16-bit mono WAV.

    Piper's ``http_server`` always returns mono 16-bit PCM WAV; we parse
    it with the stdlib ``wave`` module so we don't pull in ``soundfile``
    as a dependency. Any other WAV format would throw at the width check
    — we want that loud, not silent audio drift.
    """
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        width = wav.getsampwidth()
        if width != 2:
            raise APIConnectionError(
                f"Piper returned unexpected sample width: {width * 8} bit (want 16)"
            )
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        pcm = wav.readframes(wav.getnframes())
    return pcm, sample_rate, channels
