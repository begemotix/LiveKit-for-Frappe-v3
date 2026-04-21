import asyncio
import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

if "livekit" not in sys.modules:
    livekit_module = ModuleType("livekit")
    agents_module = ModuleType("livekit.agents")
    llm_module = ModuleType("livekit.agents.llm")
    mcp_module = ModuleType("livekit.agents.llm.mcp")

    class _FakeAgent:
        def __init__(self, instructions=""):
            self.instructions = instructions

    class _FakeAgentSession:
        def __init__(self, *args, **kwargs):
            pass

    def _function_tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    agents_module.JobContext = object
    agents_module.WorkerOptions = object
    agents_module.cli = SimpleNamespace(run_app=lambda options: options)
    agents_module.llm = llm_module
    agents_module.Agent = _FakeAgent
    agents_module.AgentSession = _FakeAgentSession
    llm_module.function_tool = _function_tool
    llm_module.mcp = mcp_module
    mcp_module.MCPToolset = lambda id, mcp_server: SimpleNamespace(id=id, mcp_server=mcp_server)

    livekit_module.agents = agents_module
    sys.modules["livekit"] = livekit_module
    sys.modules["livekit.agents"] = agents_module
    sys.modules["livekit.agents.llm"] = llm_module
    sys.modules["livekit.agents.llm.mcp"] = mcp_module

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
