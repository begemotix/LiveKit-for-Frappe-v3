"""Unit tests for the queue_size_ms monkey-patch.

The patch targets `livekit.agents.voice.room_io._output._ParticipantAudioOutput`.
We import the real class, apply the patch, and then invoke the wrapped
__init__ against a pre-prepared mock-self (so we never touch LiveKit's FFI
AudioSource). That lets us assert the two behaviours that matter:

1. The wrapper replaces `_audio_source` with a new `rtc.AudioSource`
   constructed with the requested `queue_size_ms`.
2. The wrapper is idempotent and no-ops on a broken attribute layout.
"""
from __future__ import annotations

import importlib
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def patch_module(monkeypatch: pytest.MonkeyPatch):
    """Reload the patch module so its `_PATCH_APPLIED` flag is fresh per test."""
    import src.audio_buffer_patch as m

    importlib.reload(m)
    return m


@pytest.fixture()
def target_cls():
    """Real _ParticipantAudioOutput — we need its identity for wrap tests
    but never call the real init (it would publish a WebRTC track)."""
    from livekit.agents.voice.room_io._output import _ParticipantAudioOutput

    original_init = _ParticipantAudioOutput.__init__
    yield _ParticipantAudioOutput
    _ParticipantAudioOutput.__init__ = original_init  # restore


def _invoke_wrapper_against_fake_self(
    cls, *, orig_audio_source_attrs: dict
):
    """Call the (patched) __init__ bound to a fake self that mimics what
    LiveKit's real init would have produced. We replace the real
    original_init with a stub so the wrapper runs in isolation."""
    fake_self = SimpleNamespace(
        _audio_source=SimpleNamespace(**orig_audio_source_attrs)
    )

    # The wrapper's first step is `original_init(self, *args, **kwargs)`.
    # We can't call the real init (FFI publish) in a unit test, so we
    # intercept it by monkey-patching *before* the wrapper fires.
    # In practice the wrapper calls `original_init` directly (closure);
    # to test this we pass through by overwriting __init__ ONCE more on
    # the class with a stub before invoking.
    # Trick: call the wrapper bound to fake_self; the wrapper references
    # `original_init` via its closure captured at patch-apply time.
    cls.__init__(fake_self)
    return fake_self


def test_apply_patch_wraps_init_and_replaces_audio_source(
    monkeypatch: pytest.MonkeyPatch, patch_module, target_cls
):
    # Stub the real __init__ BEFORE applying the patch, so the wrapper's
    # closure captures our stub as "original_init" — not the FFI-bound one.
    def stub_init(self, *_args, **_kwargs):
        self._audio_source = SimpleNamespace(_sample_rate=48000, _num_channels=1)

    target_cls.__init__ = stub_init

    fake_rtc_audio_source = MagicMock(
        return_value=SimpleNamespace(_sample_rate=48000, _num_channels=1, marker="new")
    )
    import livekit.rtc as rtc

    monkeypatch.setattr(rtc, "AudioSource", fake_rtc_audio_source)

    patch_module.apply_audio_buffer_patch(queue_size_ms=500)

    # __init__ is now the wrapper.
    assert target_cls.__init__ is not stub_init

    fake_self = SimpleNamespace()
    target_cls.__init__(fake_self)

    fake_rtc_audio_source.assert_called_once_with(48000, 1, queue_size_ms=500)
    assert fake_self._audio_source.marker == "new"


def test_apply_patch_is_idempotent(patch_module, target_cls):
    def stub_init(self, *_args, **_kwargs):
        self._audio_source = SimpleNamespace(_sample_rate=48000, _num_channels=1)

    target_cls.__init__ = stub_init

    patch_module.apply_audio_buffer_patch(queue_size_ms=500)
    wrapper_first = target_cls.__init__

    patch_module.apply_audio_buffer_patch(queue_size_ms=500)
    wrapper_second = target_cls.__init__

    assert wrapper_first is wrapper_second, "second apply must be a no-op"
    assert wrapper_first is not stub_init, "first apply must have replaced __init__"


def test_apply_patch_survives_unexpected_audio_source_layout(
    monkeypatch: pytest.MonkeyPatch, patch_module, target_cls
):
    # Original init produces an `_audio_source` that lacks _sample_rate.
    def stub_init(self, *_args, **_kwargs):
        self._audio_source = SimpleNamespace()  # missing attrs

    target_cls.__init__ = stub_init

    patch_module.apply_audio_buffer_patch(queue_size_ms=500)

    # The "agent" logger has propagate=False, so caplog-via-root misses it.
    # Attach a dedicated capture handler for the duration of the call.
    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):  # noqa: D401
            captured.append(record)

    handler = _Capture(level=logging.WARNING)
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(handler)
    try:
        target_cls.__init__(SimpleNamespace())
    finally:
        agent_logger.removeHandler(handler)

    assert any(
        rec.message == "audio_buffer_patch_replace_failed" for rec in captured
    ), "unexpected layout should log a warning, not raise"
