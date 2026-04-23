"""Unit tests for ``MistralAgentLLM`` — the dünn subclass that adds
Mistral Console Agent (``agent_id``) support to the upstream
``mistralai.LLM`` plugin.

The tests verify the critical contract: when ``agent_id`` is set, any
call to ``start_stream_async`` must be rewritten so that it carries
``agent_id`` instead of ``model``. When ``agent_id`` is ``None``, the
subclass must be a no-op — identical to the plain upstream plugin.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mistral_llm import MistralAgentLLM


def _fake_mistral_client() -> MagicMock:
    """Construct a MagicMock shaped like the Mistral client so the
    subclass can wrap `client.beta.conversations.start_stream_async`
    without network side-effects."""
    client = MagicMock(name="FakeMistralClient")
    client.beta.conversations.start_stream_async = AsyncMock(
        name="start_stream_async",
        return_value="stream-sentinel",
    )
    return client


@pytest.mark.asyncio
async def test_agent_id_wrapper_strips_model_and_injects_agent_id():
    """With agent_id set, a call to start_stream_async must drop the
    model kwarg the plugin sends and substitute agent_id on the way
    to the real Mistral client. This is the whole point of the subclass."""
    fake_client = _fake_mistral_client()
    # Capture the underlying AsyncMock BEFORE MistralAgentLLM replaces
    # the attribute with its wrapper — assertions go against this
    # reference, not the wrapped callable.
    underlying_mock = fake_client.beta.conversations.start_stream_async

    llm = MistralAgentLLM(
        agent_id="ag_01TEST",
        api_key="dummy",
        client=fake_client,
    )

    # Simulate what the plugin's LLMStream would do internally: call
    # start_stream_async with model=<stored> and some arbitrary kwargs.
    await llm._client.beta.conversations.start_stream_async(
        inputs="hello",
        model="mistral-small-latest",  # placeholder from subclass init
        instructions="be brief",
        timeout_ms=30000,
    )

    # The underlying real mock was called ONCE, and the kwargs it saw
    # must be model-less and carry agent_id.
    assert underlying_mock.call_count == 1
    called_kwargs = underlying_mock.call_args.kwargs
    assert "model" not in called_kwargs
    assert called_kwargs["agent_id"] == "ag_01TEST"
    # Unrelated kwargs must pass through untouched.
    assert called_kwargs["inputs"] == "hello"
    assert called_kwargs["instructions"] == "be brief"
    assert called_kwargs["timeout_ms"] == 30000


@pytest.mark.asyncio
async def test_no_agent_id_is_pure_passthrough():
    """When agent_id is None, the subclass must NOT install any wrapper.
    Calls to start_stream_async go straight through, carrying whatever
    kwargs the plugin supplied (including model)."""
    fake_client = _fake_mistral_client()

    llm = MistralAgentLLM(
        model="ministral-8b-latest",
        api_key="dummy",
        client=fake_client,
    )

    assert llm.agent_id is None

    await llm._client.beta.conversations.start_stream_async(
        inputs="hello",
        model="ministral-8b-latest",
    )

    called_kwargs = fake_client.beta.conversations.start_stream_async.call_args.kwargs
    # Model is unchanged
    assert called_kwargs["model"] == "ministral-8b-latest"
    # No agent_id was added
    assert "agent_id" not in called_kwargs


def test_agent_id_property_reflects_ctor_arg():
    fake_client = _fake_mistral_client()

    llm_with = MistralAgentLLM(agent_id="ag_01FOO", api_key="k", client=fake_client)
    assert llm_with.agent_id == "ag_01FOO"

    llm_without = MistralAgentLLM(model="x", api_key="k", client=_fake_mistral_client())
    assert llm_without.agent_id is None


def test_placeholder_model_is_applied_when_only_agent_id_supplied():
    """The upstream plugin requires ``model``. When the caller gives us
    only ``agent_id``, we must still satisfy the parent ctor with a
    valid placeholder. The placeholder is irrelevant at runtime because
    the wrapper strips it."""
    fake_client = _fake_mistral_client()

    llm = MistralAgentLLM(
        agent_id="ag_01PLACEHOLDER",
        api_key="dummy",
        client=fake_client,
    )

    # The plugin stores model on the LLM instance via a `model` property.
    # We don't care what it says — only that construction didn't fail.
    assert llm.agent_id == "ag_01PLACEHOLDER"


@pytest.mark.asyncio
async def test_explicit_model_with_agent_id_is_overridden_by_wrapper():
    """If a caller passes BOTH agent_id and model, we still enforce
    agent-mode: model is stripped at the HTTP call boundary. The user
    presumably wanted the Console agent (agent_id is the more specific
    intent)."""
    fake_client = _fake_mistral_client()
    underlying_mock = fake_client.beta.conversations.start_stream_async

    llm = MistralAgentLLM(
        agent_id="ag_01BOTH",
        model="mistral-large-latest",  # will not reach the API
        api_key="dummy",
        client=fake_client,
    )

    await llm._client.beta.conversations.start_stream_async(
        inputs="hi",
        model="mistral-large-latest",  # what the plugin thinks it's sending
    )

    called_kwargs = underlying_mock.call_args.kwargs
    assert "model" not in called_kwargs
    assert called_kwargs["agent_id"] == "ag_01BOTH"
