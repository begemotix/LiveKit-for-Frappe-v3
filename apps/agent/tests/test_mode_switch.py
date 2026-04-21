import sys
from types import SimpleNamespace

import pytest


def test_default_mode_is_type_b(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENT_MODE", raising=False)
    from src.mode_config import resolve_agent_mode

    assert resolve_agent_mode() == "type_b"


def test_agent_mode_type_a_selects_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "type_a")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    fake_openai = SimpleNamespace(
        realtime=SimpleNamespace(RealtimeModel=lambda **kwargs: {"kind": "openai_realtime", **kwargs})
    )
    monkeypatch.setitem(sys.modules, "livekit.plugins", SimpleNamespace(openai=fake_openai))
    from src.mode_config import resolve_agent_mode
    from src.model_factory import build_voice_pipeline

    mode = resolve_agent_mode()
    pipeline = build_voice_pipeline(mode)

    assert mode == "type_a"
    assert pipeline["provider"] == "openai"
