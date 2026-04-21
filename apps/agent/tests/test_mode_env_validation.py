import pytest


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


@pytest.mark.parametrize("language", ["de", "en"])
def test_type_b_accepts_de_and_en_language_smoke(
    monkeypatch: pytest.MonkeyPatch, language: str
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("AGENT_LANGUAGE", language)
    from src.mode_config import validate_mode_env

    validate_mode_env("type_b")
