---
phase: 03
slug: agent-core
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-18
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest apps/agent/tests/test_agent.py` |
| **Full suite command** | `pytest apps/agent/tests/` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

| Frequency | Action |
|-----------|--------|
| **After every task commit** | Run `grep` verification (Wave 1/2) or `pytest` (Wave 3+) |
| **After every plan wave** | Run `pytest apps/agent/tests/` |
| **Before `/gsd-verify-work`** | Full suite must be green |
| **Max feedback latency** | 15 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | AGNT-01 | integration | `test -f apps/agent/agent.py` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | D-02 | compliance | `grep "OpenAI in den USA" apps/agent/.env.example` | ✅ | ⬜ pending |
| 03-02-01 | 02 | 2 | AGNT-03 | smoke test | `grep "ServerVADOptions" apps/agent/agent.py` | ✅ | ⬜ pending |
| 03-02-03 | 02 | 2 | AGNT-04 | unit | `grep "mock_data_lookup" apps/agent/agent.py` | ✅ | ⬜ pending |
| 03-03-01 | 03 | 3 | AGNT-01/04 | automated | `pytest apps/agent/tests/test_agent.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/agent/tests/test_agent.py` — stubs for AGNT-01, AGNT-03, AGNT-04
- [ ] `pip install pytest pytest-asyncio` — if no framework detected

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Natural Conversation Flow | AGNT-02 | Subjective quality | User initiates a call and verifies that the agent sounds natural and reacts timely. |
| Interruption Timing | AGNT-03 | Hardware/Network latency | User interrupts the agent during high network load to verify the stop behavior. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
