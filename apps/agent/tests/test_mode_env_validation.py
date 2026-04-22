import pytest
from pathlib import Path


def test_type_b_requires_mistral_and_voxtral_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_MODE", "type_b")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("VOXTRAL_STT_MODEL", raising=False)
    monkeypatch.delenv("VOXTRAL_TTS_MODEL", raising=False)
    from src.mode_config import validate_mode_env

    with pytest.raises(ValueError) as exc:
        validate_mode_env("type_b")

    msg = str(exc.value)
    assert "MISTRAL_API_KEY" in msg
    assert "VOXTRAL_STT_MODEL" in msg
    assert "VOXTRAL_TTS_MODEL" in msg


def test_ref_audio_overrides_voice_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_VOICE_ID", "voice-id")
    monkeypatch.setenv("AGENT_VOICE_REF_AUDIO", "https://example.com/ref.wav")
    from src.mode_config import resolve_voice_config

    voice = resolve_voice_config()
    assert voice["ref_audio"] == "https://example.com/ref.wav"
    assert voice["voice_id"] is None


def test_type_b_ref_audio_file_missing_hard_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing_file = tmp_path / "does-not-exist.mp3"
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("AGENT_VOICE_REF_AUDIO", str(missing_file))
    monkeypatch.delenv("AGENT_VOICE_ID", raising=False)
    from src.mode_config import validate_mode_env

    with pytest.raises(ValueError) as exc:
        validate_mode_env("type_b")
    assert "AGENT_VOICE_REF_AUDIO does not exist or is not a file" in str(exc.value)


def test_type_b_ref_audio_wins_over_voice_id_in_pipeline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ref_audio_file = tmp_path / "voice_ref_de.mp3"
    ref_audio_file.write_bytes(b"fake-audio-bytes")

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("AGENT_VOICE_REF_AUDIO", str(ref_audio_file))
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")
    from src.model_factory import build_voice_pipeline

    pipeline = build_voice_pipeline("type_b")
    tts = pipeline["tts"]
    tts_opts = tts._opts  # pylint: disable=protected-access

    assert tts_opts.ref_audio is not None
    assert tts_opts.voice is None


@pytest.mark.parametrize("language", ["de", "en"])
def test_type_b_accepts_de_and_en_language_smoke(
    monkeypatch: pytest.MonkeyPatch, language: str
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")
    monkeypatch.delenv("AGENT_VOICE_REF_AUDIO", raising=False)
    monkeypatch.setenv("AGENT_LANGUAGE", language)
    from src.mode_config import validate_mode_env

    validate_mode_env("type_b")


# Phase-05 D-17: three type_b misconfiguration cases

def test_type_b_missing_agent_id_hard_fails_in_prod_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")
    monkeypatch.delenv("MISTRAL_AGENT_ID", raising=False)
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    from src.mode_config import validate_mode_env

    with pytest.raises(ValueError) as exc:
        validate_mode_env("type_b")
    msg = str(exc.value)
    assert "MISTRAL_AGENT_ID" in msg
    assert "Mistral Console" in msg
    assert "MISTRAL_STATELESS_MODE=true" in msg


def test_type_b_missing_llm_model_hard_fails_in_stateless_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")
    monkeypatch.setenv("MISTRAL_STATELESS_MODE", "true")
    monkeypatch.delenv("MISTRAL_LLM_MODEL", raising=False)
    from src.mode_config import validate_mode_env

    with pytest.raises(ValueError) as exc:
        validate_mode_env("type_b")
    msg = str(exc.value)
    assert "MISTRAL_LLM_MODEL" in msg
    assert "mistral-small-latest" in msg


def test_mistral_stateless_mode_rejects_non_boolean_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")
    monkeypatch.setenv("MISTRAL_STATELESS_MODE", "maybe")
    from src.mode_config import validate_mode_env

    with pytest.raises(ValueError) as exc:
        validate_mode_env("type_b")
    msg = str(exc.value)
    assert "MISTRAL_STATELESS_MODE must be a boolean" in msg
    assert "'maybe'" in msg


def test_type_b_stateless_mode_warns_when_agent_id_also_set(
    monkeypatch: pytest.MonkeyPatch, caplog
) -> None:
    import logging

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")
    monkeypatch.setenv("MISTRAL_STATELESS_MODE", "true")
    monkeypatch.setenv("MISTRAL_LLM_MODEL", "mistral-small-latest")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_conflict")
    from src.mode_config import validate_mode_env, resolve_mistral_config

    with caplog.at_level(logging.WARNING, logger="src.mode_config"):
        validate_mode_env("type_b")
    assert any(
        "mistral_agent_id_ignored_in_stateless_mode" in rec.message
        for rec in caplog.records
    )
    cfg = resolve_mistral_config()
    assert cfg["stateless"] is True
    assert cfg["agent_id"] is None
    assert cfg["llm_model"] == "mistral-small-latest"


def test_resolve_mistral_config_production_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_prod")
    monkeypatch.setenv("MISTRAL_LLM_MODEL", "should-be-ignored")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    from src.mode_config import resolve_mistral_config

    cfg = resolve_mistral_config()
    assert cfg["stateless"] is False
    assert cfg["agent_id"] == "ag_prod"
    assert cfg["llm_model"] is None
