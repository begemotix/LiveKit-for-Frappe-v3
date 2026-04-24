"""Observability for the Type-B Voxtral reply path.

PURPOSE
-------
Measure where the "first-word stutter" on dynamic replies originates.
We pin observation points on the three audio-boundary transitions and
leave the functional behaviour untouched:

    [LLM-Text]──Layer-1──▶[Sentence Pacer]──Layer-2──▶[Voxtral TTS]
                                                       │
                                                       ▼
                                               (HTTP round-trip)
                                                       │
                                                       ▼
    [AudioEmitter]◀──Layer-3──▶[perform_audio_forwarding]
                                                       │
                                                       ▼
                                [_ParticipantAudioOutput.capture_frame]
                                                       │
                                                   (Layer-4: 500 ms AudioSource queue
                                                    — our queue_size_ms patch sits here)
                                                       │
                                                       ▼
                                                    [WebRTC]

Layers
------
  Layer-1 (text-side):  LLM emits text chunks → MistralDrivenAgent.llm_node
  Layer-2 (text-side):  StreamAdapter + SentenceStreamPacer batches sentences
                         before handing them to the TTS plugin
  Layer-3 (boundary):   Voxtral TTS HTTP call streams PCM back; AudioEmitter
                         slices bytes into 200 ms AudioFrames
  Layer-4 (audio-side): _ParticipantAudioOutput.capture_frame pushes into
                         rtc.AudioSource; queue_size_ms=500 (our patch) lives
                         inside the AudioSource buffer

What we log (all under logger "agent", structured via `extra`):

    tx_llm_first_chunk          first non-sentinel chunk out of llm_node
    tx_sent_batch_to_tts        each sentence-batch synthesize() call
    ax_first_tts_bytes          first bytes pushed to AudioEmitter per stream
    ax_capture_frame_burst_start  rising-edge capture_frame (>300 ms silence before)
    ax_capture_frame_n2         second capture_frame of the same burst

Burst detection relies on monotonic clock deltas between consecutive
`capture_frame()` calls; no reliance on `SpeechHandle` identity, which
keeps the patch independent of LiveKit-internal API shifts.

This module is imported by agent.py and activated once per worker via
`apply_voice_diagnostics()`. It is idempotent and fail-safe (logs a
warning and no-ops on unexpected class/attribute layout).
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger("agent")

_PATCH_APPLIED = False
_BURST_IDLE_THRESHOLD_S = 0.3  # gap that demarcates a new speech burst


def apply_voice_diagnostics() -> None:
    """Install the three audio-path probes. Safe to call multiple times.

    Must be called once per worker process before AgentSession.start()
    so the patched classes are in place before the first reply flows.
    """
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    _patch_stream_adapter_wrapper()
    _patch_voxtral_chunked_stream()
    _patch_participant_audio_output()

    _PATCH_APPLIED = True
    logger.info(
        "voice_diagnostics_applied",
        extra={
            "targets": [
                "livekit.agents.tts.stream_adapter.StreamAdapterWrapper._run",
                "livekit.plugins.mistralai.tts.ChunkedStream._run",
                "livekit.agents.voice.room_io._output._ParticipantAudioOutput.capture_frame",
            ],
            "burst_idle_threshold_ms": int(_BURST_IDLE_THRESHOLD_S * 1000),
        },
    )


# ---------------------------------------------------------------------------
# Layer-2 probe: sentence-batch handoff to TTS (text-side)
# ---------------------------------------------------------------------------

def _patch_stream_adapter_wrapper() -> None:
    try:
        from livekit.agents.tts import stream_adapter as lk_sa
    except ImportError as exc:
        logger.warning(
            "voice_diagnostics_layer2_unavailable",
            extra={"detail": f"{exc!r}"},
        )
        return

    target = getattr(lk_sa, "StreamAdapterWrapper", None)
    if target is None or not hasattr(target, "_run"):
        logger.warning(
            "voice_diagnostics_layer2_unavailable",
            extra={"detail": "StreamAdapterWrapper._run not found"},
        )
        return

    original_run = target._run

    # We wrap the wrapped_tts.synthesize call to observe each batch.
    # The synthesize happens inside _run's local `_synthesize` closure,
    # which we can't reach without rewriting. Instead, we monkey-patch
    # the parent StreamAdapter instance's `_wrapped_tts.synthesize`
    # method the first time _run is called on any wrapper — once wrapped,
    # every batch call goes through our logger.

    async def wrapped_run(self, output_emitter):  # type: ignore[no-untyped-def]
        wrapped_tts = self._tts._wrapped_tts
        if not getattr(wrapped_tts, "_voice_diag_synthesize_patched", False):
            original_synthesize = wrapped_tts.synthesize

            def observed_synthesize(text, *args, **kwargs):  # type: ignore[no-untyped-def]
                logger.info(
                    "tx_sent_batch_to_tts",
                    extra={
                        "t_monotonic_s": round(time.monotonic(), 4),
                        "batch_chars": len(text),
                        "batch_preview": text[:40],
                    },
                )
                return original_synthesize(text, *args, **kwargs)

            wrapped_tts.synthesize = observed_synthesize
            wrapped_tts._voice_diag_synthesize_patched = True

        return await original_run(self, output_emitter)

    target._run = wrapped_run


# ---------------------------------------------------------------------------
# Layer-3 probe: first TTS bytes arriving at AudioEmitter (boundary)
# ---------------------------------------------------------------------------

def _patch_voxtral_chunked_stream() -> None:
    try:
        from livekit.plugins.mistralai import tts as lk_voxtral_tts
    except ImportError as exc:
        logger.warning(
            "voice_diagnostics_layer3_unavailable",
            extra={"detail": f"{exc!r}"},
        )
        return

    target = getattr(lk_voxtral_tts, "ChunkedStream", None)
    if target is None or not hasattr(target, "_run"):
        logger.warning(
            "voice_diagnostics_layer3_unavailable",
            extra={"detail": "ChunkedStream._run not found"},
        )
        return

    original_run = target._run

    async def wrapped_run(self, output_emitter):  # type: ignore[no-untyped-def]
        original_push = output_emitter.push
        first_push_captured = False

        def observed_push(data):  # type: ignore[no-untyped-def]
            nonlocal first_push_captured
            if not first_push_captured:
                first_push_captured = True
                try:
                    size = len(data) if hasattr(data, "__len__") else -1
                except Exception:
                    size = -1
                logger.info(
                    "ax_first_tts_bytes",
                    extra={
                        "t_monotonic_s": round(time.monotonic(), 4),
                        "bytes": size,
                    },
                )
            return original_push(data)

        output_emitter.push = observed_push  # type: ignore[method-assign]
        try:
            return await original_run(self, output_emitter)
        finally:
            output_emitter.push = original_push  # type: ignore[method-assign]

    target._run = wrapped_run


# ---------------------------------------------------------------------------
# Layer-4 probe: AudioSource capture_frame + queued_duration (audio-side)
# ---------------------------------------------------------------------------

def _patch_participant_audio_output() -> None:
    try:
        from livekit.agents.voice.room_io import _output as lk_output
    except ImportError as exc:
        logger.warning(
            "voice_diagnostics_layer4_unavailable",
            extra={"detail": f"{exc!r}"},
        )
        return

    target = getattr(lk_output, "_ParticipantAudioOutput", None)
    if target is None or not hasattr(target, "capture_frame"):
        logger.warning(
            "voice_diagnostics_layer4_unavailable",
            extra={"detail": "_ParticipantAudioOutput.capture_frame not found"},
        )
        return

    original_capture_frame = target.capture_frame

    async def observed_capture_frame(self, frame):  # type: ignore[no-untyped-def]
        now = time.monotonic()
        last_ts: float | None = getattr(self, "_voice_diag_last_ts", None)
        frames_in_burst: int = getattr(self, "_voice_diag_frames_in_burst", 0)
        is_rising_edge = last_ts is None or (now - last_ts) > _BURST_IDLE_THRESHOLD_S

        if is_rising_edge:
            frames_in_burst = 0

        frame_dur_ms = (frame.samples_per_channel * 1000.0) / frame.sample_rate
        queued_before_ms = _safe_queued_duration_ms(self)

        if is_rising_edge or frames_in_burst == 1:
            logger.info(
                "ax_capture_frame_burst_start" if is_rising_edge else "ax_capture_frame_n2",
                extra={
                    "t_monotonic_s": round(now, 4),
                    "gap_since_last_ms": (
                        int((now - last_ts) * 1000) if last_ts is not None else -1
                    ),
                    "frame_dur_ms": round(frame_dur_ms, 2),
                    "frame_samples": frame.samples_per_channel,
                    "frame_sample_rate": frame.sample_rate,
                    "queued_duration_ms_before": queued_before_ms,
                },
            )

        result = await original_capture_frame(self, frame)

        if is_rising_edge or frames_in_burst == 1:
            queued_after_ms = _safe_queued_duration_ms(self)
            logger.info(
                "ax_capture_frame_queued_after",
                extra={
                    "t_monotonic_s": round(time.monotonic(), 4),
                    "position": "rising" if is_rising_edge else "n2",
                    "queued_duration_ms_after": queued_after_ms,
                },
            )

        self._voice_diag_last_ts = now
        self._voice_diag_frames_in_burst = frames_in_burst + 1
        return result

    target.capture_frame = observed_capture_frame


def _safe_queued_duration_ms(participant_audio_output) -> int:  # type: ignore[no-untyped-def]
    try:
        src = participant_audio_output._audio_source
        return int(src.queued_duration * 1000)
    except Exception:
        return -1
