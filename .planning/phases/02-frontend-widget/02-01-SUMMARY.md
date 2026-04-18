---
phase: 02-frontend-widget
plan: 01
subsystem: frontend
tags: [setup, nextjs, shadcn, vitest, livekit]
dependency_graph:
  requires: []
  provides: [Frontend-Basis, UI-Framework, Test-Infrastruktur]
  affects: [all future frontend plans]
tech_stack:
  added: [shadcn/ui, vitest, jsdom, @testing-library/react]
  patterns: [Next.js App Router (Template based)]
key_files:
  created: [vitest.config.ts, tests/setup.ts, tests/widget.test.tsx, tests/api-token.test.ts, components/ui/card.tsx, components/ui/scroll-area.tsx, components/ui/avatar.tsx]
  modified: [package.json, tsconfig.json, components.json]
decisions:
  - Consolidate UI components in `components/ui` to match shadcn standard while keeping template compatibility.
  - Omitted `pnpm` in favor of `npm` to match existing workflow and avoid environment issues.
metrics:
  duration: 45m
  completed_date: "2026-04-18"
---

# Phase 02 Plan 01: Initialisierung & Basis-Setup Summary

## Objective

Initialisierung der Next.js Projektstruktur mit shadcn/ui und Installation der LiveKit SDKs.

## substantive one-liner

Lauffähige Next.js Basis basierend auf dem official LiveKit `agent-starter-embed` Template mit integriertem shadcn/ui und Vitest Test-Infrastruktur.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] Git Clone in non-empty directory**

- **Found during:** Task 1
- **Issue:** `git clone` funktioniert nicht in einem Verzeichnis mit Dateien aus Phase 01.
- **Fix:** Bestehende Infrastruktur-Dateien nach `infrastructure/` verschoben und Template via temporärem Ordner geklont.
- **Files modified:** Diverse (Infrastruktur verschoben)
- **Commit:** `feat(02-01): clone agent-starter-embed template and install dependencies`

**2. [Rule 3 - Blocker] Shadcn/ui Scan Permissions**

- **Found during:** Task 2
- **Issue:** Shadcn CLI versuchte Windows-Systemverzeichnisse zu scannen (EPERM).
- **Fix:** `components.json` Aliase korrigiert und `pnpm` Blockade durch Löschen der `pnpm-lock.yaml` behoben.
- **Files modified:** `components.json`, `package.json`
- **Commit:** `feat(02-01): integrate shadcn/ui and add base components`

**3. [Rule 1 - Bug] Accidental deletion of template components**

- **Found during:** Task 2 Cleanup
- **Issue:** Zu aggressives Löschen des `components` Ordners entfernte Template-eigene Komponenten.
- **Fix:** Ordner via Git wiederhergestellt und UI-Komponenten in `components/ui` konsolidiert.
- **Files modified:** `components/`
- **Commit:** `fix(02-01): restore accidentally deleted components and consolidate UI structure`

## Known Stubs

- `tests/widget.test.tsx`: Wave 0 Test-Stub (Nyquist Anforderung).
- `tests/api-token.test.ts`: Wave 0 Test-Stub (Nyquist Anforderung).

## Self-Check: PASSED
