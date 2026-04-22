"""Phase-05 step 1.4 — external Mistral orchestrator for the type_b path.

Replaces the LiveKit-driven AgentSession tool loop with a Mistral-driven
RunContext that owns the conversation state and the Frappe MCP client.
LiveKit keeps only STT/VAD/TTS duties; the upcoming MistralDrivenAgent
(step 1.5) consumes `run_turn()` from its `llm_node` override.

Architecture notes (Phase-05 D-17, D-18):
- One orchestrator per voice session; lifecycle bound to the LiveKit
  session (initialize/on_enter, aclose/on_exit).
- `conversation_id` is assigned by Mistral on the first turn and
  persisted in `RunContext` — subsequent `run_turn()` calls on the same
  instance share server-side state, giving us free cross-turn memory.
- Tool filtering uses Mistral's built-in include/exclude mechanism in
  `RunContext.register_mcp_client`. The allowlist from
  `get_allowed_tools_for_mode("type_b")` is passed verbatim.
- MCP-client cleanup is owned by `RunContext.__aexit__`; we don't call
  `mcp_client.aclose()` manually.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, AsyncIterator, Optional

from src.frappe_mcp import build_frappe_mistral_mcp_client

if TYPE_CHECKING:
    from mistralai.client import Mistral
    from mistralai.extra.mcp.base import MCPClientProtocol
    from mistralai.extra.run.context import RunContext

logger = logging.getLogger(__name__)


class MistralOrchestrator:
    """Runs the type_b Mistral tool loop outside LiveKit's AgentSession.

    Lifecycle:
        orch = MistralOrchestrator(...)
        await orch.initialize()
        async for chunk in orch.run_turn("user text"):
            # feed chunk into LiveKit TTS
            ...
        await orch.aclose()

    `initialize()` and `aclose()` are idempotent. Calling `run_turn()`
    before `initialize()` or after `aclose()` raises `RuntimeError`.
    """

    def __init__(
        self,
        *,
        api_key: str,
        agent_id: Optional[str],
        model: Optional[str],
        allowed_tools: Optional[list[str]],
        instructions: str,
        correlation_id: str,
        mcp_client_factory=build_frappe_mistral_mcp_client,
        mistral_client_factory=None,
    ) -> None:
        # Exactly one of agent_id / model must be set (Mistral SDK
        # enforces this in RunContext.__post_init__, but we fail earlier
        # with a clearer message).
        if bool(agent_id) == bool(model):
            raise ValueError(
                "MistralOrchestrator requires exactly one of agent_id (production) "
                "or model (stateless); got "
                f"agent_id={agent_id!r}, model={model!r}"
            )
        if not api_key:
            raise ValueError("MistralOrchestrator requires a non-empty api_key")

        self._api_key = api_key
        self._agent_id = agent_id
        self._model = model
        self._allowed_tools = list(allowed_tools) if allowed_tools else None
        self._instructions = instructions
        self._correlation_id = correlation_id
        self._mcp_client_factory = mcp_client_factory
        self._mistral_client_factory = mistral_client_factory

        self._client: Optional["Mistral"] = None
        self._run_ctx: Optional["RunContext"] = None
        self._mcp_client: Optional["MCPClientProtocol"] = None
        self._initialized = False
        self._closed = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        if self._closed:
            raise RuntimeError("cannot initialize a closed MistralOrchestrator")
        if self._initialized:
            return

        from mistralai.extra.run.context import RunContext

        if self._mistral_client_factory is not None:
            self._client = self._mistral_client_factory(api_key=self._api_key)
        else:
            from mistralai.client import Mistral
            self._client = Mistral(api_key=self._api_key)

        self._run_ctx = RunContext(
            agent_id=self._agent_id,
            model=self._model,
        )
        await self._run_ctx.__aenter__()

        self._mcp_client = self._mcp_client_factory()

        tool_configuration = None
        if self._allowed_tools is not None:
            tool_configuration = {"include": list(self._allowed_tools)}

        await self._run_ctx.register_mcp_client(
            mcp_client=self._mcp_client,
            tool_configuration=tool_configuration,
        )

        registered = [t.function.name for t in self._run_ctx.get_tools()]
        logger.info(
            "mistral_orchestrator_initialized",
            extra={
                "correlation_id": self._correlation_id,
                "agent_id": self._agent_id,
                "model": self._model,
                "allowed_tools_count": len(self._allowed_tools or []),
                "registered_tools": registered,
                "registered_tools_count": len(registered),
            },
        )

        self._initialized = True

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._run_ctx is not None:
            # RunContext.__aexit__ closes the exit_stack (MCP subprocess)
            # and calls aclose() on every registered MCP client.
            await self._run_ctx.__aexit__(None, None, None)
        logger.info(
            "mistral_orchestrator_closed",
            extra={"correlation_id": self._correlation_id},
        )

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------

    async def run_turn(self, user_text: str) -> AsyncIterator[str]:
        """Stream plain-text chunks for one user turn.

        Tool-calls are dispatched internally by the Mistral SDK against
        the registered MCP client — callers only see text. Instructions
        (system prompt) are sent per-turn only in stateless mode; in
        agent_id mode the Mistral Console agent's system prompt wins and
        we pass no override.
        """
        if not self._initialized:
            raise RuntimeError("run_turn() called before initialize()")
        if self._closed:
            raise RuntimeError("run_turn() called after aclose()")
        assert self._client is not None and self._run_ctx is not None

        # Late imports so tests that monkey-patch these symbols don't
        # have to reach into a module-level cache.
        from mistralai.client.models.messageoutputevent import MessageOutputEvent
        from mistralai.extra.run.result import RunResult

        # Instructions: only override in stateless mode.
        stream_kwargs: dict = {
            "run_ctx": self._run_ctx,
            "inputs": user_text,
        }
        if self._model is not None:
            stream_kwargs["instructions"] = self._instructions

        async for event in self._client.beta.conversations.run_stream_async(
            **stream_kwargs
        ):
            # The last yielded object is a RunResult summary; we stop there.
            if isinstance(event, RunResult):
                break

            data = getattr(event, "data", None)
            if not isinstance(data, MessageOutputEvent):
                continue

            for chunk in self._extract_text(data):
                yield chunk

    @staticmethod
    def _extract_text(msg: "MessageOutputEvent") -> list[str]:
        """Flatten MessageOutputEvent.content (str or OutputContentChunks)
        into a list of plain-text pieces suitable for LiveKit TTS."""
        content = msg.content
        if isinstance(content, str):
            return [content] if content else []

        # OutputContentChunks: iterate over .chunks, keep only text.
        text_pieces: list[str] = []
        chunks = getattr(content, "chunks", None) or []
        for chunk in chunks:
            text = getattr(chunk, "text", None)
            if isinstance(text, str) and text:
                text_pieces.append(text)
        return text_pieces

    # ------------------------------------------------------------------
    # Introspection (for tests and diagnostics)
    # ------------------------------------------------------------------

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def registered_tool_names(self) -> list[str]:
        if self._run_ctx is None:
            return []
        return [t.function.name for t in self._run_ctx.get_tools()]
