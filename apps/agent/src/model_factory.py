from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any

from src.mode_config import resolve_voice_config, validate_mode_env

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

        pipeline_build_started = time.perf_counter()
        stt_kwargs: dict[str, Any] = {}
        if voice["language"]:
            stt_kwargs["language"] = voice["language"]

        tts_kwargs: dict[str, Any] = {}
        t_ref_audio_read_ms = 0.0
        t_ref_audio_b64_ms = 0.0
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
            logger.info("tts voice config: ref_audio active", extra={"ref_audio_path": voice["ref_audio"]})
        elif voice["voice_id"]:
            tts_kwargs["voice"] = voice["voice_id"]
            tts_voice_mode = "voice_id"
            logger.info("tts voice config: voice_id active", extra={"voice_id": voice["voice_id"]})
        else:
            raise ValueError(
                "Missing voice config for type_b: set AGENT_VOICE_REF_AUDIO or AGENT_VOICE_ID"
            )

        tts_kwargs["response_format"] = "pcm"
        llm_model = os.getenv("MISTRAL_LLM_MODEL") or "mistral-small-latest"
        stt_model = os.getenv("VOXTRAL_STT_MODEL", "")
        tts_model = os.getenv("VOXTRAL_TTS_MODEL", "")
        t_pipeline_build_ms = (time.perf_counter() - pipeline_build_started) * 1000

        return {
            "provider": "mistral_voxtral",
            "llm": mistralai.LLM(model=llm_model, temperature=0.8),
            "stt": mistralai.STT(model=stt_model, **stt_kwargs),
            "tts": mistralai.TTS(model=tts_model, **tts_kwargs),
            "metrics": {
                "t_pipeline_build_ms": t_pipeline_build_ms,
                "t_ref_audio_read_ms": t_ref_audio_read_ms,
                "t_ref_audio_b64_ms": t_ref_audio_b64_ms,
            },
            "tts_observability": {
                "tts_model": tts_model,
                "response_format": tts_kwargs["response_format"],
                "voice_mode": tts_voice_mode,
            },
        }

    raise ValueError(f"Unsupported mode: {mode}")
