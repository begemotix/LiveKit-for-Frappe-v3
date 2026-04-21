---
phase: 05-eu-voice-agent-typ-b
plan: 01
subsystem: agent
tags: [livekit, mistral, voxtral, openai, env-contract, pytest]
requires:
  - phase: 04-frappe-integration
    provides: MCP stdio sidecar contract and AgentSession tool wiring
provides:
  - Deterministic mode resolution with type_b as default
  - Mode-specific env validation for type_a and type_b
  - Provider-separated voice pipeline factory for OpenAI vs Mistral/Voxtral
affects: [05-02, agent-entrypoint, phase-06]
tech-stack:
  added: [livekit-agents mistralai extra]
  patterns: [mode_config contract, provider factory, env-first runtime switching]
key-files:
  created: [apps/agent/src/mode_config.py, apps/agent/src/model_factory.py, apps/agent/tests/test_mode_switch.py, apps/agent/tests/test_mode_env_validation.py]
  modified: [apps/agent/pyproject.toml, apps/agent/.env.example, apps/agent/uv.lock]
key-decisions:
  - "AGENT_MODE resolves deterministically to type_b when unset."
  - "No silent fallback from type_b to type_a is implemented."
  - "Voice cloning config prioritizes AGENT_VOICE_REF_AUDIO over AGENT_VOICE_ID."
patterns-established:
  - "Mode contract isolated in src/mode_config.py."
  - "Model construction isolated in src/model_factory.py."
requirements-completed: [AGNT-05]
duration: 0h 12m
completed: 2026-04-21
---

# Phase 05 Plan 01: EU voice mode foundation Summary

**Deterministic type_b default mode with strict env validation and a provider-separated OpenAI/Mistral-Voxtral factory contract for the agent runtime.**

## Performance

- **Duration:** 0h 12m
- **Started:** 2026-04-21T09:33:00Z
- **Completed:** 2026-04-21T09:45:12Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Wave-0 tests for mode switch, type_b required envs, voice priority, and DE/EN language smoke were added.
- `mode_config.py` now enforces mode defaults and per-mode required env validation.
- `model_factory.py` now builds distinct type_a and type_b pipelines without fallback behavior.
- Dependency and `.env.example` contracts now explicitly include Mistral/Voxtral and `AGENT_MODE=type_b`.

## Task Commits

1. **Task 1: Wave-0-Tests fuer Mode-Vertrag und Voice-Prioritaet anlegen** - `4759bab` (test)
2. **Task 2: Mode-Konfiguration und Pipeline-Factory fuer Typ A/B implementieren** - `eff117a` (feat)

**Additional execution metadata:** `9351488` (chore lockfile sync required after dependency change)

## Files Created/Modified
- `apps/agent/tests/test_mode_switch.py` - mode default and explicit type_a selection contract tests
- `apps/agent/tests/test_mode_env_validation.py` - required env, voice priority, and DE/EN smoke tests
- `apps/agent/src/mode_config.py` - mode/env/voice resolution and validation contract
- `apps/agent/src/model_factory.py` - provider-separated pipeline creation for type_a/type_b
- `apps/agent/pyproject.toml` - adds `mistralai` extra to LiveKit dependency
- `apps/agent/.env.example` - documents full mode-specific runtime env contract
- `apps/agent/uv.lock` - lockfile update after dependency extension

## Decisions Made
- Kept type_b as deterministic default in `resolve_agent_mode()` (Decision D-F).
- Implemented strict hard-fail env validation per mode (Decision D-06).
- Enforced voice config precedence `AGENT_VOICE_REF_AUDIO` over `AGENT_VOICE_ID` (Decision D-08).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Avoided platform DLL block during plugin imports in tests**
- **Found during:** Task 2
- **Issue:** Direct LiveKit plugin imports triggered a blocked `av` DLL load in this environment.
- **Fix:** Switched `model_factory.py` to branch-local lazy imports and mocked plugin module in the type_a test.
- **Files modified:** `apps/agent/src/model_factory.py`, `apps/agent/tests/test_mode_switch.py`
- **Verification:** `uv run pytest tests/test_mode_switch.py tests/test_mode_env_validation.py -q` passed.
- **Committed in:** `eff117a`

---

**Total deviations:** 1 auto-fixed (Rule 3: 1)
**Impact on plan:** Required to make plan verification executable on this machine; no architectural drift.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for `05-02-PLAN.md` integration into entrypoint/session wiring.

## Self-Check: PASSED

- FOUND: `apps/agent/src/mode_config.py`
- FOUND: `apps/agent/src/model_factory.py`
- FOUND: commits `4759bab`, `eff117a`, `9351488`
