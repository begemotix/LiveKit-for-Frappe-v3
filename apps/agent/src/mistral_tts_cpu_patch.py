"""Replace Voxtral plugin's per-sample Python PCM conversion with NumPy.

The upstream ``livekit-plugins-mistralai.tts._f32le_to_s16le`` converts the
float32 PCM chunks Voxtral streams back into the int16 PCM that LiveKit's
``AudioEmitter`` expects. Its implementation is a Python generator
expression running ``max/min/int`` per sample::

    return struct.pack(f"<{n}h", *(
        max(-32768, min(32767, int(s * 32767))) for s in floats
    ))

For a 9.4 s reply at 24 kHz that's 225,600 samples processed inside a
Python loop on the asyncio event loop. During this window Silero VAD,
``_ParticipantAudioOutput.capture_frame`` and the WebRTC frame push all
wait — which matches the "inference is slower than realtime" cascade
observed in production (voice_diagnostics, 2026-04-24).

LiveKit Agents itself uses NumPy for bulk audio work (``AudioByteStream``,
``rtc.AudioFrame``, ``inference.interruption`` — all ``import numpy as np``).
This patch brings the Voxtral plugin in line with that idiom until the
change lands upstream.

Contract
--------
- ``apply_mistral_tts_cpu_patch()`` replaces the module-level function
  ``livekit.plugins.mistralai.tts._f32le_to_s16le`` with a NumPy variant
  that is bit-perfect equivalent on the plugin's happy path (finite
  float32 inputs). Idempotent.
- The NumPy variant preserves the original's clamp-after-truncate
  semantics (``int(s * 32767)`` truncates toward zero, *then* clamps to
  [-32768, 32767]). See tests/test_mistral_tts_cpu_patch.py for the
  bit-perfect oracle check.
- Fail-safe: if the plugin module or attribute layout is not what we
  expect (e.g. after a future LiveKit upgrade that moves the function or
  changes its signature), we log a warning and no-op — Voxtral stays
  functional with the slow Python loop.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("agent")

_PATCH_APPLIED = False


def apply_mistral_tts_cpu_patch() -> None:
    """Install the NumPy-backed _f32le_to_s16le replacement. Idempotent."""
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    try:
        import numpy as np
    except ImportError as exc:
        logger.warning(
            "mistral_tts_cpu_patch_unavailable",
            extra={"detail": f"NumPy not importable: {exc!r}"},
        )
        return

    try:
        from livekit.plugins.mistralai import tts as lk_voxtral_tts
    except ImportError as exc:
        logger.warning(
            "mistral_tts_cpu_patch_unavailable",
            extra={"detail": f"mistralai TTS module not importable: {exc!r}"},
        )
        return

    if not hasattr(lk_voxtral_tts, "_f32le_to_s16le"):
        logger.warning(
            "mistral_tts_cpu_patch_unavailable",
            extra={"detail": "_f32le_to_s16le not found in mistralai.tts"},
        )
        return

    def _f32le_to_s16le_numpy(data: bytes) -> bytes:
        # np.trunc matches Python's int() (truncate toward zero) for
        # finite floats, so np.trunc -> clip -> int16 is bit-equivalent
        # to the original max(-32768, min(32767, int(s * 32767))).
        arr = np.frombuffer(data, dtype="<f4")
        scaled = np.trunc(arr * 32767.0)
        clipped = np.clip(scaled, -32768, 32767).astype("<i2")
        return clipped.tobytes()

    lk_voxtral_tts._f32le_to_s16le = _f32le_to_s16le_numpy
    _PATCH_APPLIED = True
    logger.info(
        "mistral_tts_cpu_patch_applied",
        extra={
            "target": "livekit.plugins.mistralai.tts._f32le_to_s16le",
            "backend": "numpy",
        },
    )
