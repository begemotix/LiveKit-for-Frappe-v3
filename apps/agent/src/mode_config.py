from __future__ import annotations

import os
from pathlib import Path

VALID_MODES = {"type_a", "type_b"}


def _required_env_keys(mode: str) -> list[str]:
    if mode == "type_a":
        return ["OPENAI_API_KEY"]
    if mode == "type_b":
        return ["MISTRAL_API_KEY", "VOXTRAL_STT_MODEL", "VOXTRAL_TTS_MODEL"]
    raise ValueError(f"Unsupported AGENT_MODE: {mode}")


def resolve_agent_mode() -> str:
    raw_mode = (os.getenv("AGENT_MODE") or "type_b").strip().lower()
    if raw_mode not in VALID_MODES:
        raise ValueError(f"Unsupported AGENT_MODE: {raw_mode}")
    return raw_mode


def validate_mode_env(mode: str) -> None:
    missing = [key for key in _required_env_keys(mode) if not (os.getenv(key) or "").strip()]
    if missing:
        raise ValueError(f"Missing required env vars for {mode}: {', '.join(missing)}")

    language = (os.getenv("AGENT_LANGUAGE") or "").strip().lower()
    if language and language not in {"de", "en"}:
        raise ValueError("AGENT_LANGUAGE must be 'de' or 'en' when set")

    if mode == "type_b":
        ref_audio = (os.getenv("AGENT_VOICE_REF_AUDIO") or "").strip()
        voice_id = (os.getenv("AGENT_VOICE_ID") or "").strip()

        if ref_audio:
            ref_path = Path(ref_audio)
            if not ref_path.is_file():
                raise ValueError(
                    f"AGENT_VOICE_REF_AUDIO does not exist or is not a file: {ref_audio}"
                )
            if not os.access(ref_path, os.R_OK):
                raise ValueError(f"AGENT_VOICE_REF_AUDIO is not readable: {ref_audio}")
        elif not voice_id:
            raise ValueError(
                "Missing voice config for type_b: set AGENT_VOICE_REF_AUDIO or AGENT_VOICE_ID"
            )


def resolve_voice_config() -> dict[str, str | None]:
    ref_audio = (os.getenv("AGENT_VOICE_REF_AUDIO") or "").strip() or None
    voice_id = (os.getenv("AGENT_VOICE_ID") or "").strip() or None
    language = (os.getenv("AGENT_LANGUAGE") or "").strip().lower() or None

    # D-08: ref_audio has priority over voice_id when both are set.
    if ref_audio:
        voice_id = None

    return {
        "ref_audio": ref_audio,
        "voice_id": voice_id,
        "language": language,
    }
