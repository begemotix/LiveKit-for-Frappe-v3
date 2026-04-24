"""Lightweight tests for the voice diagnostics activation.

The module is diagnostic-only; the functional guarantees we care about
are (a) it does not alter behaviour, (b) it's idempotent, and (c) it
downgrades cleanly when the target classes shift under a future LiveKit
upgrade. Full monkey-patch correctness is verified by observation in
production logs — the point of the module is to generate those logs.
"""
from __future__ import annotations

import importlib
import logging


def _reload():
    import src.voice_diagnostics as m

    importlib.reload(m)
    return m


def test_apply_is_idempotent_on_real_targets():
    m = _reload()

    m.apply_voice_diagnostics()
    m.apply_voice_diagnostics()  # second call must not double-wrap or raise


def test_apply_logs_its_activation():
    m = _reload()

    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            captured.append(record)

    handler = _Capture(level=logging.INFO)
    agent_logger = logging.getLogger("agent")
    prior_level = agent_logger.level
    agent_logger.setLevel(logging.INFO)
    agent_logger.addHandler(handler)
    try:
        m.apply_voice_diagnostics()
    finally:
        agent_logger.removeHandler(handler)
        agent_logger.setLevel(prior_level)

    activation = [rec for rec in captured if rec.message == "voice_diagnostics_applied"]
    assert activation, "expected an activation INFO log"
    assert activation[0].burst_idle_threshold_ms == 300
