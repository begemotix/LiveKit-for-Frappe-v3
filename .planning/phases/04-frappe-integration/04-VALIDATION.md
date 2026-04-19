---
phase: 04
slug: frappe-integration
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | apps/agent/pyproject.toml (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest apps/agent/tests/test_mcp_integration.py -x -q` |
| **Full suite command** | `uv run pytest apps/agent/tests -q` |
| **Estimated runtime** | ~20-30 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task’s `<automated>` command from the active PLAN (single-test node, `pytest --collect-only`, or smoke command as specified).
- **After every plan wave:** Run `uv run pytest apps/agent/tests -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Notes |
|---------|------|------|-------------|-----------|-------------------|--------|
| 04-01-T1 | 01 | 1 | INTG-01, INTG-02 | test scaffold | `uv run pytest apps/agent/tests/test_mcp_integration.py --collect-only -q` | Tests exist before factory impl (Nyquist task order). |
| 04-01-T2 | 01 | 1 | INTG-01, INTG-02 | unit | `uv run pytest apps/agent/tests/test_mcp_integration.py -x -q` | Covers `test_build_frappe_mcp_server_*`. |
| 04-02-T1 | 02 | 2 | INTG-03, INTG-04 | test scaffold | `uv run pytest apps/agent/tests/test_mcp_integration.py --collect-only -q` | Session/guard tests before `agent.py` wiring. |
| 04-02-T2 | 02 | 2 | INTG-03, INTG-04 | unit/integration | `uv run pytest apps/agent/tests/test_mcp_integration.py -x -q` | Covers `test_session_has_mcp_server`, cleanup, discovery, purity. |
| 04-03-T1 | 03 | 3 | INTG-05 | unit | `uv run pytest apps/agent/tests/test_mcp_integration.py::test_permission_error_user_friendly_no_retry apps/agent/tests/test_mcp_integration.py::test_permission_error_logged_with_correlation -x -q` | D-10/D-11/D-12. |
| 04-03-T2 | 03 | 3 | INTG-05 | doc | `rg -n "^(## Coolify-ENV-Variablen|## Konfigurierbare Komponenten|## Nicht-konfigurierbare Komponenten|## Handover-Checkliste fuer den Onboarding-Termin)$" .planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md` | Operator handover sections. |
| 04-04-T1 | 04 | 4 | INTG-01..05 | smoke + regression | `uv run python -c "from livekit.agents import mcp; print('mcp-ok')"` && `uv run pytest apps/agent/tests/test_mcp_integration.py -x -q` | Dependency + full integration file after deps sync. |
| 04-04-T2 | 04 | 4 | INTG-01..05 | unit | `uv run pytest apps/agent/tests/test_mcp_integration.py::test_mcp_module_import_available apps/agent/tests/test_mcp_integration.py::test_agent_module_import_does_not_raise_mcp_import_error -x -q` | Import regression nodes. |

*Status tracking during execution: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 / Nyquist Ordering

- **No separate stub wave:** Plans **04-01** and **04-02** satisfy Nyquist **8a–8d** by placing **test modules and discoverable tests in Task 1** (`pytest --collect-only`) before Task 2 implementation that runs the same nodes green.
- **`apps/agent/tests/test_mcp_integration.py`** remains the single automated contract surface for INTG-01..05 through wave 3; **04-04** adds import/regression nodes and dependency contracts.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live MCP against real Frappe (stdio sidecar + credentials) | INTG-02 | Needs deployment URL, API keys, and running worker | Set `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET`; start worker; confirm MCP session and tool calls in logs (no `ModuleNotFoundError: mcp`). |
| Server-side read-only policy of dedicated agent user | INTG-04 | Depends on remote Frappe role configuration | Attempt allowed read tool and disallowed write-like tool in staging; verify permission denial (403) without session crash (align with **04-HUMAN-UAT.md**). |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify; Task 1 in plans 01/02 uses `pytest --collect-only` where tests precede implementation
- [ ] Sampling continuity: no verify references tests that do not yet exist after prior tasks in the same plan
- [ ] No watch-mode flags
- [ ] Feedback latency <= 30s
- [ ] `nyquist_compliant: true` remains accurate after plan changes

**Approval:** pending
