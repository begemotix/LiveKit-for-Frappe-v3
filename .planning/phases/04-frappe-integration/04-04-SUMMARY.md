---
phase: 04-frappe-integration
plan: 04
subsystem: testing
tags: [livekit, mcp, dependencies, pytest, uat]
requires:
  - phase: 04-03
    provides: MCP lifecycle, permission mapping, operator handover
provides:
  - uv/pip dependency contracts aligned with MCP-enabled livekit-agents
  - regression tests guarding MCP module import and agent import path
  - updated UAT status documenting unblocked retest sequence
affects: [phase-04-verification, phase-05-planning]
tech-stack:
  added: [livekit-agents mcp extra in pip/uv contracts, python-json-logger in uv contract]
  patterns: [dependency parity between pyproject and requirements, import-regression guard tests]
key-files:
  created: [.planning/phases/04-frappe-integration/04-04-SUMMARY.md]
  modified:
    - apps/agent/pyproject.toml
    - apps/agent/requirements.txt
    - apps/agent/tests/test_mcp_integration.py
    - .planning/phases/04-frappe-integration/04-HUMAN-UAT.md
key-decisions:
  - "Use livekit-agents[mcp,openai,silero,turn-detector]~=1.5 in pyproject to keep MCP runtime importable in uv path."
  - "Track live UAT checks as retest-required-unblocked after fixing runtime blocker instead of leaving failed/pending states."
patterns-established:
  - "Dependency parity: MCP extras must be present in both uv (pyproject) and pip (requirements) contracts."
  - "Runtime guards: keep direct mcp import and agent module import tests to prevent pre-session crash regressions."
requirements-completed: [INTG-01, INTG-02, INTG-03, INTG-04, INTG-05]
duration: 32min
completed: 2026-04-19
---

# Phase 4 Plan 04: MCP Runtime Gap Closure Summary

**MCP runtime dependency parity for uv/pip plus import-regression tests now prevents the pre-session `ModuleNotFoundError: mcp` crash and reopens live UAT retesting.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-04-19T18:46:00Z
- **Completed:** 2026-04-19T19:18:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Synchronized LiveKit dependency contracts to include MCP support in both `pyproject.toml` and `requirements.txt`.
- Added `test_mcp_module_import_available` and `test_agent_module_import_does_not_raise_mcp_import_error` to lock runtime import behavior.
- Updated `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md` with unblocked retest status for Discovery, E2E read-only, and 403 checks.

## Task Commits

Each task was committed atomically:

1. **Task 1: MCP-Runtime-Abhaengigkeiten fuer uv und pip synchronisieren** - `94b1c30` (`chore`)
2. **Task 2: Runtime-Start-Regressionstest und UAT-Re-Test-Protokoll vervollstaendigen** - `858821c` (`test`)

**Plan metadata:** pending final docs commit

## Files Created/Modified
- `apps/agent/pyproject.toml` - MCP-enabled `livekit-agents` extras and uv dependency parity fix.
- `apps/agent/requirements.txt` - pip runtime contract aligned to `livekit-agents[mcp,openai]~=1.5`.
- `apps/agent/tests/test_mcp_integration.py` - import regression guards for MCP module and agent module import path.
- `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md` - gap update and retest-required-unblocked status for all three human checks.

## Decisions Made
- Keep `livekit-agents` MCP extra mandatory in both dependency contracts to avoid session-start import failures.
- Represent post-fix human checks as `retest-required-unblocked` to reflect real execution state without claiming live-system pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added missing `python-json-logger` to uv dependency contract**
- **Found during:** Task 2 verification (`uv run pytest ...`)
- **Issue:** `agent.py` imports `pythonjsonlogger`, but uv environment lacked this dependency, blocking uv-based test execution path.
- **Fix:** Added `python-json-logger~=2.0.0` to `apps/agent/pyproject.toml`.
- **Files modified:** `apps/agent/pyproject.toml`
- **Verification:** `python -m pytest apps/agent/tests/test_mcp_integration.py -x -q` passes; agent import succeeds with MCP env vars.
- **Committed in:** `858821c` (part of Task 2 commit)

**2. [Rule 3 - Blocking] uv runtime blocked by host DLL policy for `av`**
- **Found during:** Task 1/2 uv verification commands
- **Issue:** `uv run` imports fail with `ImportError: DLL load failed ... policy blocked` in `av`.
- **Fix:** Completed equivalent verification path via system Python (`python -m pytest ...` and explicit MCP import check), preserving plan intent while documenting host constraint.
- **Files modified:** none
- **Verification:** `python -m pytest apps/agent/tests/test_mcp_integration.py -x -q` and `python -m pytest apps/agent/tests -q` both pass.
- **Committed in:** operational deviation (no file changes)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** No scope creep. Deviations were required to make verification reliable in this host environment.

## Authentication Gates

None.

## Known Stubs

None.

## Issues Encountered
- `uv` verification path is partially constrained by local Windows application control policy on `av` DLL loading.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 04 Plan 04 artifacts are complete, committed per task, and regression-guarded.
- Human live-system retests remain required in target Frappe environment (Discovery, E2E read-only, 403).

## Self-Check: PASSED

- FOUND: `.planning/phases/04-frappe-integration/04-04-SUMMARY.md`
- FOUND: `94b1c30`
- FOUND: `858821c`
