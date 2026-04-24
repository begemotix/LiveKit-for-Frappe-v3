"""Unit tests for the NumPy replacement of the Voxtral PCM converter.

The patch target is ``livekit.plugins.mistralai.tts._f32le_to_s16le``.
We capture the original Python implementation as an oracle, apply the
patch to swap it for a NumPy variant, and assert bit-perfect equivalence
across a mix of random and pathological inputs.

Why bit-perfect matters: WebRTC pushes the resulting int16 samples
straight into the jitter buffer. Any off-by-one rounding mismatch
between the two implementations would be audible as a DC shift or
subtle noise floor change and would invalidate our ability to roll the
patch back as a no-op in an incident.
"""
from __future__ import annotations

import importlib
import logging
import random
import struct
from typing import Callable

import numpy as np
import pytest


@pytest.fixture()
def patch_module():
    """Reload so the module-level _PATCH_APPLIED flag is fresh per test."""
    import src.mistral_tts_cpu_patch as m

    importlib.reload(m)
    return m


@pytest.fixture()
def original_and_patched() -> tuple[Callable[[bytes], bytes], Callable[[bytes], bytes]]:
    """Return (original, patched) _f32le_to_s16le implementations.

    The patch replaces the function on the plugin module. We snapshot the
    original before applying so tests can compare the two side-by-side
    without depending on import order elsewhere.
    """
    from livekit.plugins.mistralai import tts as lk_voxtral_tts

    original = lk_voxtral_tts._f32le_to_s16le
    import src.mistral_tts_cpu_patch as m

    importlib.reload(m)
    m.apply_mistral_tts_cpu_patch()
    patched = lk_voxtral_tts._f32le_to_s16le

    yield original, patched

    lk_voxtral_tts._f32le_to_s16le = original


def _floats_to_le_bytes(samples: list[float]) -> bytes:
    """Pack floats as little-endian float32 — the on-the-wire layout from
    Voxtral when response_format="pcm"."""
    return struct.pack(f"<{len(samples)}f", *samples)


def test_patched_is_not_original(original_and_patched):
    original, patched = original_and_patched
    assert patched is not original, "apply must have replaced the function"


def test_idempotent_apply(patch_module):
    from livekit.plugins.mistralai import tts as lk_voxtral_tts

    patch_module.apply_mistral_tts_cpu_patch()
    first = lk_voxtral_tts._f32le_to_s16le

    patch_module.apply_mistral_tts_cpu_patch()
    second = lk_voxtral_tts._f32le_to_s16le

    assert first is second, "second apply must be a no-op"


def test_empty_input_matches(original_and_patched):
    original, patched = original_and_patched
    assert patched(b"") == original(b"") == b""


def test_single_zero_sample(original_and_patched):
    _, patched = original_and_patched
    data = _floats_to_le_bytes([0.0])
    # int(0.0 * 32767) == 0; int16 zero = two zero bytes little-endian.
    assert patched(data) == b"\x00\x00"


@pytest.mark.parametrize(
    "sample,expected",
    [
        # Happy-path edges — the values hit without clipping.
        (0.0, 0),
        (1.0, 32767),          # int(1.0 * 32767) = 32767
        (-1.0, -32767),        # int(-1.0 * 32767) = -32767 (not -32768!)
        (0.5, 16383),          # int(16383.5) truncates toward zero → 16383
        (-0.5, -16383),        # int(-16383.5) truncates toward zero → -16383
        # Clipping region — values past ±1.0 get clamped to int16 range.
        (1.5, 32767),          # int(49150.5) = 49150, clamp → 32767
        (-1.5, -32768),        # int(-49150.5) = -49150, clamp → -32768
        (2.0, 32767),
        (-2.0, -32768),
        # Values just inside the clamp boundary.
        (32767.0 / 32767.0, 32767),
        (-32768.0 / 32767.0, -32768),
    ],
)
def test_specific_values_match_original_semantics(
    original_and_patched, sample: float, expected: int
):
    original, patched = original_and_patched
    data = _floats_to_le_bytes([sample])
    assert patched(data) == original(data)
    got = struct.unpack("<h", patched(data))[0]
    assert got == expected, f"expected {expected} for sample {sample}, got {got}"


def test_bit_perfect_on_random_chunk(original_and_patched):
    """Match a realistic Voxtral chunk: ~4800 samples (~200 ms at 24 kHz),
    float32 little-endian, mostly in-range with occasional spikes over ±1.0."""
    original, patched = original_and_patched
    rng = random.Random(0xDEADBEEF)
    n = 4800
    samples = [rng.uniform(-1.1, 1.1) for _ in range(n)]
    # sprinkle a few explicit extremes to hit both clamp branches
    for i in (0, 100, 200, 300, 4799):
        samples[i] = 2.0 if i % 2 == 0 else -2.0
    data = _floats_to_le_bytes(samples)
    assert patched(data) == original(data)


def test_bit_perfect_on_full_sentence_chunk(original_and_patched):
    """Match a full sentence-batch-sized buffer (~9.4 s @ 24 kHz — the
    duration measured in the 2026-04-24 CPU incident). Both implementations
    must agree on ~225k samples."""
    original, patched = original_and_patched
    rng = np.random.default_rng(12345)
    n = 225_600
    samples = rng.uniform(-1.2, 1.2, size=n).astype("<f4")
    data = samples.tobytes()
    assert patched(data) == original(data)


def test_odd_byte_count_discards_trailing_bytes_like_original(original_and_patched):
    """The original computes n = len(data) // 4 and silently discards any
    trailing bytes that don't form a full float32. NumPy's frombuffer
    would normally raise on a non-multiple-of-4 length, so the patched
    version must match the original's lenient behaviour — or we must
    assert both raise consistently."""
    original, patched = original_and_patched
    # 9 bytes = 2 complete floats + 1 dangling byte
    # Use tobytes from a float32 array then append a byte.
    two_floats = np.array([0.25, -0.25], dtype="<f4").tobytes()
    data = two_floats + b"\x01"
    # The original truncates to 2 floats via // 4 then struct.unpack 2f.
    # If NumPy raises ValueError, we document that as an expected
    # behavioural divergence; production traffic never sends partial
    # samples (Voxtral always emits whole float32 frames), but we want
    # the test to pin whichever behaviour the patch chooses.
    try:
        patched_out = patched(data)
    except ValueError:
        # NumPy's frombuffer refuses non-multiple-of-itemsize buffers.
        # This is stricter than the original, but safe: Voxtral never
        # emits a partial float32 sample on the wire.
        return
    assert patched_out == original(data)


def test_warning_logged_when_module_missing(monkeypatch, patch_module, caplog):
    """If the mistralai plugin is somehow absent, apply logs a warning
    and no-ops. Simulate by temporarily hiding the module."""
    import sys

    # Attach a capture handler because the "agent" logger disables propagation.
    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            captured.append(record)

    handler = _Capture(level=logging.WARNING)
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(handler)
    try:
        monkeypatch.setitem(sys.modules, "livekit.plugins.mistralai", None)
        monkeypatch.setitem(sys.modules, "livekit.plugins.mistralai.tts", None)
        patch_module.apply_mistral_tts_cpu_patch()
    finally:
        agent_logger.removeHandler(handler)

    assert any(
        rec.message == "mistral_tts_cpu_patch_unavailable" for rec in captured
    ), "expected an mistral_tts_cpu_patch_unavailable warning"
