---
phase: 02
slug: frontend-widget
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                              |
| ---------------------- | ---------------------------------- |
| **Framework**          | {jest 29.x / vitest / playwright}  |
| **Config file**        | {path or "none — Wave 0 installs"} |
| **Quick run command**  | `npm test`                         |
| **Full suite command** | `npm test -- --coverage`           |
| **Estimated runtime**  | ~30 seconds                        |

---

## Sampling Rate

- **After every task commit:** Run `npm test`
- **After every plan wave:** Run `npm test -- --coverage`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | ----------------- | ----------- | ---------- |
| 02-01-01 | 01   | 1    | WIDG-01     | unit        | `npm test`        | ❌ W0       | ⬜ pending |
| 02-01-02 | 01   | 1    | WIDG-02     | unit        | `npm test`        | ❌ W0       | ⬜ pending |
| 02-01-03 | 01   | 1    | WIDG-03     | integration | `npm test`        | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/widget.test.tsx` — stubs for WIDG-01, WIDG-02
- [ ] `tests/api-token.test.ts` — stubs for WIDG-03
- [ ] `npm install --save-dev jest @types/jest` — if no framework detected

_If none: "Existing infrastructure covers all phase requirements."_

---

## Manual-Only Verifications

| Behavior            | Requirement | Why Manual                     | Test Instructions                         |
| ------------------- | ----------- | ------------------------------ | ----------------------------------------- |
| Audio visualization | WIDG-02     | Requires browser audio context | Open widget, speak, verify wave animation |

_If none: "All phase behaviors have automated verification."_

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
