"""Phase-05 step 1.4 — MistralOrchestrator tests.

The tests exercise the orchestrator against a **real** `RunContext` from
mistralai 2.4.0 but substitute the MCP client and the Mistral SDK client
with fakes. That way we validate the SDK contracts (include-filter,
tool registration, AsyncExitStack cleanup, event streaming shape) without
needing network, API credentials, or an actual frappe-mcp subprocess.
"""
from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any, AsyncGenerator, List, Optional
from unittest.mock import MagicMock

import pytest

from mistralai.client.models import Function, FunctionTool
from mistralai.client.models.messageoutputevent import MessageOutputEvent
from mistralai.extra.run.result import RunResultEvents


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class FakeMCPClient:
    """Implements enough of MCPClientProtocol for RunContext to accept it."""

    def __init__(self, tool_names: List[str], name: str = "fake-frappe-mcp"):
        self._name = name
        self._tool_names = tool_names
        self.initialize_calls = 0
        self.aclose_calls = 0
        self.exit_stack_seen: Optional[AsyncExitStack] = None

    async def initialize(self, exit_stack: Optional[AsyncExitStack]) -> None:
        self.initialize_calls += 1
        self.exit_stack_seen = exit_stack

    async def aclose(self) -> None:
        self.aclose_calls += 1

    async def get_tools(self) -> List[FunctionTool]:
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

    async def execute_tool(self, name: str, arguments: dict) -> list:  # pragma: no cover
        return [{"type": "text", "text": f"result-of-{name}"}]

    async def get_system_prompt(self, name: str, arguments: dict):  # pragma: no cover
        raise NotImplementedError

    async def list_system_prompts(self):  # pragma: no cover
        raise NotImplementedError


class _FakeStream:
    """Async generator adapter. `events` is consumed in order; if the last
    item is anything besides a RunResultEvents, it is yielded as-is (so
    the orchestrator's RunResult sentinel-break can be exercised)."""

    def __init__(self, events: list):
        self._events = events
        self._recorded_calls: list = []  # populated by caller for assertions

    def __aiter__(self):
        return self._aiter_impl()

    async def _aiter_impl(self):
        for ev in self._events:
            yield ev


class FakeMistralClient:
    """Just enough surface to satisfy `orch._client.beta.conversations.run_stream_async`."""

    def __init__(self, events: list):
        self._events = events
        self.calls: list[dict] = []
        self.beta = MagicMock()
        self.beta.conversations = MagicMock()
        self.beta.conversations.run_stream_async = self._run_stream_async

    def _run_stream_async(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeStream(self._events)


def _msg_event(text: str) -> RunResultEvents:
    return RunResultEvents(
        event="message.output.delta",
        data=MessageOutputEvent(id="evt-1", content=text),
    )


def _mistral_factory_builder(client: FakeMistralClient):
    def _factory(api_key: str):
        # api_key is passed through from the orchestrator; tests don't
        # need to re-assert it here.
        return client
    return _factory


# ---------------------------------------------------------------------------
# Constructor / invariants
# ---------------------------------------------------------------------------

def test_constructor_requires_exactly_one_of_agent_id_or_model():
    from src.mistral_orchestrator import MistralOrchestrator

    with pytest.raises(ValueError, match="exactly one of agent_id"):
        MistralOrchestrator(
            api_key="k", agent_id="ag_1", model="m",
            allowed_tools=None, instructions="", correlation_id="c",
        )

    with pytest.raises(ValueError, match="exactly one of agent_id"):
        MistralOrchestrator(
            api_key="k", agent_id=None, model=None,
            allowed_tools=None, instructions="", correlation_id="c",
        )


def test_constructor_requires_api_key():
    from src.mistral_orchestrator import MistralOrchestrator

    with pytest.raises(ValueError, match="non-empty api_key"):
        MistralOrchestrator(
            api_key="", agent_id="ag_1", model=None,
            allowed_tools=None, instructions="", correlation_id="c",
        )


# ---------------------------------------------------------------------------
# initialize(): tool registration + allowlist filter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_initialize_registers_mcp_client_and_filters_by_allowlist():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=[
        "get_document", "list_documents", "create_document",
        "update_document", "ping", "delete_everything",
    ])
    fake_mistral = FakeMistralClient(events=[])

    orch = MistralOrchestrator(
        api_key="test-key",
        agent_id="ag_test",
        model=None,
        allowed_tools=["get_document", "list_documents", "ping"],
        instructions="ignored in agent mode",
        correlation_id="corr-1",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )

    await orch.initialize()

    # The MCP client is initialized with the RunContext's exit stack.
    assert fake_mcp.initialize_calls == 1
    assert isinstance(fake_mcp.exit_stack_seen, AsyncExitStack)

    # Only allowlisted tools survive the filter.
    assert set(orch.registered_tool_names) == {"get_document", "list_documents", "ping"}
    assert orch.is_initialized is True
    assert orch.is_closed is False

    await orch.aclose()


@pytest.mark.asyncio
async def test_initialize_with_none_allowlist_registers_all_tools():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["a", "b", "c"])
    fake_mistral = FakeMistralClient(events=[])

    orch = MistralOrchestrator(
        api_key="test-key",
        agent_id=None,
        model="mistral-small-latest",
        allowed_tools=None,
        instructions="be concise",
        correlation_id="corr-2",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )

    await orch.initialize()
    assert set(orch.registered_tool_names) == {"a", "b", "c"}
    await orch.aclose()


@pytest.mark.asyncio
async def test_initialize_is_idempotent():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["x"])
    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    await orch.initialize()
    assert fake_mcp.initialize_calls == 1  # second initialize is a no-op
    await orch.aclose()


# ---------------------------------------------------------------------------
# run_turn(): streaming behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_turn_yields_text_chunks_from_message_output_events():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    fake_mistral = FakeMistralClient(events=[
        _msg_event("Hallo"),
        _msg_event(", "),
        _msg_event("ich bin bereit."),
    ])

    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_1", model=None,
        allowed_tools=["ping"], instructions="",
        correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()

    chunks: list[str] = []
    async for c in orch.run_turn("hallo"):
        chunks.append(c)

    assert chunks == ["Hallo", ", ", "ich bin bereit."]

    # Confirm the SDK was called with the right shape.
    assert len(fake_mistral.calls) == 1
    call = fake_mistral.calls[0]
    assert call["inputs"] == "hallo"
    assert call["run_ctx"] is orch._run_ctx  # pylint: disable=protected-access
    # Agent-id mode: instructions must NOT be forwarded (Console owns prompt).
    assert "instructions" not in call

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_forwards_instructions_in_stateless_mode():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    fake_mistral = FakeMistralClient(events=[_msg_event("hi")])

    orch = MistralOrchestrator(
        api_key="test-key", agent_id=None, model="mistral-small-latest",
        allowed_tools=["ping"], instructions="You are terse.",
        correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()
    async for _ in orch.run_turn("say hi"):
        pass

    call = fake_mistral.calls[0]
    assert call["instructions"] == "You are terse."

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_ignores_non_message_events():
    """function.call.delta / tool.execution.* / conversation.* arrive in the
    same stream but must not reach LiveKit TTS."""
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    unrelated = RunResultEvents(
        event="tool.execution.started",
        # We mock the data with a plain object so the orchestrator's
        # isinstance(data, MessageOutputEvent) check returns False.
        # RunResultEvents accepts any annotated union member; here we use
        # MessageOutputEvent with an out-of-band type to keep pydantic happy,
        # then rely on the orchestrator's filter.
        data=MessageOutputEvent(id="evt-bogus", content=""),
    )
    fake_mistral = FakeMistralClient(events=[
        _msg_event("hello"),
        # An event whose `.data` is missing or unrelated:
        type("FakeEv", (), {"data": object()})(),
        _msg_event(" world"),
    ])

    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()

    out = [c async for c in orch.run_turn("input")]
    assert out == ["hello", " world"]

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_before_initialize_raises():
    from src.mistral_orchestrator import MistralOrchestrator

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: FakeMCPClient([]),
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    with pytest.raises(RuntimeError, match="before initialize"):
        async for _ in orch.run_turn("x"):
            pass


@pytest.mark.asyncio
async def test_run_turn_after_aclose_raises():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=[])
    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    await orch.aclose()
    with pytest.raises(RuntimeError, match="after aclose"):
        async for _ in orch.run_turn("x"):
            pass


# ---------------------------------------------------------------------------
# aclose(): lifecycle + MCP cleanup
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_aclose_closes_mcp_client_via_run_context():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["x"])
    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    assert fake_mcp.aclose_calls == 0

    await orch.aclose()
    # RunContext.__aexit__ calls aclose() on every registered MCP client.
    assert fake_mcp.aclose_calls == 1
    assert orch.is_closed is True


@pytest.mark.asyncio
async def test_aclose_is_idempotent():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["x"])
    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    await orch.aclose()
    await orch.aclose()  # second call must not raise / must not double-close
    assert fake_mcp.aclose_calls == 1


@pytest.mark.asyncio
async def test_initialize_after_aclose_raises():
    from src.mistral_orchestrator import MistralOrchestrator

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda: FakeMCPClient([]),
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    await orch.aclose()
    with pytest.raises(RuntimeError, match="closed MistralOrchestrator"):
        await orch.initialize()
