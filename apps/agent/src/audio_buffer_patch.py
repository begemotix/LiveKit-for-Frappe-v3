"""Test patch: enlarge WebRTC AudioSource jitter buffer for agent speech.

LiveKit Agents 1.5.5 hardcodes ``queue_size_ms=200`` on the
``rtc.AudioSource`` inside ``_ParticipantAudioOutput.__init__``
(``livekit/agents/voice/room_io/_output.py:40``). The LiveKit rtc
default is 1000 ms; Agents picks a tighter value for low-latency
Realtime LLM paths.

For non-streaming TTS (Voxtral, one HTTP round-trip per sentence batch)
this produces audible gaps between batches larger than the 200 ms buffer
can absorb. This module lets us raise that buffer without forking the
vendored LiveKit Agents code.

Contract:
- ``apply_audio_buffer_patch(queue_size_ms=500)`` wraps
  ``_ParticipantAudioOutput.__init__`` once, idempotently. After the
  original init runs, the freshly created ``_audio_source`` is replaced
  with a new ``rtc.AudioSource`` that uses the requested queue size.
- The replacement happens *before* ``start()`` publishes the track, so
  no published audio is ever disconnected.
- If the target class or attribute layout is not what we expect (e.g.
  after a future LiveKit upgrade), the patch logs a warning and is a
  no-op — the agent keeps working with the 200 ms default.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("agent")

_PATCH_APPLIED = False


def apply_audio_buffer_patch(queue_size_ms: int = 500) -> None:
    """Install the class-level monkey-patch. Safe to call multiple times.

    Should be called once per worker process, early in the entrypoint,
    before ``AgentSession.start(room=…)`` triggers the RoomIO init
    path that constructs ``_ParticipantAudioOutput``.
    """
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    try:
        from livekit import rtc
        from livekit.agents.voice.room_io import _output as lk_output
    except ImportError as exc:
        logger.warning(
            "audio_buffer_patch_unavailable",
            extra={"detail": f"LiveKit modules not importable: {exc!r}"},
        )
        return

    target_cls = getattr(lk_output, "_ParticipantAudioOutput", None)
    if target_cls is None:
        logger.warning(
            "audio_buffer_patch_unavailable",
            extra={"detail": "_ParticipantAudioOutput not found in livekit.agents.voice.room_io._output"},
        )
        return

    original_init = target_cls.__init__

    def patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        original_init(self, *args, **kwargs)
        try:
            old_source = self._audio_source
            sample_rate = old_source._sample_rate
            num_channels = old_source._num_channels
            self._audio_source = rtc.AudioSource(
                sample_rate, num_channels, queue_size_ms=queue_size_ms
            )
        except AttributeError as exc:
            logger.warning(
                "audio_buffer_patch_replace_failed",
                extra={
                    "detail": f"unexpected _audio_source layout: {exc!r}",
                    "queue_size_ms_requested": queue_size_ms,
                },
            )

    target_cls.__init__ = patched_init
    _PATCH_APPLIED = True
    logger.info(
        "audio_buffer_patch_applied",
        extra={
            "queue_size_ms": queue_size_ms,
            "default_was_ms": 200,
            "patched_class": "livekit.agents.voice.room_io._output._ParticipantAudioOutput",
        },
    )
