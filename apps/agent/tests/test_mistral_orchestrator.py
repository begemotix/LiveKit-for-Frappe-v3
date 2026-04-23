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
from mistralai.client.models.responseerrorevent import ResponseErrorEvent
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
    """Mirrors the real SDK contract: `run_stream_async` is declared
    `async def ... -> AsyncGenerator[...]`, so calling it returns a
    coroutine that must be awaited before iteration. Emulating this
    shape is what actually guards the orchestrator against the
    production `TypeError: async for requires an object with __aiter__`
    regression."""

    def __init__(self, events: list):
        self._events = events
        self.calls: list[dict] = []
        self.beta = MagicMock()
        self.beta.conversations = MagicMock()
        self.beta.conversations.run_stream_async = self._run_stream_async

    async def _run_stream_async(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeStream(self._events)


def _msg_event(text: str) -> RunResultEvents:
    return RunResultEvents(
        event="message.output.delta",
        data=MessageOutputEvent(id="evt-1", content=text),
    )


def _error_event(message: str = "bad request", code: int = 400) -> RunResultEvents:
    return RunResultEvents(
        event="conversation.response.error",
        data=ResponseErrorEvent(message=message, code=code),
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
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()

    out = [c async for c in orch.run_turn("input")]
    assert out == ["hello", " world"]

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_logs_response_error_event_and_yields_fallback(caplog):
    """A ResponseErrorEvent in the stream must (a) log at ERROR with
    message/code/correlation_id, (b) not be silently discarded, and
    (c) still result in a user-audible fallback reply."""
    import logging
    from src.mistral_orchestrator import MistralOrchestrator, _FALLBACK_REPLY

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    fake_mistral = FakeMistralClient(events=[
        _error_event(message="invalid agent_id", code=404),
    ])

    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_wrong", model=None,
        allowed_tools=None, instructions="", correlation_id="corr-err",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()

    chunks: list[str] = []
    with caplog.at_level(logging.ERROR, logger="src.mistral_orchestrator"):
        async for c in orch.run_turn("hallo"):
            chunks.append(c)

    # Fallback-reply was spoken so the user never faces a mute agent.
    assert chunks == [_FALLBACK_REPLY]

    # Error was logged at ERROR with structured fields.
    error_records = [
        rec for rec in caplog.records
        if rec.message == "mistral_stream_response_error"
    ]
    assert error_records, "Expected mistral_stream_response_error ERROR log"
    rec = error_records[0]
    assert rec.levelno == logging.ERROR
    assert rec.correlation_id == "corr-err"
    assert rec.agent_id == "ag_wrong"
    assert rec.error_message == "invalid agent_id"
    assert rec.error_code == 404

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_yields_fallback_on_empty_stream(caplog):
    """Stream that emits zero events at all (pure silence from Mistral)
    must still yield the fallback so TTS has text to speak."""
    import logging
    from src.mistral_orchestrator import MistralOrchestrator, _FALLBACK_REPLY

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    fake_mistral = FakeMistralClient(events=[])  # truly empty

    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_1", model=None,
        allowed_tools=None, instructions="", correlation_id="corr-empty",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()

    chunks: list[str] = []
    with caplog.at_level(logging.WARNING, logger="src.mistral_orchestrator"):
        async for c in orch.run_turn("hallo"):
            chunks.append(c)

    assert chunks == [_FALLBACK_REPLY]
    assert any(
        rec.message == "mistral_run_turn_empty_stream_fallback"
        for rec in caplog.records
    )

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_awaits_coroutine_returned_by_run_stream_async():
    """Regression: mistralai's run_stream_async is `async def`, decorated
    with the sync `run_requirements` wrapper, so calling it returns a
    coroutine. Iterating that coroutine directly (pre-fix behaviour)
    raises `TypeError: async for requires __aiter__`. This test hardens
    the fix: the orchestrator must `await` the returned coroutine first,
    then iterate the resulting async generator."""
    import inspect
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    fake_mistral = FakeMistralClient(events=[_msg_event("pong")])

    # Sanity-check the fake mirrors the real SDK shape: the method must
    # be a coroutine function (calling it returns a coroutine).
    assert inspect.iscoroutinefunction(
        fake_mistral.beta.conversations.run_stream_async
    ), "Fake must mimic real SDK: run_stream_async is async def"

    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_1", model=None,
        allowed_tools=None, instructions="",
        correlation_id="corr-coro",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
    )
    await orch.initialize()

    # Must not raise `TypeError: async for requires an object with __aiter__`.
    chunks = [c async for c in orch.run_turn("hallo")]
    assert chunks == ["pong"]

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_before_initialize_yields_fallback_after_timeout():
    """Phase-N change: run_turn() no longer raises immediately when
    called before initialize() — it briefly waits for the background
    init Event and, on timeout, yields the fallback reply so the user
    hears something instead of facing a crash."""
    from src.mistral_orchestrator import MistralOrchestrator, _FALLBACK_REPLY

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda **_:FakeMCPClient([]),
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
        init_wait_timeout_s=0.1,  # short timeout for tests
    )
    chunks = [c async for c in orch.run_turn("x")]
    assert chunks == [_FALLBACK_REPLY]


@pytest.mark.asyncio
async def test_run_turn_waits_for_background_init_then_proceeds():
    """If initialize() is running in parallel and finishes within
    timeout, run_turn() should pick up cleanly without yielding the
    fallback."""
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    fake_mistral = FakeMistralClient(events=[_msg_event("hallo")])

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag_1", model=None,
        allowed_tools=None, instructions="",
        correlation_id="c-init-race",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(fake_mistral),
        init_wait_timeout_s=2.0,
    )

    # Schedule initialize() with a tiny delay; run_turn() will start
    # before it completes and should wait on the init_complete event.
    async def delayed_init():
        await asyncio.sleep(0.05)
        await orch.initialize()

    init_task = asyncio.create_task(delayed_init())
    try:
        chunks = [c async for c in orch.run_turn("hi")]
    finally:
        await init_task

    assert chunks == ["hallo"]
    assert orch.is_initialized is True
    await orch.aclose()


@pytest.mark.asyncio
async def test_initialize_passes_filler_callback_to_mcp_factory():
    """Wiring contract: the orchestrator hands its internal
    _fire_filler_if_needed to the MCP client factory as
    `on_tool_execute`. This is the only way the FillerAwareMCPClient
    knows whom to notify when a tool dispatches — and the sole
    mechanism by which the filler fires in type_b now."""
    from src.mistral_orchestrator import MistralOrchestrator

    captured_kwargs: list[dict] = []

    def _recording_factory(**kwargs):
        captured_kwargs.append(kwargs)
        return FakeMCPClient(tool_names=["get_document"])

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="",
        correlation_id="c-wiring",
        mcp_client_factory=_recording_factory,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()

    assert len(captured_kwargs) == 1
    cb = captured_kwargs[0].get("on_tool_execute")
    assert callable(cb)
    # Calling the captured callback must route into the orchestrator's
    # tool-started callback (the one MistralDrivenAgent registers).
    received: list[str] = []
    orch.set_tool_started_callback(lambda name: received.append(name))
    cb("list_documents")
    assert received == ["list_documents"]

    await orch.aclose()


@pytest.mark.asyncio
async def test_fire_filler_is_debounced_per_turn_and_resets_next_turn():
    """MCP dispatches multiple tools in one turn → only one filler.
    New turn → filler gate resets so the next tool call can fire it
    again. Validates both idempotence and per-turn reset."""
    from src.mistral_orchestrator import MistralOrchestrator

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="",
        correlation_id="c-debounce",
        mcp_client_factory=lambda **_: FakeMCPClient(tool_names=["a", "b"]),
        mistral_client_factory=_mistral_factory_builder(
            FakeMistralClient(events=[_msg_event("ok")])
        ),
    )
    received: list[str] = []
    orch.set_tool_started_callback(lambda name: received.append(name))
    await orch.initialize()

    # Simulate three back-to-back MCP dispatches within one turn.
    # (In production this would be the FillerAwareMCPClient calling
    # _fire_filler_if_needed on every execute_tool().)
    async for _ in orch.run_turn("first turn"):
        orch._fire_filler_if_needed("a")  # pylint: disable=protected-access
        orch._fire_filler_if_needed("b")  # pylint: disable=protected-access
        orch._fire_filler_if_needed("a")  # pylint: disable=protected-access

    assert received == ["a"], "only the FIRST tool of the turn fires the filler"

    # Second turn: gate must reset so the first tool can fire again.
    async for _ in orch.run_turn("second turn"):
        orch._fire_filler_if_needed("b")  # pylint: disable=protected-access

    assert received == ["a", "b"]

    await orch.aclose()


@pytest.mark.asyncio
async def test_fire_filler_is_noop_when_no_callback_registered():
    """If no filler callback is registered (e.g. direct orchestrator
    use in a test), _fire_filler_if_needed must silently no-op — not
    raise. Otherwise a single forgotten set_tool_started_callback()
    would crash every tool dispatch in production."""
    from src.mistral_orchestrator import MistralOrchestrator

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="",
        correlation_id="c-no-cb",
        mcp_client_factory=lambda **_: FakeMCPClient(tool_names=["x"]),
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()

    # No set_tool_started_callback() call — must not raise.
    orch._fire_filler_if_needed("x")  # pylint: disable=protected-access

    await orch.aclose()


@pytest.mark.asyncio
async def test_fire_filler_swallows_callback_exception(caplog):
    """Filler is best-effort — a crashing callback must not break the
    tool dispatch (which would abort the whole turn). Exception gets
    logged at ERROR for diagnosis, filler gate still flips so the bad
    callback isn't called twice per turn."""
    import logging
    from src.mistral_orchestrator import MistralOrchestrator

    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="",
        correlation_id="c-broken-cb",
        mcp_client_factory=lambda **_: FakeMCPClient(tool_names=["x"]),
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )

    def _broken(_name):
        raise RuntimeError("callback exploded on purpose")

    orch.set_tool_started_callback(_broken)
    await orch.initialize()

    with caplog.at_level(logging.ERROR, logger="src.mistral_orchestrator"):
        # Must not raise.
        orch._fire_filler_if_needed("x")  # pylint: disable=protected-access

    assert any(
        rec.message == "mistral_tool_started_callback_failed"
        for rec in caplog.records
    )
    # Gate still flipped so the bad callback isn't retried this turn.
    assert orch._filler_fired_this_turn is True  # pylint: disable=protected-access

    await orch.aclose()


@pytest.mark.asyncio
async def test_run_turn_after_aclose_raises():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=[])
    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    assert fake_mcp.aclose_calls == 0

    await orch.aclose()
    # RunContext.__aexit__ calls aclose() on every registered MCP client.
    assert fake_mcp.aclose_calls == 1
    assert orch.is_closed is True


@pytest.mark.asyncio
async def test_aclose_swallows_anyio_cross_task_runtime_error(caplog):
    """Regression: on LiveKit session teardown, on_enter and on_exit run
    in different asyncio tasks in some paths; the anyio TaskGroup that
    MCPClientSTDIO opened via stdio_client() refuses a cross-task exit
    with:
      RuntimeError: Attempted to exit cancel scope in a different task
      than it was entered in
    The orchestrator must log WARNING and continue — the stdio
    subprocess is reaped by the OS on agent shutdown, so functional
    impact is zero, and crashing here would pollute prod logs and
    potentially disturb the agent's shutdown path."""
    import logging
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_1", model=None,
        allowed_tools=None, instructions="",
        correlation_id="corr-cross-task",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()

    # Swap RunContext.__aexit__ with one that raises the exact anyio
    # cross-task error we see in production.
    async def raising_aexit(*_args, **_kwargs):
        raise RuntimeError(
            "Attempted to exit cancel scope in a different task than "
            "it was entered in"
        )

    orch._run_ctx.__aexit__ = raising_aexit  # type: ignore[assignment]

    with caplog.at_level(logging.WARNING, logger="src.mistral_orchestrator"):
        # Must not raise.
        await orch.aclose()

    assert orch.is_closed is True
    suppressed = [
        rec for rec in caplog.records
        if rec.message == "mistral_orchestrator_cross_task_close_suppressed"
    ]
    assert suppressed, "Expected suppressed-log for cross-task aclose"
    assert "different task" in suppressed[0].detail


@pytest.mark.asyncio
async def test_aclose_swallows_anyio_cross_task_error_wrapped_in_exception_group(caplog):
    """AnyIO sometimes wraps the cross-task RuntimeError in an
    ExceptionGroup when the task group unwinds. The suppression must
    cover that shape too."""
    import logging
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_1", model=None,
        allowed_tools=None, instructions="",
        correlation_id="corr-cross-task-group",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()

    async def raising_aexit(*_args, **_kwargs):
        raise BaseExceptionGroup(
            "unhandled errors in a TaskGroup",
            [
                RuntimeError(
                    "Attempted to exit cancel scope in a different "
                    "task than it was entered in"
                )
            ],
        )

    orch._run_ctx.__aexit__ = raising_aexit  # type: ignore[assignment]

    with caplog.at_level(logging.WARNING, logger="src.mistral_orchestrator"):
        await orch.aclose()

    assert orch.is_closed is True
    assert any(
        rec.message == "mistral_orchestrator_cross_task_close_suppressed"
        for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_aclose_reraises_unrelated_runtime_error():
    """Don't mask bugs: unrelated RuntimeErrors during close must surface."""
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["ping"])
    orch = MistralOrchestrator(
        api_key="test-key", agent_id="ag_1", model=None,
        allowed_tools=None, instructions="",
        correlation_id="corr-unrelated-err",
        mcp_client_factory=lambda **_:fake_mcp,
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()

    async def raising_aexit(*_args, **_kwargs):
        raise RuntimeError("something else entirely went wrong")

    orch._run_ctx.__aexit__ = raising_aexit  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="something else entirely"):
        await orch.aclose()


@pytest.mark.asyncio
async def test_aclose_is_idempotent():
    from src.mistral_orchestrator import MistralOrchestrator

    fake_mcp = FakeMCPClient(tool_names=["x"])
    orch = MistralOrchestrator(
        api_key="k", agent_id="ag", model=None,
        allowed_tools=None, instructions="", correlation_id="c",
        mcp_client_factory=lambda **_:fake_mcp,
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
        mcp_client_factory=lambda **_:FakeMCPClient([]),
        mistral_client_factory=_mistral_factory_builder(FakeMistralClient([])),
    )
    await orch.initialize()
    await orch.aclose()
    with pytest.raises(RuntimeError, match="closed MistralOrchestrator"):
        await orch.initialize()
