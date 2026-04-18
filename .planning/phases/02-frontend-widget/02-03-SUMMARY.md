---
phase: 02-frontend-widget
plan: 03
subsystem: widget-ui
tags: [frontend, widget, shadcn, tailwind]
dependency_graph:
  requires: [02-01]
  provides: [widget-ui-shell]
  affects: [app-page]
tech_stack:
  added: [lucide-react]
  patterns: [shadcn/card, shadcn/scroll-area, FAB]
key_files:
  created:
    - components/widget/FloatingButton.tsx
    - components/widget/ChatPanel.tsx
    - components/widget/index.tsx
  modified:
    - app/(app)/page.tsx
decisions:
  - name: Installation von lucide-react
    rationale: Wird laut Plan für Icons benötigt, war aber nicht in package.json vorhanden.
  - name: Positionierung des Widgets
    rationale: bottom-6 right-6 für FAB, bottom-24 right-6 für Panel gemäß UI-Standard.
metrics:
  duration: 15m
  completed_date: "2026-04-18"
---

# Phase 02 Plan 03: Widget UI Shell Summary

## One-liner
Implementierung der visuellen Widget-Hülle bestehend aus einem Floating Action Button (FAB) und einem ausklappbaren Chat-Panel unter Nutzung von shadcn Komponenten.

## Key Changes
- **Floating Action Button (FAB)**: Ein fixierter Button unten rechts mit MessageCircle Icon, der den Chat-Status toggelt.
- **Chat Panel Shell**: Ein ausklappbares Panel basierend auf shadcn `Card` und `ScrollArea` mit Platzhaltern für Visualizer und Nachrichten.
- **Widget Integration**: Zusammenführung der Komponenten in `VoiceWidget` und Einbindung in die Hauptseite `app/(app)/page.tsx`.
- **Icon Library**: `lucide-react` wurde als Abhängigkeit hinzugefügt.

## Deviations from Plan
- **Rule 3 - Auto-fix**: `lucide-react` war im Plan gefordert, aber nicht installiert. Wurde nachinstalliert.
- **Pfadänderung**: `app/page.tsx` wurde im Plan genannt, die tatsächliche Datei liegt jedoch unter `app/(app)/page.tsx` (Next.js Group).

## Known Stubs
- **ChatPanel.tsx**:
  - Zeile 23: Platzhalter-Text für Willkommensnachricht.
  - Zeile 28: Platzhalter für Voice-Visualizer.
  - Zeile 39: `console.log` Stub für den "Gespräch starten" Button. Diese werden in späteren Plänen der Phase 02 (02-04, 02-05) durch echte Logik ersetzt.

## Self-Check: PASSED
- [x] FloatingButton.tsx existiert
- [x] ChatPanel.tsx existiert
- [x] index.tsx existiert
- [x] app/(app)/page.tsx integriert das Widget
- [x] Commits für alle Tasks vorhanden
