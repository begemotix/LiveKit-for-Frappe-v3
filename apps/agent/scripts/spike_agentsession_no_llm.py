"""
Phase-05 Spike 1.0 — can AgentSession(livekit-agents==1.5.5) be driven without
a real LLM so that a custom llm_node yields plain-text chunks to the TTS path?

Four questions:
  1. Is AgentSession(llm=None, ...) stable at instantiation?
  2. Does a custom llm_node yielding strings reach the TTS pipeline?
  3. Does stream-end flush cleanly without hangers?
  4. If (1) fails: does a minimal NullLLM(llm.LLM) stub unblock the path?

This spike does static + lightweight dynamic verification. It does NOT open a
LiveKit room — that would require a server. Instead it instantiates the session
and inspects the code paths that the session would exercise on a user turn.
"""
from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterable

from livekit.agents import llm as lk_llm
from livekit.agents.voice.agent_session import AgentSession
from livekit.agents.voice.agent import Agent, ModelSettings
from livekit.agents.types import FlushSentinel


# ---------------------------------------------------------------------------
# 1. Static path analysis of the installed 1.5.5 code
# ---------------------------------------------------------------------------

def static_analysis() -> dict:
    """Read the source lines that gate llm_node invocation."""
    from livekit.agents.voice import agent_activity as aa

    src = inspect.getsource(aa)
    findings = {}

    # Gate 1: pipeline_reply_task is only spawned for isinstance(self.llm, llm.LLM)
    findings["pipeline_gate_requires_llm_instance"] = (
        "elif isinstance(self.llm, llm.LLM):" in src
        and "self._pipeline_reply_task(" in src
    )

    # Gate 2: on_user_turn_completed early-returns when self.llm is None
    findings["on_user_turn_skips_when_llm_none"] = (
        "elif self.llm is None:" in src
        and "# skip response if no llm is set" in src
    )

    # Gate 3: generate_reply raises if self.llm is None
    findings["generate_reply_requires_llm"] = (
        'raise RuntimeError("trying to generate reply without an LLM model")' in src
    )

    return findings


# ---------------------------------------------------------------------------
# 2. AgentSession(llm=None) instantiation
# ---------------------------------------------------------------------------

def try_session_with_none() -> dict:
    result = {"instantiated": False, "session_llm_is_none": None, "error": None}
    try:
        session = AgentSession(llm=None)
        result["instantiated"] = True
        result["session_llm_is_none"] = session.llm is None
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


# ---------------------------------------------------------------------------
# 3. NullLLM fallback stub
# ---------------------------------------------------------------------------

class NullLLM(lk_llm.LLM):
    """Minimal LLM stub: satisfies isinstance(..., LLM) routing so that
    AgentActivity._pipeline_reply_task fires and invokes the overridden
    llm_node. chat() is never called when llm_node is fully overridden."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def model(self) -> str:
        return "null-llm"

    @property
    def provider(self) -> str:
        return "spike"

    def chat(self, *_args, **_kwargs):
        raise RuntimeError(
            "NullLLM.chat() must never be called — llm_node override missing?"
        )


def try_session_with_null_llm() -> dict:
    result = {
        "instantiated": False,
        "llm_is_lk_llm_instance": None,
        "pipeline_gate_would_open": None,
        "error": None,
    }
    try:
        session = AgentSession(llm=NullLLM())
        result["instantiated"] = True
        result["llm_is_lk_llm_instance"] = isinstance(session.llm, lk_llm.LLM)
        # This is the exact gate at agent_activity.py line 1191.
        result["pipeline_gate_would_open"] = isinstance(session.llm, lk_llm.LLM)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


# ---------------------------------------------------------------------------
# 4. Sanity-check: custom llm_node can yield strings + FlushSentinel
#    (type-level verification, see perform_llm_inference at generation.py:149-188)
# ---------------------------------------------------------------------------

class DemoAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="demo")

    async def llm_node(
        self,
        chat_ctx: lk_llm.ChatContext,
        tools: list[lk_llm.Tool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[str | FlushSentinel]:
        yield "Hallo"
        yield ", "
        yield "ich bin ein Spike."
        yield FlushSentinel()


async def exercise_llm_node() -> dict:
    agent = DemoAgent()
    chunks: list = []
    async for chunk in agent.llm_node(
        chat_ctx=lk_llm.ChatContext(), tools=[], model_settings=ModelSettings()
    ):
        chunks.append(chunk)
    return {
        "chunk_count": len(chunks),
        "str_chunks": [c for c in chunks if isinstance(c, str)],
        "flush_sentinel_present": any(isinstance(c, FlushSentinel) for c in chunks),
    }


# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("Spike 1.0 — AgentSession without real LLM (livekit-agents 1.5.5)")
    print("=" * 70)

    print("\n[1] Static analysis of 1.5.5 code paths:")
    for k, v in static_analysis().items():
        print(f"    {k}: {v}")

    print("\n[2] AgentSession(llm=None):")
    for k, v in try_session_with_none().items():
        print(f"    {k}: {v}")

    print("\n[3] AgentSession(llm=NullLLM()):")
    for k, v in try_session_with_null_llm().items():
        print(f"    {k}: {v}")

    print("\n[4] Custom llm_node yields strings + FlushSentinel:")
    r = asyncio.run(exercise_llm_node())
    for k, v in r.items():
        print(f"    {k}: {v}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
