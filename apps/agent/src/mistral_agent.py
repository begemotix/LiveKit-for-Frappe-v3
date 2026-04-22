"""Phase-05 step 1.5 — LiveKit `Agent` subclass that routes all LLM work
through the external `MistralOrchestrator`.

The Mistral SDK owns the RunContext, the MCP tool loop and conversation
state. LiveKit only keeps STT, VAD and TTS; the glue between them is the
`llm_node` override below, which yields plain strings into LiveKit's
`perform_llm_inference` pipeline (verified in Spike 1.0 and D-17).

Architecture notes (Phase-05 D-16, D-17):
- `NullLLM` is the compatibility adapter that opens LiveKit 1.5.5's
  `isinstance(self.llm, llm.LLM)` gate at agent_activity.py:1191. The
  default `Agent.default.llm_node` path — which would call
  `activity.llm.chat(...)` — is bypassed because we override
  `llm_node` fully. If `NullLLM.chat()` is ever reached, that's a bug.
- `AgentSession(tools=[])` is set by the caller (agent.py entrypoint);
  the `tools` kwarg that reaches `llm_node(...)` here is therefore
  always empty. We document the decision (no LiveKit-tools in type_b)
  with an assertion in the node body to keep future regressions loud.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator, TYPE_CHECKING

from livekit.agents import llm as lk_llm
from livekit.agents.types import FlushSentinel
from livekit.agents.voice.agent import Agent, ModelSettings

if TYPE_CHECKING:
    from src.mistral_orchestrator import MistralOrchestrator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NullLLM — compatibility adapter for LiveKit 1.5.5 isinstance() gates
# ---------------------------------------------------------------------------

class NullLLM(lk_llm.LLM):
    """Empty LLM stub that satisfies `isinstance(x, lk_llm.LLM)` so that
    `AgentActivity._pipeline_reply_task` (agent_activity.py:1191) is
    entered and invokes the overridden `llm_node`. `chat()` must never
    be called — if it is, the override is broken."""

    @property
    def model(self) -> str:
        return "null-llm"

    @property
    def provider(self) -> str:
        return "phase-05-compat"

    def chat(self, *_args, **_kwargs):
        raise RuntimeError(
            "NullLLM.chat() was called — MistralDrivenAgent.llm_node must handle "
            "all LLM work. This path should never execute."
        )


# ---------------------------------------------------------------------------
# MistralDrivenAgent — routes llm_node through the orchestrator
# ---------------------------------------------------------------------------

class MistralDrivenAgent(Agent):
    """LiveKit Agent subclass for the type_b voice path.

    Lifecycle: `on_enter` → orchestrator.initialize();
               `on_exit`  → orchestrator.aclose().
    Turn logic: `llm_node` extracts the latest user text from the chat
               context, calls `orchestrator.run_turn(text)`, and yields
               the stream of plain strings into LiveKit's TTS pipeline,
               ending with a `FlushSentinel` so the last sentence is
               flushed without waiting for the next turn.
    """

    def __init__(
        self,
        *,
        orchestrator: "MistralOrchestrator",
        instructions: str,
        correlation_id: str,
    ) -> None:
        super().__init__(instructions=instructions)
        self._orchestrator = orchestrator
        self._correlation_id = correlation_id

    async def on_enter(self) -> None:
        logger.info(
            "mistral_agent_on_enter",
            extra={"correlation_id": self._correlation_id},
        )
        await self._orchestrator.initialize()

    async def on_exit(self) -> None:
        logger.info(
            "mistral_agent_on_exit",
            extra={"correlation_id": self._correlation_id},
        )
        await self._orchestrator.aclose()

    async def llm_node(
        self,
        chat_ctx: lk_llm.ChatContext,
        tools: list,
        model_settings: ModelSettings,
    ) -> AsyncIterator[str | FlushSentinel]:
        # D-16: type_b deliberately passes no LiveKit tools. If any reach
        # here, the wiring in agent.py has regressed and someone re-added
        # an MCPToolset (or similar) into AgentSession(tools=[...]).
        assert not tools, (
            "MistralDrivenAgent.llm_node received LiveKit tools, but type_b "
            "routes all tools through the Mistral RunContext (D-16). "
            f"Offending tools: {[getattr(t, 'id', t) for t in tools]!r}"
        )

        user_text = self._extract_latest_user_text(chat_ctx)
        if not user_text:
            logger.warning(
                "mistral_agent_empty_user_turn",
                extra={"correlation_id": self._correlation_id},
            )
            return

        async for chunk in self._orchestrator.run_turn(user_text):
            yield chunk
        yield FlushSentinel()

    @staticmethod
    def _extract_latest_user_text(chat_ctx: lk_llm.ChatContext) -> str:
        """Scan chat_ctx items in reverse for the most recent user message."""
        for item in reversed(chat_ctx.items):
            if getattr(item, "role", None) == "user":
                text = getattr(item, "text_content", None)
                if isinstance(text, str) and text.strip():
                    return text
        return ""
