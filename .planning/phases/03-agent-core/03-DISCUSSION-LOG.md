# Phase 3: Agent Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 03-agent-core
**Areas discussed:** Persona & Branding, Konversations-Logik, VAD, Lifecycle, Logging

---

## Persona & Branding

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded Persona | Namen und Texte fest im Code hinterlegen. | |
| Dynamische ENV-Konfiguration | Volle Steuerung über ENV-Variablen mit Platzhaltern. | ✓ |

**User's choice:** Vollständige White-Labeling Unterstützung über ENV-Templates. Pflichtansage (DSGVO) als separater Eintrag.

---

## Konversations-Logik (Filler)

| Option | Description | Selected |
|--------|-------------|----------|
| Native Filler Audio | Nutzung von MP3-Dateien während Tool-Calls. | |
| Prompt-Trick | System-Prompt weist Agent an, Überbrückungssätze zu sprechen. | ✓ |

**User's choice:** Prompt-Trick zur Überbrückung von Latenzen vor Tool-Calls. Architektur-Vorbereitung mit `on_function_call_start` Hook und Mock-Tool.

---

## VAD & Interruption

| Option | Description | Selected |
|--------|-------------|----------|
| Standard VAD | LiveKit Default-Werte nutzen. | |
| Konfigurierbares VAD | Schwellwerte via ENV steuerbar machen. | ✓ |

**User's choice:** Sofortiger Stopp bei Unterbrechung. Sensibilität (Threshold/Duration) über ENV konfigurierbar.

---

## Agent Lifecycle (Dispatch)

| Option | Description | Selected |
|--------|-------------|----------|
| Room-Creation Trigger | Agent spawnt sobald Raum existiert. | |
| Participant-Trigger | Agent spawnt erst wenn User beitritt. | ✓ |

**User's choice:** Participant-Join-Event als Trigger (Standard-Dispatch), um Leerlauf von Agenten in ungenutzten Räumen zu vermeiden.

---

## Logging & Observability

| Option | Description | Selected |
|--------|-------------|----------|
| Standard Print Logging | Einfache Konsolenausgabe. | |
| Strukturiertes JSON Logging | Professionelles Logging mit Korrelations-ID. | ✓ |

**User's choice:** JSON-Logger mit Session-ID (abgeleitet vom Room-Name) für bessere Fehlersuche.

---

## Claude's Discretion

- Feinabstimmung der VAD-Default-Werte in der Implementierungsphase.
- Wahl der spezifischen System-Prompt-Formulierungen für die Persona-Platzhalter.

## Deferred Ideas

- Echte Frappe-Anbindung (Phase 4).
- Authentifizierung/Token-Handling für Frappe-MCP (Phase 4).
