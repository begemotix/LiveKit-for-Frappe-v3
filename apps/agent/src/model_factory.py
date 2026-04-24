from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any

from livekit.agents import tts as lk_tts

from src.mode_config import (
    resolve_tts_provider,
    resolve_voice_config,
    validate_mode_env,
)
from src.piper_server import piper_base_url
from src.piper_tts import PiperTTS

logger = logging.getLogger("agent")


def build_voice_pipeline(mode: str) -> dict[str, Any]:
    validate_mode_env(mode)
    voice = resolve_voice_config()

    if mode == "type_a":
        from livekit.plugins import openai

        return {
            "provider": "openai",
            "llm": openai.realtime.RealtimeModel(
                modalities=["audio", "text"],
                turn_detection={
                    "type": "server_vad",
                    "threshold": float(os.getenv("VAD_THRESHOLD", 0.5)),
                    "silence_duration_ms": int(os.getenv("VAD_SILENCE_DURATION_MS", 500)),
                },
            ),
            "stt": None,
            "tts": None,
        }

    if mode == "type_b":
        from livekit.plugins import mistralai

        from src.mistral_agent import NullLLM

        tts_provider = resolve_tts_provider()
        pipeline_build_started = time.perf_counter()
        stt_kwargs: dict[str, Any] = {}
        if voice["language"]:
            stt_kwargs["language"] = voice["language"]

        stt_model = os.getenv("VOXTRAL_STT_MODEL", "")
        tts_model = os.getenv("VOXTRAL_TTS_MODEL", "")

        t_ref_audio_read_ms = 0.0
        t_ref_audio_b64_ms = 0.0

        if tts_provider == "piper":
            piper_voice = (
                os.getenv("PIPER_VOICE") or "de_DE-thorsten-high"
            ).strip()
            piper_sample_rate = int(os.getenv("PIPER_SAMPLE_RATE") or "22050")
            piper_instance = PiperTTS(
                voice=piper_voice,
                base_url=piper_base_url(),
                sample_rate=piper_sample_rate,
            )
            # Same StreamAdapter wrapping as the Voxtral path — Piper's
            # HTTP server is also per-request-not-streaming, so we let
            # the SentenceStreamPacer batch sentences before each call.
            paced_tts = lk_tts.StreamAdapter(tts=piper_instance, text_pacing=True)
            tts_model_label = piper_voice
            tts_response_format = "pcm"
            tts_voice_mode = "preset"
            logger.info(
                "tts voice config: piper preset active",
                extra={"voice": piper_voice, "base_url": piper_base_url()},
            )
        else:
            tts_kwargs: dict[str, Any] = {}
            tts_voice_mode = "none"
            if voice["ref_audio"]:
                t_read_started = time.perf_counter()
                with open(voice["ref_audio"], "rb") as ref_file:
                    ref_audio_bytes = ref_file.read()
                t_ref_audio_read_ms = (time.perf_counter() - t_read_started) * 1000

                t_b64_started = time.perf_counter()
                encoded_ref_audio = base64.b64encode(ref_audio_bytes).decode("utf-8")
                t_ref_audio_b64_ms = (time.perf_counter() - t_b64_started) * 1000
                tts_kwargs["ref_audio"] = encoded_ref_audio
                tts_voice_mode = "ref_audio"
                logger.info(
                    "tts voice config: ref_audio active",
                    extra={"ref_audio_path": voice["ref_audio"]},
                )
            elif voice["voice_id"]:
                tts_kwargs["voice"] = voice["voice_id"]
                tts_voice_mode = "voice_id"
                logger.info(
                    "tts voice config: voice_id active",
                    extra={"voice_id": voice["voice_id"]},
                )
            else:
                raise ValueError(
                    "Missing voice config for type_b: set AGENT_VOICE_REF_AUDIO or AGENT_VOICE_ID"
                )

            tts_kwargs["response_format"] = "pcm"

            # Voxtral TTS has `capabilities.streaming=False` (it's a per-request
            # HTTP call). LiveKit's default tts_node wraps non-streaming TTS in
            # a StreamAdapter that synthesises one sentence at a time — so every
            # sentence boundary costs a full HTTP round-trip to Mistral. In
            # production that was audible as stuttering / long pauses mid-reply.
            # We wrap it explicitly with text_pacing=True so the built-in
            # SentenceStreamPacer batches sentences (up to ~300 chars) before
            # each TTS call, which smooths the audio and reduces API calls.
            voxtral_tts = mistralai.TTS(model=tts_model, **tts_kwargs)
            paced_tts = lk_tts.StreamAdapter(tts=voxtral_tts, text_pacing=True)
            tts_model_label = tts_model
            tts_response_format = tts_kwargs["response_format"]

        t_pipeline_build_ms = (time.perf_counter() - pipeline_build_started) * 1000

        # Phase-05 D-17: the real LLM is the external MistralOrchestrator
        # driven from agent.py's type_b branch. NullLLM only exists so the
        # LiveKit 1.5.5 `isinstance(session.llm, llm.LLM)` gate at
        # agent_activity.py:1191 opens and the overridden `llm_node` runs.
        return {
            "provider": f"mistral_voxtral_{tts_provider}" if tts_provider != "voxtral" else "mistral_voxtral",
            "llm": NullLLM(),
            "stt": mistralai.STT(model=stt_model, **stt_kwargs),
            "tts": paced_tts,
            "metrics": {
                "t_pipeline_build_ms": t_pipeline_build_ms,
                "t_ref_audio_read_ms": t_ref_audio_read_ms,
                "t_ref_audio_b64_ms": t_ref_audio_b64_ms,
            },
            "tts_observability": {
                "tts_model": tts_model_label,
                "response_format": tts_response_format,
                "voice_mode": tts_voice_mode,
                "stt_model": stt_model,
                "stt_streaming": "realtime" in stt_model,
                "tts_pacer_enabled": True,
                "tts_provider": tts_provider,
            },
        }

    raise ValueError(f"Unsupported mode: {mode}")
