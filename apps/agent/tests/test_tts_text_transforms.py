"""Unit tests for TTS text transforms.

Verifies behaviour of ``PronunciationTransform`` and ``NumberTransform``
as plugged into LiveKit's ``tts_text_transforms`` pipeline. Each
transform's ``__call__`` is an async generator; we drive it with a small
helper and collect the emitted chunks.
"""
from __future__ import annotations

from typing import AsyncIterable

import pytest

from src.tts_text_transforms import NumberTransform, PronunciationTransform


async def _as_async_iter(chunks: list[str]) -> AsyncIterable[str]:
    for c in chunks:
        yield c


async def _collect(async_iter: AsyncIterable[str]) -> list[str]:
    out: list[str] = []
    async for chunk in async_iter:
        out.append(chunk)
    return out


# ---------------------------------------------------------------------------
# PronunciationTransform
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pronunciation_transform_replaces_single_key():
    t = PronunciationTransform({"Frappe": "Frapp"})
    out = await _collect(t(_as_async_iter(["Ich nutze Frappe gerne."])))
    assert out == ["Ich nutze Frapp gerne."]


@pytest.mark.asyncio
async def test_pronunciation_transform_replaces_multiple_keys():
    t = PronunciationTransform(
        {"Frappe": "Frapp", "ERPNext": "ERPNext-Suite"}
    )
    out = await _collect(t(_as_async_iter(["Frappe und ERPNext"])))
    assert out == ["Frapp und ERPNext-Suite"]


@pytest.mark.asyncio
async def test_pronunciation_transform_longest_key_wins():
    """``ERPNext`` must match as a whole even though ``ERP`` is also a
    key, otherwise we'd double-replace inside the longer match."""
    t = PronunciationTransform(
        {"ERP": "E-R-P", "ERPNext": "ERPNext-Suite"}
    )
    out = await _collect(t(_as_async_iter(["ERPNext ist ERP-Software"])))
    assert out == ["ERPNext-Suite ist E-R-P-Software"]


@pytest.mark.asyncio
async def test_pronunciation_transform_empty_mapping_is_passthrough():
    t = PronunciationTransform({})
    out = await _collect(t(_as_async_iter(["Hallo", " Welt"])))
    assert out == ["Hallo", " Welt"]


@pytest.mark.asyncio
async def test_pronunciation_transform_preserves_chunk_boundaries():
    """Transform must emit one output chunk per input chunk — downstream
    TTS relies on chunk boundaries for sentence pacing."""
    t = PronunciationTransform({"Frappe": "Frapp"})
    chunks = ["Frappe", " und ", "Frappe"]
    out = await _collect(t(_as_async_iter(chunks)))
    assert out == ["Frapp", " und ", "Frapp"]


@pytest.mark.asyncio
async def test_pronunciation_transform_is_case_sensitive():
    t = PronunciationTransform({"Frappe": "Frapp"})
    out = await _collect(t(_as_async_iter(["frappe und Frappe"])))
    # Only the exact-case key is replaced.
    assert out == ["frappe und Frapp"]


# ---------------------------------------------------------------------------
# NumberTransform
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_number_transform_expands_hhmm_time():
    t = NumberTransform()
    out = await _collect(t(_as_async_iter(["Der Termin ist um 14:30."])))
    assert out == ["Der Termin ist um 14 Uhr 30."]


@pytest.mark.asyncio
async def test_number_transform_expands_single_digit_hour():
    t = NumberTransform()
    out = await _collect(t(_as_async_iter(["Start um 9:05."])))
    assert out == ["Start um 9 Uhr 05."]


@pytest.mark.asyncio
async def test_number_transform_leaves_plain_numbers_alone():
    t = NumberTransform()
    out = await _collect(t(_as_async_iter(["Es gibt 42 Projekte."])))
    assert out == ["Es gibt 42 Projekte."]


@pytest.mark.asyncio
async def test_number_transform_handles_multiple_times_in_chunk():
    t = NumberTransform()
    out = await _collect(
        t(_as_async_iter(["Von 08:00 bis 17:30 geöffnet."]))
    )
    assert out == ["Von 08 Uhr 00 bis 17 Uhr 30 geöffnet."]


@pytest.mark.asyncio
async def test_number_transform_preserves_chunks_without_matches():
    t = NumberTransform()
    chunks = ["Hallo", " Welt", " ohne Zahlen"]
    out = await _collect(t(_as_async_iter(chunks)))
    assert out == chunks


# ---------------------------------------------------------------------------
# Chaining smoke-test — matches the order used in agent.py
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chaining_number_then_pronunciation_matches_agent_py_order():
    """NumberTransform runs first, PronunciationTransform second — same
    as the list passed to AgentSession. We simulate the chain by feeding
    the output of one into the other."""
    number = NumberTransform()
    pronunciation = PronunciationTransform({"Frappe": "Frapp"})
    src = _as_async_iter(["In Frappe um 14:30 einloggen."])
    out = await _collect(pronunciation(number(src)))
    assert out == ["In Frapp um 14 Uhr 30 einloggen."]
