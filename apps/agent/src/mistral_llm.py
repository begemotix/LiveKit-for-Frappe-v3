"""Mistral Console Agent (agent_id) support for the LiveKit LLM pipeline.

The upstream ``livekit-plugins-mistralai`` LLM plugin wraps Mistral's
Conversations API via ``self._client.beta.conversations.start_stream_async``.
Its ``__init__`` accepts only ``model`` — there is no hook for
``agent_id``. The Mistral API rejects requests that carry both ``model``
and ``agent_id`` at the same time (they are mutually exclusive).

This subclass enables the Mistral Console Agent workflow without
forking the plugin:

1. It accepts an ``agent_id`` constructor parameter.
2. It installs a thin runtime wrapper on the internal
   ``client.beta.conversations.start_stream_async`` that removes the
   ``model`` kwarg and injects ``agent_id`` on the way out.
3. Subsequent turns use ``append_stream_async`` (which carries
   ``conversation_id`` only — no model, no agent_id) and are
   unaffected.

If ``agent_id`` is ``None``, the subclass is behaviourally identical
to the plain upstream ``mistralai.LLM`` — safe to use in both modes.

See ``readme/MISTRAL-AGENT.md`` for the customer-facing rationale
(Mistral Console Agent as the operator-editable system prompt surface).
"""
from __future__ import annotations

from typing import Any

from livekit.plugins.mistralai import LLM as _BaseMistralLLM

_PLACEHOLDER_MODEL = "mistral-small-latest"


class MistralAgentLLM(_BaseMistralLLM):
    """Mistral LLM that can address a Mistral Console Agent by id.

    Usage:

        llm = MistralAgentLLM(agent_id="ag_01xxxxx", api_key=…)

        # Or stateless (delegates to plain plugin behaviour):
        llm = MistralAgentLLM(model="ministral-8b-latest", api_key=…)
    """

    def __init__(
        self,
        *,
        agent_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        # The upstream plugin requires a `model`. When using agent_id we
        # still have to pass one to the parent ctor — it gets stored on
        # the LLMStream and handed to start_stream_async alongside the
        # other kwargs. We filter it out at the HTTP call site (see
        # ``_wrap_client_for_agent_id``), so the placeholder value never
        # reaches the Mistral API.
        if agent_id is not None and "model" not in kwargs:
            kwargs["model"] = _PLACEHOLDER_MODEL

        super().__init__(**kwargs)
        self._agent_id = agent_id

        if agent_id is not None:
            self._wrap_client_for_agent_id()

    def _wrap_client_for_agent_id(self) -> None:
        """Install a runtime wrapper on the Mistral client's
        ``start_stream_async`` method. Only called when ``agent_id`` is
        set. Idempotent — wraps the current bound method once per
        instance."""
        agent_id = self._agent_id
        assert agent_id is not None

        original_start = self._client.beta.conversations.start_stream_async

        async def wrapped_start(**kwargs: Any) -> Any:
            # Mistral API requirement: either model or agent_id, not both.
            # The plugin always forwards `model`; we strip it here and
            # override with our agent_id so the request goes to the
            # Console-agent path.
            kwargs.pop("model", None)
            kwargs["agent_id"] = agent_id
            return await original_start(**kwargs)

        # Attach the wrapped callable on the instance's conversations
        # object. Python method lookup finds this attribute before the
        # unbound class method, so all callers (including internal
        # plugin code) route through the wrapper.
        self._client.beta.conversations.start_stream_async = wrapped_start

    @property
    def agent_id(self) -> str | None:
        """Mistral Console Agent id if this LLM is configured to use one,
        else ``None``."""
        return self._agent_id
