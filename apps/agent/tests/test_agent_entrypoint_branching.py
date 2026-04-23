"""Entrypoint branching tests (Phase-2 architecture).

After the Phase-2 cut-over:

- type_a  → AgentSession carries a ``MCPToolset(id="frappe_mcp")`` in
            ``tools=[…]`` and uses OpenAI Realtime as the LLM.
- type_b  → AgentSession carries ``mcp_servers=[frappe_server]`` and
            a ``MistralAgentLLM`` instance that routes to the Mistral
            Console Agent via ``agent_id`` (or to a stateless model
            when ``MISTRAL_STATELESS_MODE`` is set).

We patch out the Mistral/LiveKit heavy-lifters so the test never
touches the network, never spawns a subprocess, and never instantiates
a real MCP or LLM client. The assertions only verify that the session
is wired with the right *kind* of components — runtime behaviour is
covered by the dedicated test suites for each of those building
blocks.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared test doubles
# ---------------------------------------------------------------------------

class FakeAgentSession:
    """Minimal stand-in for LiveKit's ``AgentSession``. Records the
    kwargs it was constructed with so tests can assert on them."""

    last_instance: Optional["FakeAgentSession"] = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.tools = kwargs.get("tools") or []
        self.mcp_servers = kwargs.get("mcp_servers") or []
        self.llm = kwargs.get("llm")
        self.stt = kwargs.get("stt")
        self.tts = kwargs.get("tts")
        self._handlers = {}
        FakeAgentSession.last_instance = self

    def on(self, event_name: str):
        def decorator(func):
            self._handlers[event_name] = func
            return func
        return decorator

    async def start(self, **_kwargs):
        return None


class FakeRoom:
    def __init__(self):
        self.name = "branching-test-room"
        self.remote_participants = {
            "p1": SimpleNamespace(identity="participant-1"),
        }
        self._handlers: dict = {}

    def on(self, event_name):
        def decorator(func):
            self._handlers[event_name] = func
            return func
        return decorator


class FakeJobProcess:
    def __init__(self):
        # Populate userdata with a placeholder VAD — the real prewarm_fnc
        # fills this slot at worker start. The entrypoint asserts it's
        # present before constructing the AgentSession.
        self.userdata: dict = {"vad": object()}


class FakeContext:
    def __init__(self):
        self.room = FakeRoom()
        self.proc = FakeJobProcess()
        self.log_context_fields: dict = {}

    async def connect(self):
        return None


def _schedule_now_factory():
    """Replace ``asyncio.create_task`` so coroutines run eagerly on the
    current loop and we can deterministically wait for them."""
    tasks: list[asyncio.Task] = []

    def _schedule(coro):
        task = asyncio.get_event_loop().create_task(coro)
        tasks.append(task)
        return task

    return _schedule, tasks


# ---------------------------------------------------------------------------
# type_a — MCPToolset in tools list, OpenAI Realtime as LLM
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_type_a_session_has_mcptoolset_in_tools():
    import agent as agent_module

    fake_toolset = SimpleNamespace(id="frappe_mcp")

    async def _aclose():
        return None

    fake_toolset.aclose = _aclose

    schedule_now, created_tasks = _schedule_now_factory()
    pipeline = {"llm": object(), "stt": object(), "tts": object()}

    with patch("agent.resolve_agent_mode", return_value="type_a"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.build_frappe_mcp_server", return_value=object()), \
         patch("agent.mcp.MCPToolset", return_value=fake_toolset), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        await agent_module.entrypoint(FakeContext())
        await asyncio.gather(*created_tasks)

    session = FakeAgentSession.last_instance
    assert session is not None
    assert len(session.tools) == 1
    assert session.tools[0].id == "frappe_mcp"
    # type_a keeps the pipeline-provided LLM (OpenAI Realtime).
    assert session.llm is pipeline["llm"]
    # type_a does NOT use the mcp_servers parameter.
    assert session.mcp_servers == []


# ---------------------------------------------------------------------------
# type_b — mcp_servers list + MistralAgentLLM, no custom orchestrator
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_type_b_session_uses_mcp_servers_and_mistral_agent_llm(monkeypatch):
    import agent as agent_module

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_branching")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.delenv("MISTRAL_LLM_MODEL", raising=False)

    schedule_now, created_tasks = _schedule_now_factory()
    # Pipeline now returns llm=None for type_b — agent.py owns LLM construction.
    pipeline = {"llm": None, "stt": object(), "tts": object()}
    fake_frappe_server = object()
    fake_llm = MagicMock(name="MistralAgentLLM")

    with patch("agent.resolve_agent_mode", return_value="type_b"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.build_frappe_mcp_server", return_value=fake_frappe_server), \
         patch("agent.MistralAgentLLM", return_value=fake_llm) as llm_ctor, \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        await agent_module.entrypoint(FakeContext())
        await asyncio.gather(*created_tasks)

    session = FakeAgentSession.last_instance
    assert session is not None

    # type_b no longer uses the `tools=[…]` list for MCP.
    assert session.tools == []
    # MCP now arrives via the standard mcp_servers parameter.
    assert session.mcp_servers == [fake_frappe_server]

    # The LLM is the MistralAgentLLM, constructed with agent_id from env.
    assert session.llm is fake_llm
    ctor_kwargs = llm_ctor.call_args.kwargs
    assert ctor_kwargs["agent_id"] == "ag_branching"
    assert ctor_kwargs["api_key"] == "test-key"
    # model should be None because agent_id is the configured routing target.
    assert ctor_kwargs["model"] is None


@pytest.mark.asyncio
async def test_type_b_stateless_mode_uses_model_not_agent_id(monkeypatch):
    import agent as agent_module

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_STATELESS_MODE", "true")
    monkeypatch.setenv("MISTRAL_LLM_MODEL", "ministral-8b-latest")
    monkeypatch.delenv("MISTRAL_AGENT_ID", raising=False)

    schedule_now, created_tasks = _schedule_now_factory()
    pipeline = {"llm": None, "stt": object(), "tts": object()}
    fake_frappe_server = object()
    fake_llm = MagicMock(name="MistralAgentLLM")

    with patch("agent.resolve_agent_mode", return_value="type_b"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.build_frappe_mcp_server", return_value=fake_frappe_server), \
         patch("agent.MistralAgentLLM", return_value=fake_llm) as llm_ctor, \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        await agent_module.entrypoint(FakeContext())
        await asyncio.gather(*created_tasks)

    # In stateless mode agent_id is None and model carries the selection.
    ctor_kwargs = llm_ctor.call_args.kwargs
    assert ctor_kwargs["agent_id"] is None
    assert ctor_kwargs["model"] == "ministral-8b-latest"
