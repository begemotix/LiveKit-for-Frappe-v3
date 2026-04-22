import asyncio
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# Phase-04 era this file stubbed livekit.agents in sys.modules. That is no
# longer needed now that livekit-agents==1.5.5 is a pinned dependency —
# keeping the stub would shadow the real package and drop symbols that
# later-loaded test modules rely on (e.g. JobProcess, types.FlushSentinel).
from agent import entrypoint


class FakeRoom:
    def __init__(self):
        self.name = "room-type-b"
        self.remote_participants = {"p1": SimpleNamespace(identity="participant-1")}
        self._handlers = {}

    def on(self, event_name):
        def decorator(func):
            self._handlers[event_name] = func
            return func

        return decorator


class FakeContext:
    def __init__(self):
        self.room = FakeRoom()
        self.log_context_fields = {}

    async def connect(self):
        return None


@pytest.mark.asyncio
async def test_type_b_provider_error_triggers_hard_fail() -> None:
    with patch("agent.resolve_agent_mode", return_value="type_b"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", side_effect=RuntimeError("mistral unavailable")), \
         patch.dict(os.environ, {"AGENT_MODE": "type_b"}, clear=False):
        with pytest.raises(RuntimeError, match="mistral unavailable"):
            await entrypoint(FakeContext())


@pytest.mark.asyncio
async def test_type_b_provider_error_does_not_fallback_to_type_a() -> None:
    attempted_modes = []

    def _failing_pipeline(mode: str):
        attempted_modes.append(mode)
        raise RuntimeError("provider failure")

    with patch("agent.resolve_agent_mode", return_value="type_b"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", side_effect=_failing_pipeline), \
         patch("agent.build_frappe_mcp_server") as mcp_server_mock:
        with pytest.raises(RuntimeError, match="provider failure"):
            await entrypoint(FakeContext())

    assert attempted_modes == ["type_b"]
    mcp_server_mock.assert_not_called()
