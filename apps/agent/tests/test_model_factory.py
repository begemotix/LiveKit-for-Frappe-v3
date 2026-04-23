"""Phase-05 step 1.3 — tests for build_voice_pipeline.

Confirms the contract shift from the previous `mistralai.LLM` to
`NullLLM` for the type_b branch while asserting type_a remains
byte-compatible (same provider key, same dict shape).
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


# ---------------------------------------------------------------------------
# type_b — llm is NullLLM, STT/TTS come from the real livekit mistralai plugin
# ---------------------------------------------------------------------------

def test_build_voice_pipeline_type_b_returns_null_llm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from livekit.agents import llm as lk_llm

    ref_audio_file = tmp_path / "voice.mp3"
    ref_audio_file.write_bytes(b"audio-bytes")

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.setenv("AGENT_VOICE_REF_AUDIO", str(ref_audio_file))
    monkeypatch.delenv("AGENT_VOICE_ID", raising=False)

    from src.model_factory import build_voice_pipeline

    pipeline = build_voice_pipeline("type_b")

    assert pipeline["provider"] == "mistral_voxtral"
    # Phase-2 change: pipeline no longer owns the LLM for type_b. The
    # LLM is constructed in agent.py (MistralAgentLLM with agent_id) and
    # passed directly to AgentSession. The factory returns only
    # STT + TTS + observability.
    assert pipeline["llm"] is None

    # STT/TTS are still real livekit-mistralai plugins.
    assert pipeline["stt"] is not None
    assert pipeline["tts"] is not None
    assert pipeline["tts_observability"]["response_format"] == "pcm"
    assert pipeline["tts_observability"]["voice_mode"] == "ref_audio"
    assert pipeline["tts_observability"]["tts_pacer_enabled"] is True


def test_build_voice_pipeline_type_b_tts_is_wrapped_in_stream_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Voxtral TTS is non-streaming; the factory must wrap it in
    tts.StreamAdapter with text_pacing=True so LiveKit batches sentences
    before each HTTP synthesis call (fix for production stuttering)."""
    from livekit.agents import tts as lk_tts

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-mini-tts-latest")
    monkeypatch.delenv("AGENT_VOICE_REF_AUDIO", raising=False)
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")

    from src.model_factory import build_voice_pipeline

    pipeline = build_voice_pipeline("type_b")

    assert isinstance(pipeline["tts"], lk_tts.StreamAdapter)
    # StreamAdapter advertises streaming=True so the default tts_node does
    # not double-wrap it.
    assert pipeline["tts"].capabilities.streaming is True
    # Confirm the pacer is active inside the adapter.
    assert pipeline["tts"]._stream_pacer is not None


def test_build_voice_pipeline_type_b_stt_streaming_flag_reflects_model_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Voxtral STT plugin auto-enables streaming when the model name
    contains 'realtime'. The observability dict exposes that flag so
    operators can confirm from logs which path is active."""
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-mini-tts-latest")
    monkeypatch.delenv("AGENT_VOICE_REF_AUDIO", raising=False)
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")

    from src.model_factory import build_voice_pipeline

    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-mini-transcribe-realtime-2602")
    pipeline = build_voice_pipeline("type_b")
    assert pipeline["tts_observability"]["stt_streaming"] is True
    assert pipeline["stt"].capabilities.streaming is True

    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-mini-latest")
    pipeline = build_voice_pipeline("type_b")
    assert pipeline["tts_observability"]["stt_streaming"] is False
    assert pipeline["stt"].capabilities.streaming is False


def test_build_voice_pipeline_type_b_keeps_voice_selection_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """voice_id path still works when ref_audio is absent."""
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_test")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.setenv("VOXTRAL_STT_MODEL", "voxtral-stt")
    monkeypatch.setenv("VOXTRAL_TTS_MODEL", "voxtral-tts")
    monkeypatch.delenv("AGENT_VOICE_REF_AUDIO", raising=False)
    monkeypatch.setenv("AGENT_VOICE_ID", "en_paul_neutral")

    from src.model_factory import build_voice_pipeline

    pipeline = build_voice_pipeline("type_b")
    assert pipeline["tts_observability"]["voice_mode"] == "voice_id"


# ---------------------------------------------------------------------------
# type_a — regression guard: llm is still OpenAI Realtime, dict shape unchanged
# ---------------------------------------------------------------------------

def test_build_voice_pipeline_type_a_llm_remains_openai_realtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Stub the livekit.plugins.openai module to avoid a real API
    # construction, while keeping the type_a dispatch path intact.
    fake_openai = SimpleNamespace(
        realtime=SimpleNamespace(
            RealtimeModel=lambda **kwargs: {"kind": "openai_realtime", **kwargs}
        )
    )
    monkeypatch.setitem(
        sys.modules, "livekit.plugins",
        SimpleNamespace(openai=fake_openai),
    )

    from src.model_factory import build_voice_pipeline

    pipeline = build_voice_pipeline("type_a")

    assert pipeline["provider"] == "openai"
    # Still a RealtimeModel descriptor, not a NullLLM or a Mistral stub.
    assert pipeline["llm"]["kind"] == "openai_realtime"
    assert pipeline["stt"] is None  # realtime model handles STT inline
    assert pipeline["tts"] is None  # realtime model handles TTS inline
