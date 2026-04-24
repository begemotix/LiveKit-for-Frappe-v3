"""Prebuffer patch: accumulate ~300 ms of audio before forwarding to
rtc.AudioSource, so the 500 ms queue is populated and can absorb
intra-reply jitter.

Problem this solves
-------------------
The voice_diagnostics run proved that the ``rtc.AudioSource`` queue
sits near-empty during dynamic TTS replies: Voxtral delivers PCM in
near-realtime, each ``capture_frame`` call adds ~200 ms of audio and
the FFI queue is drained almost as fast. `queue_size_ms=500` is a
*maximum*, not a *minimum* — raising it achieves nothing on its own if
the producer never gets ahead.

This patch inserts a short warm-up buffer on the Agent side:
- Each speech burst (detected by a silence > RESET_IDLE_MS between
  consecutive ``capture_frame`` calls) starts with a fill-phase.
- Frames are accumulated in Python until ~PREBUFFER_MS of audio has
  arrived, then the full batch is pushed to the original
  ``capture_frame`` in quick succession. From there on the burst
  passes through directly.
- A safety cap (MAX_WAIT_MS since burst start) releases whatever we
  have in case Voxtral stalls, so the user never waits forever.

Fail-safe: if the target class / attribute layout shifts under a
future LiveKit upgrade, we log a single warning and fall through to
the original capture_frame behaviour.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger("agent")

_PATCH_APPLIED = False

# Tunables — conservative defaults for the first deploy.
PREBUFFER_MS = 300          # target fill before release
MAX_WAIT_MS = 500           # safety cap: release even if fill not reached
RESET_IDLE_S = 0.3          # gap that demarcates a new burst (same as diag)


def apply_audio_prebuffer_patch(
    prebuffer_ms: int = PREBUFFER_MS,
    max_wait_ms: int = MAX_WAIT_MS,
) -> None:
    """Install the capture_frame prebuffer. Idempotent."""
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    try:
        from livekit.agents.voice.room_io import _output as lk_output
    except ImportError as exc:
        logger.warning(
            "audio_prebuffer_patch_unavailable",
            extra={"detail": f"{exc!r}"},
        )
        return

    target_cls = getattr(lk_output, "_ParticipantAudioOutput", None)
    if target_cls is None or not hasattr(target_cls, "capture_frame"):
        logger.warning(
            "audio_prebuffer_patch_unavailable",
            extra={"detail": "_ParticipantAudioOutput.capture_frame not found"},
        )
        return

    original_capture_frame = target_cls.capture_frame

    async def prebuffered_capture_frame(self, frame):  # type: ignore[no-untyped-def]
        now = time.monotonic()
        last_ts = getattr(self, "_prebuf_last_ts", None)
        is_rising_edge = last_ts is None or (now - last_ts) > RESET_IDLE_S

        if is_rising_edge:
            self._prebuf_frames = []
            self._prebuf_duration_ms = 0.0
            self._prebuf_start_ts = now
            self._prebuf_released = False

        self._prebuf_last_ts = now

        if getattr(self, "_prebuf_released", True):
            return await original_capture_frame(self, frame)

        frame_ms = (frame.samples_per_channel * 1000.0) / frame.sample_rate
        self._prebuf_frames.append(frame)
        self._prebuf_duration_ms += frame_ms

        elapsed_ms = (now - self._prebuf_start_ts) * 1000.0
        if (
            self._prebuf_duration_ms >= prebuffer_ms
            or elapsed_ms >= max_wait_ms
        ):
            # Release the accumulated frames in one quick burst. The
            # first call to original_capture_frame may block at the
            # queue_size_ms ceiling, which is exactly what we want:
            # subsequent frames then stream behind a properly filled
            # jitter buffer.
            buffered = self._prebuf_frames
            self._prebuf_frames = []
            self._prebuf_released = True
            logger.info(
                "audio_prebuffer_released",
                extra={
                    "frames_burst": len(buffered),
                    "buffered_duration_ms": round(self._prebuf_duration_ms, 1),
                    "wait_ms": round(elapsed_ms, 1),
                    "trigger": (
                        "fill" if self._prebuf_duration_ms >= prebuffer_ms else "timeout"
                    ),
                },
            )
            for f in buffered:
                await original_capture_frame(self, f)

    target_cls.capture_frame = prebuffered_capture_frame
    _PATCH_APPLIED = True
    logger.info(
        "audio_prebuffer_patch_applied",
        extra={
            "prebuffer_ms": prebuffer_ms,
            "max_wait_ms": max_wait_ms,
            "reset_idle_ms": int(RESET_IDLE_S * 1000),
        },
    )
