from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

VALID_MODES = {"type_a", "type_b"}

# Phase-05 D-17: MISTRAL_AGENT_ID is the production contract for type_b.
# MISTRAL_STATELESS_MODE=true is an explicit dev/test escape hatch that swaps
# the Console-Agent path for a stateless chat.complete call that requires
# MISTRAL_LLM_MODEL. The two paths never coexist silently.
_TRUE_STRINGS = frozenset({"true", "1", "yes", "on"})
_FALSE_STRINGS = frozenset({"false", "0", "no", "off"})


def _resolve_stateless_mode() -> bool:
    raw = (os.getenv("MISTRAL_STATELESS_MODE") or "").strip().lower()
    if raw == "":
        return False
    if raw in _TRUE_STRINGS:
        return True
    if raw in _FALSE_STRINGS:
        return False
    raise ValueError(
        f"MISTRAL_STATELESS_MODE must be a boolean (true/false, 1/0, yes/no, on/off); "
        f"got: {os.getenv('MISTRAL_STATELESS_MODE')!r}"
    )


def _required_env_keys(mode: str) -> list[str]:
    if mode == "type_a":
        return ["OPENAI_API_KEY"]
    if mode == "type_b":
        base = ["MISTRAL_API_KEY", "VOXTRAL_STT_MODEL", "VOXTRAL_TTS_MODEL"]
        if _resolve_stateless_mode():
            base.append("MISTRAL_LLM_MODEL")
        else:
            base.append("MISTRAL_AGENT_ID")
        return base
    raise ValueError(f"Unsupported AGENT_MODE: {mode}")


def resolve_agent_mode() -> str:
    raw_mode = (os.getenv("AGENT_MODE") or "type_b").strip().lower()
    if raw_mode not in VALID_MODES:
        raise ValueError(f"Unsupported AGENT_MODE: {raw_mode}")
    return raw_mode


def validate_mode_env(mode: str) -> None:
    # Validate the stateless switch first — this may raise with its own
    # precise message for case (3) (bad boolean value).
    stateless = False
    if mode == "type_b":
        stateless = _resolve_stateless_mode()

    missing = [key for key in _required_env_keys(mode) if not (os.getenv(key) or "").strip()]

    if missing:
        # Tailor the message for the two type_b-specific misconfigurations
        # (cases 1 and 2) when the base Mistral/Voxtral keys are all present.
        # If base keys are also missing, fall through to the generic error
        # so callers learn everything that's broken at once.
        if mode == "type_b":
            base_keys = {"MISTRAL_API_KEY", "VOXTRAL_STT_MODEL", "VOXTRAL_TTS_MODEL"}
            base_missing = [k for k in missing if k in base_keys]

            if not base_missing and "MISTRAL_AGENT_ID" in missing:
                raise ValueError(
                    "type_b production mode requires MISTRAL_AGENT_ID. "
                    "Set it to the agent id from the Mistral Console "
                    "(https://console.mistral.ai), or set "
                    "MISTRAL_STATELESS_MODE=true for dev/stateless mode "
                    "(which then requires MISTRAL_LLM_MODEL)."
                )

            if not base_missing and "MISTRAL_LLM_MODEL" in missing:
                raise ValueError(
                    "type_b stateless mode (MISTRAL_STATELESS_MODE=true) requires "
                    "MISTRAL_LLM_MODEL, e.g. 'mistral-small-latest'. "
                    "Unset MISTRAL_STATELESS_MODE to use the production "
                    "Console-Agent path via MISTRAL_AGENT_ID instead."
                )

        raise ValueError(f"Missing required env vars for {mode}: {', '.join(missing)}")

    # Stateless mode deliberately ignores MISTRAL_AGENT_ID. Surface it so
    # operators don't silently rely on an agent that isn't being used.
    if mode == "type_b" and stateless:
        agent_id = (os.getenv("MISTRAL_AGENT_ID") or "").strip()
        if agent_id:
            logger.warning(
                "mistral_agent_id_ignored_in_stateless_mode",
                extra={"agent_id_present": True},
            )

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


def resolve_mistral_config() -> dict[str, object]:
    """Resolve type_b Mistral runtime config from ENV.

    Call after `validate_mode_env("type_b")` to ensure invariants hold.
    Returns a dict with keys `stateless`, `agent_id`, `llm_model`.
    In stateless mode, `agent_id` is deliberately returned as None even if
    the MISTRAL_AGENT_ID env var is set (a warning is emitted from
    `validate_mode_env`).
    """
    stateless = _resolve_stateless_mode()
    agent_id = (os.getenv("MISTRAL_AGENT_ID") or "").strip() or None
    llm_model = (os.getenv("MISTRAL_LLM_MODEL") or "").strip() or None

    if stateless:
        agent_id = None
    else:
        llm_model = None

    return {
        "stateless": stateless,
        "agent_id": agent_id,
        "llm_model": llm_model,
    }
