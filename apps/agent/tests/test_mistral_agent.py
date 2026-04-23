"""Phase-05 step 1.5 — MistralDrivenAgent + NullLLM tests.

Covers:
- NullLLM satisfies LiveKit's isinstance(self.llm, lk_llm.LLM) gate and
  raises loudly if `chat()` is ever invoked.
- MistralDrivenAgent.on_enter / on_exit delegate to the orchestrator's
  initialize / aclose lifecycle hooks.
- MistralDrivenAgent.llm_node yields plain text chunks followed by a
  FlushSentinel, ignoring LiveKit-side tools (D-16 regression guard).
- llm_node extracts the most recent user message from ChatContext and
  drops empty turns silently.
"""
from __future__ import annotations

from typing import AsyncIterator
from unittest.mock import MagicMock

import pytest

from livekit.agents import llm as lk_llm
from livekit.agents.types import FlushSentinel
from livekit.agents.voice.agent import ModelSettings


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class FakeOrchestrator:
    """Records lifecycle calls and replays a canned stream from `run_turn`."""

    def __init__(self, chunks: list[str] | None = None):
        self._chunks = list(chunks) if chunks else []
        self.initialize_calls = 0
        self.aclose_calls = 0
        self.run_turn_calls: list[str] = []
        self.tool_started_callback = None

    def set_tool_started_callback(self, callback) -> None:
        self.tool_started_callback = callback

    async def initialize(self) -> None:
        self.initialize_calls += 1

    async def aclose(self) -> None:
        self.aclose_calls += 1

    async def run_turn(self, user_text: str) -> AsyncIterator[str]:
        self.run_turn_calls.append(user_text)
        for c in self._chunks:
            yield c


def _chat_ctx_with_user(text: str) -> lk_llm.ChatContext:
    ctx = lk_llm.ChatContext()
    ctx.add_message(role="user", content=text)
    return ctx


def _chat_ctx_with_turns(*turns: tuple[str, str]) -> lk_llm.ChatContext:
    ctx = lk_llm.ChatContext()
    for role, text in turns:
        ctx.add_message(role=role, content=text)
    return ctx


# ---------------------------------------------------------------------------
# NullLLM
# ---------------------------------------------------------------------------

def test_null_llm_is_lk_llm_instance_for_pipeline_gate():
    from src.mistral_agent import NullLLM

    llm = NullLLM()
    # This is the exact check at agent_activity.py:1191 in livekit-agents 1.5.5.
    assert isinstance(llm, lk_llm.LLM) is True


def test_null_llm_exposes_model_and_provider_identifiers():
    from src.mistral_agent import NullLLM

    llm = NullLLM()
    assert llm.model == "null-llm"
    assert llm.provider == "phase-05-compat"


def test_null_llm_chat_raises_with_clear_message():
    from src.mistral_agent import NullLLM

    llm = NullLLM()
    with pytest.raises(RuntimeError, match="NullLLM.chat\\(\\) was called"):
        llm.chat(chat_ctx=lk_llm.ChatContext(), tools=[])


# ---------------------------------------------------------------------------
# MistralDrivenAgent — lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_on_enter_returns_immediately_and_initializes_in_background():
    """Phase-N change: on_enter must return immediately so the
    greeting fires without waiting for the MCP-subprocess spawn /
    Mistral handshake. Initialize then runs in a background asyncio
    task whose handle is exposed as agent._init_task for testing."""
    import asyncio
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator()
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-1"
    )

    # The await on on_enter() itself returns ~instantly because the
    # heavy init was scheduled as a Task. Yield control to the loop
    # once so the background task gets to run for the assertion.
    await agent.on_enter()
    assert agent._init_task is not None  # background task scheduled
    await agent._init_task             # let it finish for the assertion

    assert orch.initialize_calls == 1
    assert orch.aclose_calls == 0
    # Tool-started callback was wired during on_enter (before init).
    assert orch.tool_started_callback is not None


@pytest.mark.asyncio
async def test_speak_filler_uses_session_say_with_default_text_and_interruptions_allowed():
    """When the orchestrator signals tool execution start, the agent
    must call session.say() with the configured filler text and
    allow_interruptions=True (so the user can still cut in)."""
    from src.mistral_agent import DEFAULT_FILLER_TEXT, MistralDrivenAgent

    orch = FakeOrchestrator()
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-filler"
    )

    # Inject a fake session that records say() calls.
    say_calls: list[dict] = []

    class _FakeSession:
        def say(self, text, *, allow_interruptions=False, add_to_chat_ctx=True):
            say_calls.append({
                "text": text,
                "allow_interruptions": allow_interruptions,
                "add_to_chat_ctx": add_to_chat_ctx,
            })

    # The Agent base class exposes session via @property; we patch the
    # underlying private attribute to avoid spinning up a real session.
    agent._activity = type("X", (), {"session": _FakeSession()})()

    agent._speak_filler("get_document")

    assert len(say_calls) == 1
    assert say_calls[0]["text"] == DEFAULT_FILLER_TEXT
    assert say_calls[0]["allow_interruptions"] is True
    assert say_calls[0]["add_to_chat_ctx"] is False


@pytest.mark.asyncio
async def test_speak_filler_skips_safely_when_session_unavailable(caplog):
    """If the filler callback fires before the session is wired up
    (race during init), the call must log a warning and return
    cleanly — never raise into the orchestrator's stream loop."""
    import logging
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator()
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-no-session"
    )

    with caplog.at_level(logging.WARNING, logger="src.mistral_agent"):
        # Should not raise even without a session bound.
        agent._speak_filler("get_document")

    assert any(
        rec.message == "mistral_agent_filler_skipped_no_session"
        for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_filler_text_is_configurable_via_constructor():
    """Operators may override the filler text per deployment."""
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator()
    agent = MistralDrivenAgent(
        orchestrator=orch,
        instructions="sys",
        correlation_id="c-cfg",
        filler_text="Moment, ich prüfe das.",
    )
    say_calls: list[str] = []

    class _FakeSession:
        def say(self, text, **_kwargs):
            say_calls.append(text)

    agent._activity = type("X", (), {"session": _FakeSession()})()
    agent._speak_filler("anytool")

    assert say_calls == ["Moment, ich prüfe das."]


@pytest.mark.asyncio
async def test_on_exit_calls_orchestrator_aclose():
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator()
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-2"
    )

    await agent.on_exit()
    assert orch.aclose_calls == 1


# ---------------------------------------------------------------------------
# MistralDrivenAgent — llm_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_node_yields_orchestrator_chunks_then_flush_sentinel():
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator(chunks=["Hallo", ", ", "ich helfe."])
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-3"
    )

    chat_ctx = _chat_ctx_with_user("kannst du mir helfen?")
    out: list = []
    async for piece in agent.llm_node(
        chat_ctx=chat_ctx, tools=[], model_settings=ModelSettings()
    ):
        out.append(piece)

    # Strings first, FlushSentinel last.
    assert out[:-1] == ["Hallo", ", ", "ich helfe."]
    assert isinstance(out[-1], FlushSentinel)
    assert orch.run_turn_calls == ["kannst du mir helfen?"]


@pytest.mark.asyncio
async def test_llm_node_extracts_latest_user_message_from_mixed_turns():
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator(chunks=["ok"])
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-4"
    )

    chat_ctx = _chat_ctx_with_turns(
        ("user", "alte frage"),
        ("assistant", "alte antwort"),
        ("user", "neue frage"),
    )
    async for _ in agent.llm_node(
        chat_ctx=chat_ctx, tools=[], model_settings=ModelSettings()
    ):
        pass

    assert orch.run_turn_calls == ["neue frage"]


@pytest.mark.asyncio
async def test_llm_node_skips_turn_when_no_user_message(caplog):
    import logging
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator(chunks=["should-not-stream"])
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-5"
    )

    chat_ctx = lk_llm.ChatContext()  # empty
    with caplog.at_level(logging.WARNING, logger="src.mistral_agent"):
        out: list = []
        async for piece in agent.llm_node(
            chat_ctx=chat_ctx, tools=[], model_settings=ModelSettings()
        ):
            out.append(piece)

    assert out == []
    assert orch.run_turn_calls == []
    assert any(
        rec.message == "mistral_agent_empty_user_turn" for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_llm_node_rejects_livekit_tools_d16_regression_guard():
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator(chunks=["won't matter"])
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-6"
    )

    fake_tool = MagicMock()
    fake_tool.id = "frappe_toolset"

    chat_ctx = _chat_ctx_with_user("anything")
    with pytest.raises(AssertionError, match="D-16"):
        async for _ in agent.llm_node(
            chat_ctx=chat_ctx, tools=[fake_tool], model_settings=ModelSettings()
        ):
            pass

    assert orch.run_turn_calls == []


@pytest.mark.asyncio
async def test_llm_node_flush_sentinel_fires_even_when_run_turn_yields_nothing():
    """If Mistral produces zero text chunks (e.g. pure tool-only turn that
    ends without a message), we still want the FlushSentinel so LiveKit
    doesn't wait for more."""
    from src.mistral_agent import MistralDrivenAgent

    orch = FakeOrchestrator(chunks=[])  # no chunks
    agent = MistralDrivenAgent(
        orchestrator=orch, instructions="sys", correlation_id="c-7"
    )

    chat_ctx = _chat_ctx_with_user("irrelevant")
    out: list = []
    async for piece in agent.llm_node(
        chat_ctx=chat_ctx, tools=[], model_settings=ModelSettings()
    ):
        out.append(piece)

    assert len(out) == 1
    assert isinstance(out[0], FlushSentinel)
    assert orch.run_turn_calls == ["irrelevant"]


# ---------------------------------------------------------------------------
# Round-trip: AgentSession(llm=NullLLM()) opens the pipeline gate
# (static compile-time check — runtime verification done in Spike 1.0)
# ---------------------------------------------------------------------------

def test_agent_session_accepts_null_llm_without_runtime_error():
    """End-to-end sanity: the AgentSession constructor accepts a NullLLM
    instance and exposes it via .llm, satisfying the isinstance() gate
    that _pipeline_reply_task relies on."""
    from livekit.agents import AgentSession
    from src.mistral_agent import NullLLM

    session = AgentSession(llm=NullLLM())

    assert isinstance(session.llm, lk_llm.LLM)
    # And our specific subclass identity is preserved.
    assert type(session.llm).__name__ == "NullLLM"
