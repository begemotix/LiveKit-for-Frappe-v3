from __future__ import annotations

import os
from typing import Any

from src.mode_config import resolve_voice_config, validate_mode_env


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

        tts_kwargs: dict[str, Any] = {}
        if voice["language"]:
            tts_kwargs["language"] = voice["language"]
        if voice["voice_id"]:
            tts_kwargs["voice_id"] = voice["voice_id"]
        if voice["ref_audio"]:
            tts_kwargs["ref_audio"] = voice["ref_audio"]

        return {
            "provider": "mistral_voxtral",
            "llm": mistralai.LLM(model=os.getenv("MISTRAL_LLM_MODEL") or "mistral-medium-latest"),
            "stt": mistralai.STT(model=os.getenv("VOXTRAL_STT_MODEL", "")),
            "tts": mistralai.TTS(model=os.getenv("VOXTRAL_TTS_MODEL", ""), **tts_kwargs),
        }

    raise ValueError(f"Unsupported mode: {mode}")
