---
phase: 4
slug: frappe-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Quick run command** | `pytest apps/agent/tests/test_mcp_integration.py -x -q` |
| **Full suite command** | `pytest apps/agent/tests -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest apps/agent/tests/test_mcp_integration.py -x -q`
- **After every plan wave:** Run `pytest apps/agent/tests -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | INTG-01 | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_session_has_mcp_server -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | INTG-02 | unit/integration | `pytest apps/agent/tests/test_mcp_integration.py::test_mcp_headers_from_env -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | INTG-03 | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_no_runtime_credential_switch -x -q` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | INTG-04 | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_no_direct_frappe_api_calls -x -q` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | INTG-05 | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_permission_error_user_friendly_no_retry -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/agent/tests/test_mcp_integration.py` — stubs covering INTG-01 to INTG-05
- [ ] `apps/agent/.env.example` — MCP-specific ENV keys (`FRAPPE_MCP_URL` and agent credentials)
- [ ] `apps/agent/src/mcp_errors.py` (or equivalent helper module) — permission error classification helper (`is_permission_error`) plus unit tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MCP endpoint/path compatibility on target deployment (`/mcp` vs `/sse`) | INTG-02 | Requires real deployment endpoint and credentials | Configure `FRAPPE_MCP_URL`, start worker, trigger one MCP tool call, confirm successful connection in logs |
| Server-side read-only policy of dedicated agent user | INTG-04 | Depends on remote Frappe role and allowlist configuration | Attempt allowed read tool and disallowed write-like tool in staging; verify write attempt returns permission denial (403) without session crash |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
