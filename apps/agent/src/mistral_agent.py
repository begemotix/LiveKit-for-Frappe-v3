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

import asyncio
import logging
import random
from typing import AsyncIterator, Optional, TYPE_CHECKING

from livekit.agents import llm as lk_llm
from livekit.agents.types import FlushSentinel
from livekit.agents.voice.agent import Agent, ModelSettings

if TYPE_CHECKING:
    from src.mistral_orchestrator import MistralOrchestrator

logger = logging.getLogger(__name__)

# Humanisierung Tier 1: Filler-Pool statt Einzelphrase.
# Ein fester Satz pro Tool-Call klingt nach ~3 Aufrufen roboterhaft
# ("Papagei-Effekt"). Mit einer Rotation von natürlichen Varianten
# wirkt der Agent lebendiger. Bei jedem MCP-Dispatch wird aus dem
# Pool zufällig gewählt. Die Phrasen sind bewusst kurz (< 1.5 s TTS),
# damit die echte Antwort den Filler schnell ablösen kann.
DEFAULT_FILLER_TEXTS: list[str] = [
    "Einen Moment, ich schaue nach.",
    "Ich prüfe das kurz.",
    "Lassen Sie mich das nachsehen.",
    "Moment bitte, ich recherchiere.",
]

# Backwards-compatibility alias — some call sites / tests still import
# the singular name. Always points to the first pool entry.
DEFAULT_FILLER_TEXT = DEFAULT_FILLER_TEXTS[0]


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
        filler_text: Optional[str] = None,
        filler_texts: Optional[list[str]] = None,
    ) -> None:
        super().__init__(instructions=instructions)
        self._orchestrator = orchestrator
        self._correlation_id = correlation_id
        # Filler-Pool-Auflösung:
        # - Explizite `filler_texts`-Liste gewinnt (neue API).
        # - Fallback `filler_text` (Einzelphrase, legacy, weiterhin
        #   gültig für Tests und Deployments, die nur eine Phrase
        #   wollen). Wird in eine 1-Element-Liste umgewandelt.
        # - Ohne Angabe wird der kuratierte Pool genutzt.
        if filler_texts:
            self._filler_texts = list(filler_texts)
        elif filler_text:
            self._filler_texts = [filler_text]
        else:
            self._filler_texts = list(DEFAULT_FILLER_TEXTS)
        self._init_task: Optional[asyncio.Task] = None

    async def on_enter(self) -> None:
        """Returns immediately. Two side effects are scheduled in the
        background so the greeting (fired by agent.py right after
        session.start) is not blocked by MCP-subprocess spawn or any
        Mistral-side handshake:

        1. Wire the orchestrator's tool-started callback so we can
           speak the filler sentence as soon as Mistral signals the
           start of a tool execution.
        2. Run orchestrator.initialize() as a background asyncio task.
           If the user speaks before init finishes, run_turn() will
           wait briefly (up to ~10 s) on the orchestrator's
           init_complete event before either proceeding or yielding
           the fallback reply.
        """
        logger.info(
            "mistral_agent_on_enter",
            extra={"correlation_id": self._correlation_id},
        )
        self._orchestrator.set_tool_started_callback(self._speak_filler)
        self._init_task = asyncio.create_task(
            self._initialize_orchestrator_in_background()
        )

    async def _initialize_orchestrator_in_background(self) -> None:
        try:
            await self._orchestrator.initialize()
        except Exception:
            logger.exception(
                "mistral_orchestrator_background_init_failed",
                extra={"correlation_id": self._correlation_id},
            )

    def _speak_filler(self, tool_name: str) -> None:
        """Invoked by the orchestrator on the first ToolExecutionStartedEvent
        of a turn. Queues the filler sentence into LiveKit's speech
        queue. The subsequent LLM reply will be queued *after* the
        filler (FIFO ordering at the same priority), so sentences
        never get cut mid-word. The user can interrupt either with
        their voice (allow_interruptions=True is LiveKit's default).
        """
        # Agent.session is a property that raises if no activity is
        # bound. Guard with try/except rather than a `is None` check
        # so we degrade quietly during the brief race where the
        # orchestrator emits a tool event before the LiveKit session
        # is fully wired.
        try:
            session = self.session
        except Exception:
            logger.warning(
                "mistral_agent_filler_skipped_no_session",
                extra={"correlation_id": self._correlation_id},
            )
            return

        phrase = random.choice(self._filler_texts)
        try:
            session.say(
                phrase,
                allow_interruptions=True,
                add_to_chat_ctx=False,
            )
            logger.info(
                "mistral_agent_filler_spoken",
                extra={
                    "correlation_id": self._correlation_id,
                    "tool_name": tool_name,
                    "filler_text_length": len(phrase),
                    "filler_pool_size": len(self._filler_texts),
                },
            )
        except Exception:
            logger.exception(
                "mistral_agent_filler_failed",
                extra={"correlation_id": self._correlation_id},
            )

    async def on_exit(self) -> None:
        logger.info(
            "mistral_agent_on_exit",
            extra={"correlation_id": self._correlation_id},
        )
        if self._init_task is not None and not self._init_task.done():
            self._init_task.cancel()
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

        # BUFFER-LAYER-1 (text-side): LLM → text chunks.
        # Diagnostic only — see src/voice_diagnostics.py for the full layer map.
        import time as _diag_time

        _diag_first_chunk_logged = False
        async for chunk in self._orchestrator.run_turn(user_text):
            if not _diag_first_chunk_logged:
                _diag_first_chunk_logged = True
                logger.info(
                    "tx_llm_first_chunk",
                    extra={
                        "correlation_id": self._correlation_id,
                        "t_monotonic_s": round(_diag_time.monotonic(), 4),
                        "chunk_preview": (chunk if isinstance(chunk, str) else "")[:40],
                    },
                )
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
