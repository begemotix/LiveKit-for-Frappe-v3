# LiveKit for Frappe

## What This Is

Ein White-Label Open-Source Voice-Assistent für Frappe/ERPNext, der vollständig selbst-gehostet auf eigener Kunden-Infrastruktur läuft. Nutzer können per Browser-Widget, Chatbot oder Telefon direkt mit ihrem ERP interagieren und Aktionen im Namen ihres authentifizierten Frappe-Users ausführen.

## Core Value

Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Einrichtung des selbst-gehosteten LiveKit-Servers via Docker
- [ ] Implementierung des Agent-Workers (Typ A - OpenAI Realtime API) für geringe Latenz
- [ ] Bereitstellung eines Browser-Widgets (Next.js) für Voice-Interaktionen
- [ ] Anbindung an Frappe über MCP (Read-only Abfragen)
- [ ] Bereitstellung der Infrastruktur über Docker Compose (Agent, Frontend, Caddy, LiveKit)

### Out of Scope

- LiveKit Cloud oder begemotix-Cloud Hosting — Server und Agents laufen zwingend beim Kunden
- Eigene Berechtigungslogik im Agenten — Der Agent nutzt ausschließlich die Frappe-Rechte des angemeldeten Users
- Authentifizierung von anrufenden Kunden durch LiveKit — Verifizierung erfolgt separat asynchron
- Frappe-interne App/Bench-Erweiterung — Das Produkt ist eine strikt externe Standalone-Lösung

## Context

- **Produktlinien**: Typ A (OpenAI Realtime), Typ B (Mistral + EU-TTS für DSGVO), Typ C (Text-Agenten).
- **Ziel heute**: Erster Realtime-sprechender Agent (Typ A) über Browser, der sich mit Frappe verbinden kann.
- Das Projekt orientiert sich massiv an den offiziellen LiveKit Vorlagen und Repos (z.B. `agent-starter-python`, `agent-starter-embed`).
- Frontend agiert sowohl als Voice-Widget (Floating-Button) als auch als Chatbot-Fenster.

## Constraints

- **Hardware-Agnostik**: Die App bleibt hardware-agnostisch und wird als regulärer Docker-Container-Stack deployed. Hardware-Profile sind reine Deployment-Empfehlungen für Endkunden; es gibt keine festen Bindungen an spezifische VPS-Klassen.
- **White-Label & Identität**: Keine Hardcodings der Firma (begemotix) oder spezifischer Frappe-Instanzen. LiveKit darf als zugrundeliegende Technologie erkennbar bleiben. Farbwerte und Verbindungs-URLs im Frontend-Widget werden ausschließlich generisch über `.env` gesteuert.
- **Strikte MCP-Reinheit**: Keine direkten Aufrufe von Frappe-APIs. Die App agiert ausschließlich als MCP-Client. Der Agent entdeckt Tools dynamisch über den MCP-Server der Kunden-Instanz (Introspection). Es wird keine Frappe-spezifische Geschäftslogik oder Doctype-Struktur im Python-Agenten hardcoded.
- **Lizenz**: Open Source (Apache-2.0, Vorlagen via MIT mit NOTICE).
- **Deployment**: Regulärer Docker-Container-Stack (z.B. über einfaches Docker-Compose Setup) ohne tiefgreifende Modifikationen an den Standard-Templates.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| MCP für Frappe-Integration | Keine eigene API nötig; standardisierte Anbindung, Tools werden dynamisch vom Frappe-MCP-Server bezogen. | — Pending |
| OpenAI Realtime (Typ A) für V1 | Schnelles Feedback, geringe Latenz, keine separaten STT/TTS-Module nötig. Eignet sich für Evaluationen ohne harte EU-DSGVO Anforderungen. | — Pending |
| Template-Nutzung | Orientierung an offiziellen LiveKit-Repos für hohe Wartbarkeit und Kompatibilität. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-18 after initialization*