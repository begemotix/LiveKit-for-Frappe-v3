from __future__ import annotations

import base64
import logging
import os
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

        stt_kwargs: dict[str, Any] = {}
        if voice["language"]:
            stt_kwargs["language"] = voice["language"]

        tts_kwargs: dict[str, Any] = {}
        if voice["ref_audio"]:
            with open(voice["ref_audio"], "rb") as ref_file:
                encoded_ref_audio = base64.b64encode(ref_file.read()).decode("utf-8")
            tts_kwargs["ref_audio"] = encoded_ref_audio
            logger.info("tts voice config: ref_audio active", extra={"ref_audio_path": voice["ref_audio"]})
        elif voice["voice_id"]:
            tts_kwargs["voice"] = voice["voice_id"]
            logger.info("tts voice config: voice_id active", extra={"voice_id": voice["voice_id"]})
        else:
            raise ValueError(
                "Missing voice config for type_b: set AGENT_VOICE_REF_AUDIO or AGENT_VOICE_ID"
            )

        llm_model = os.getenv("MISTRAL_LLM_MODEL") or "mistral-medium-latest"
        stt_model = os.getenv("VOXTRAL_STT_MODEL", "")
        tts_model = os.getenv("VOXTRAL_TTS_MODEL", "")

        return {
            "provider": "mistral_voxtral",
            "llm": mistralai.LLM(model=llm_model),
            "stt": mistralai.STT(model=stt_model, **stt_kwargs),
            "tts": mistralai.TTS(model=tts_model, **tts_kwargs),
        }

    raise ValueError(f"Unsupported mode: {mode}")
