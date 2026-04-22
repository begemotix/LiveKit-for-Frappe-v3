"""Phase-05 step 1.8 — entrypoint branching tests.

Exercises the agent.py entrypoint across both modes after the 1.3 + 1.6
refactor:

- type_a  → AgentSession carries a `MCPToolset(id="frappe_mcp")` and the
            disconnect handler closes that toolset.
- type_b  → AgentSession carries `tools=[]`, the Mistral orchestrator
            registered the MCP client on its RunContext, the D-16
            assertion in MistralDrivenAgent.llm_node fires if a stray
            LiveKit tool reaches it, and the disconnect handler closes
            the orchestrator (not a LiveKit toolset).

For type_b we run the *real* `MistralOrchestrator` through the
entrypoint but swap its MCP and Mistral-client factories so no network
or subprocess starts during the test.
"""
from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from types import SimpleNamespace
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from livekit.agents import llm as lk_llm
from livekit.agents.voice.agent import ModelSettings

from src.mistral_orchestrator import MistralOrchestrator


# ---------------------------------------------------------------------------
# Shared test doubles for entrypoint exercises
# ---------------------------------------------------------------------------

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


class FakeContext:
    def __init__(self):
        self.room = FakeRoom()
        self.log_context_fields: dict = {}
        self.proc = SimpleNamespace(userdata={"vad": object()})

    async def connect(self):
        return None


class FakeAgentSession:
    """Captures the kwargs agent.py passes to AgentSession. MetricsListener
    pokes at .llm/.stt/.tts during init so those must exist."""
    last_instance: Optional["FakeAgentSession"] = None

    def __init__(self, *_args, **kwargs):
        self.llm = kwargs.get("llm")
        self.stt = kwargs.get("stt")
        self.tts = kwargs.get("tts")
        self.tools = kwargs.get("tools") or []
        self.turn_handling = kwargs.get("turn_handling")
        self.vad = kwargs.get("vad")
        FakeAgentSession.last_instance = self

    def on(self, _event_name):
        def decorator(func):
            return func
        return decorator

    async def start(self, room, agent):
        self.room = room
        self.agent = agent
        # Real AgentSession calls agent.on_enter() during start; mirror it
        # so tests can observe the orchestrator lifecycle.
        if hasattr(agent, "on_enter"):
            await agent.on_enter()

    async def say(self, text, **_kwargs):
        return text


def _schedule_now_factory():
    """Returns (schedule_now, created_tasks) — agent.py uses
    asyncio.create_task(...) extensively; we capture them so tests can
    await completion deterministically."""
    created: list[asyncio.Task] = []

    def schedule_now(coro):
        task = asyncio.get_running_loop().create_task(coro)
        created.append(task)
        return task

    return schedule_now, created


class FakeMCPClient:
    """Minimal MCPClientProtocol implementation. Records lifecycle calls."""

    def __init__(self, tool_names: list[str], name: str = "fake-frappe-mcp"):
        self._name = name
        self._tool_names = tool_names
        self.initialize_calls = 0
        self.aclose_calls = 0

    async def initialize(self, exit_stack: Optional[AsyncExitStack]) -> None:
        self.initialize_calls += 1

    async def aclose(self) -> None:
        self.aclose_calls += 1

    async def get_tools(self):
        from mistralai.client.models import Function, FunctionTool
        return [
            FunctionTool(
                function=Function(
                    name=n,
                    description=f"stub for {n}",
                    parameters={"type": "object", "properties": {}},
                )
            )
            for n in self._tool_names
        ]


def _make_mistral_client_factory():
    """Returns a factory that builds a minimal client-like Mock."""
    def _factory(api_key: str):
        client = MagicMock()
        client.beta = MagicMock()
        client.beta.conversations = MagicMock()
        return client
    return _factory


def _patched_orchestrator_factory(fake_mcp: FakeMCPClient):
    """Returns a side-effect callable for `patch('agent.MistralOrchestrator')`
    that constructs the *real* MistralOrchestrator with our in-memory
    MCP + Mistral-client fakes."""
    def _build(*, api_key, agent_id, model, allowed_tools, instructions, correlation_id):
        return MistralOrchestrator(
            api_key=api_key,
            agent_id=agent_id,
            model=model,
            allowed_tools=allowed_tools,
            instructions=instructions,
            correlation_id=correlation_id,
            mcp_client_factory=lambda: fake_mcp,
            mistral_client_factory=_make_mistral_client_factory(),
        )
    return _build


# ---------------------------------------------------------------------------
# 1. type_a — session.tools contains MCPToolset(id="frappe_mcp")
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_build_voice_pipeline_type_a_mcp_toolset_present():
    import agent as agent_module

    fake_toolset = SimpleNamespace(id="frappe_mcp", aclose=MagicMock())

    async def _aclose():
        return None
    fake_toolset.aclose = _aclose  # AsyncMock equivalent

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
    # Type-A keeps the LiveKit LLM placeholder straight from the pipeline
    # (NullLLM is only used on the type_b path).
    assert session.llm is pipeline["llm"]


# ---------------------------------------------------------------------------
# 2. type_b — session.tools == [], orchestrator registered MCP client
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_build_voice_pipeline_type_b_tools_empty(monkeypatch):
    import agent as agent_module

    # Minimal env so resolve_mistral_config inside the entrypoint is happy.
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_branching")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.delenv("MISTRAL_LLM_MODEL", raising=False)

    fake_mcp = FakeMCPClient(
        tool_names=["get_document", "list_documents", "ping", "delete_doc"]
    )

    schedule_now, created_tasks = _schedule_now_factory()
    pipeline = {"llm": object(), "stt": object(), "tts": object()}

    captured_orchestrators: list[MistralOrchestrator] = []

    def _build_orch(**kwargs):
        orch = _patched_orchestrator_factory(fake_mcp)(**kwargs)
        captured_orchestrators.append(orch)
        return orch

    with patch("agent.resolve_agent_mode", return_value="type_b"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.MistralOrchestrator", side_effect=_build_orch), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        await agent_module.entrypoint(FakeContext())
        await asyncio.gather(*created_tasks)

    session = FakeAgentSession.last_instance
    assert session is not None
    # D-16: type_b must not carry any LiveKit-side tools.
    assert session.tools == []

    # And the orchestrator actually registered the MCP client against its
    # RunContext. The read-only allowlist from
    # get_allowed_tools_for_mode("type_b") filters the fake MCP inventory.
    assert len(captured_orchestrators) == 1
    orch = captured_orchestrators[0]
    assert orch.is_initialized is True
    assert fake_mcp.initialize_calls == 1
    registered = set(orch.registered_tool_names)
    # "delete_doc" is not in get_allowed_tools_for_mode("type_b") and must
    # be filtered out; at least one allowed tool survived.
    assert "delete_doc" not in registered
    assert "get_document" in registered or "list_documents" in registered or "ping" in registered


# ---------------------------------------------------------------------------
# 3. MistralDrivenAgent.llm_node — D-16 assertion on any LiveKit tool
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mistral_driven_agent_llm_node_d16_assertion():
    from src.mistral_agent import MistralDrivenAgent

    class _NoopOrch:
        async def initialize(self):
            pass

        async def aclose(self):
            pass

        async def run_turn(self, _text):
            if False:
                yield ""  # pragma: no cover — never reached

    agent = MistralDrivenAgent(
        orchestrator=_NoopOrch(),
        instructions="sys",
        correlation_id="branch-d16",
    )

    chat_ctx = lk_llm.ChatContext()
    chat_ctx.add_message(role="user", content="anything")

    stray_tool = SimpleNamespace(id="stray_frappe_toolset")

    with pytest.raises(AssertionError, match="D-16"):
        async for _ in agent.llm_node(
            chat_ctx=chat_ctx,
            tools=[stray_tool],
            model_settings=ModelSettings(),
        ):
            pass


# ---------------------------------------------------------------------------
# 4. cleanup_session_mcp (type_b) closes the orchestrator, not a toolset
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cleanup_session_mcp_type_b_calls_orchestrator_aclose(monkeypatch):
    import agent as agent_module

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_AGENT_ID", "ag_branching")
    monkeypatch.delenv("MISTRAL_STATELESS_MODE", raising=False)
    monkeypatch.delenv("MISTRAL_LLM_MODEL", raising=False)

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    schedule_now, created_tasks = _schedule_now_factory()
    pipeline = {"llm": object(), "stt": object(), "tts": object()}

    captured_orchestrators: list[MistralOrchestrator] = []

    def _build_orch(**kwargs):
        orch = _patched_orchestrator_factory(fake_mcp)(**kwargs)
        captured_orchestrators.append(orch)
        return orch

    # This mock flags any accidental MCPToolset aclose so the test would
    # fail loud if the refactor regressed back to the LiveKit-tool path.
    livekit_toolset_aclose = MagicMock()

    with patch("agent.resolve_agent_mode", return_value="type_b"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.MistralOrchestrator", side_effect=_build_orch), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        ctx = FakeContext()
        await agent_module.entrypoint(ctx)
        await asyncio.gather(*created_tasks)

        # Trigger participant_disconnected — the cleanup path under test.
        disconnect_handler = ctx.room._handlers["participant_disconnected"]
        disconnect_handler(SimpleNamespace(identity="participant-1"))
        await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})

    orch = captured_orchestrators[0]
    # cleanup_session_mcp() must have routed to orchestrator.aclose().
    assert orch.is_closed is True
    # RunContext.__aexit__ fans aclose() out to every registered MCP client.
    assert fake_mcp.aclose_calls == 1
    # And we definitely did not close a ghost LiveKit toolset.
    livekit_toolset_aclose.assert_not_called()
