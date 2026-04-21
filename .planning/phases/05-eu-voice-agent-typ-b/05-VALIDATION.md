---
phase: 05
slug: eu-voice-agent-typ-b
status: active
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-20
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `apps/agent/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd apps/agent && uv run pytest tests/test_mode_switch.py tests/test_mode_env_validation.py tests/test_mode_failure_policy.py -q` |
| **Full suite command** | `cd apps/agent && uv run pytest tests/test_agent.py tests/test_mode_switch.py tests/test_mode_env_validation.py tests/test_mode_failure_policy.py -q` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/agent && uv run pytest tests/test_mode_switch.py tests/test_mode_env_validation.py tests/test_mode_failure_policy.py -q`
- **After every plan wave:** Run `cd apps/agent && uv run pytest tests/test_agent.py tests/test_mode_switch.py tests/test_mode_env_validation.py tests/test_mode_failure_policy.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | AGNT-05 | unit/integration | `cd apps/agent && python -m pytest tests/unit -q` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | AGNT-05 | integration | `cd apps/agent && python -m pytest -k mode_switch -q` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | AGNT-05 | integration | `cd apps/agent && uv run pytest tests/test_mode_switch.py tests/test_mode_env_validation.py tests/test_mode_failure_policy.py -q` | ✅ | ✅ green |
| 05-03-01 | 03 | 2 | AGNT-05 | integration/manual-hybrid | `cd apps/agent && python -m pytest -k voxtral -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `apps/agent/tests/test_mode_switch.py` — validates ENV-based mode selection and default Typ B behavior
- [x] `apps/agent/tests/test_mode_env_validation.py` — validates required Typ-B ENV contract and DE/EN language acceptance
- [x] `apps/agent/tests/test_mode_failure_policy.py` — validates hard-fail behavior without silent fallback

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DE+EN provider smoke via language ENV (`AGENT_LANGUAGE=de|en`) | AGNT-05 (D-10) | Runtime provider quality is environment-dependent and requires deployed credentials | Execute technical smoke with `uv run pytest tests/test_mode_env_validation.py -q` and verify both parametrized languages pass |
| Product hearing test for subjective audio quality | AGNT-05 (D-09) | Intentionally excluded as release gate in this phase | Not a mandatory gate for Phase 05; defer to later product QA |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
