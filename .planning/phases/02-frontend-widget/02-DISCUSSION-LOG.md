# Phase 2: Frontend Widget - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 02-frontend-widget
**Areas discussed:** Widget-Layout, User Interface Details, Token-Generierung, Start-Verhalten, White-Labeling

---

## Widget-Layout

| Option            | Description                           | Selected |
| ----------------- | ------------------------------------- | -------- |
| Eingeklappt (FAB) | Widget startet minimiert unten rechts | ✓        |
| Inline            | Direkt eingebettet in den Content     |          |

**User's choice:** FAB-Icon (standardmäßig eingeklappt).

---

## User Interface Details

| Option                | Description                                 | Selected |
| --------------------- | ------------------------------------------- | -------- |
| Voice-Only            | Nur Waveforms, kein Text                    |          |
| Hybrid (Text + Voice) | Transkription + Waveforms für Text-Fallback | ✓        |

**User's choice:** Hybrid-Mode (zwingend Text-Historie für laute Umgebungen).

---

## Token-Generierung

| Option                  | Description                               | Selected |
| ----------------------- | ----------------------------------------- | -------- |
| Client-Side             | Schnell, aber unsicher (Exponiert Secret) |          |
| Server-Side (API Route) | Sicherer Proxy über Next.js API           | ✓        |

**User's choice:** Zwingend Next.js API-Route (z.B. /api/token). Client-Side Token Generation ist verboten.

---

## Start-Verhalten

| Option         | Description                     | Selected |
| -------------- | ------------------------------- | -------- |
| Auto-Connect   | Versucht Verbindung beim Öffnen |          |
| Connect Button | Bewusster Klick vor Audio-Start | ✓        |

**User's choice:** Expliziter "Start/Connect"-Knopf (Voraussetzung für Browser-Mikrofon-Berechtigung).

---

## White-Labeling

| Option                 | Description                          | Selected |
| ---------------------- | ------------------------------------ | -------- |
| CSS Variables via .env | Dynamische Steuerung der Primärfarbe | ✓        |
| Hardcoded Styles       | Feste Farbwerte                      |          |

**User's choice:** Styling muss flexibel über CSS-Variablen aus .env Werten gespeist werden.

---

## Claude's Discretion

- Auswahl der UI-Bibliothek (Tailwind CSS wird empfohlen).
- Genaue Struktur der Transkriptions-Anzeige.

## Deferred Ideas

- None — discussion stayed within phase scope
