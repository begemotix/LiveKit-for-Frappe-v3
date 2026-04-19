# LiveKit for Frappe

## What This Is

Ein White-Label Open-Source Voice-Assistent für Frappe/ERPNext, der vollständig selbst-gehostet auf eigener Kunden-Infrastruktur läuft. Nutzer können per Browser-Widget, Chatbot oder Telefon direkt mit ihrem ERP interagieren und Aktionen im Namen ihres authentifizierten Frappe-Users ausführen.

## Core Value

Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.

## Requirements

### Validated

- [x] Einrichtung des selbst-gehosteten LiveKit-Servers via Docker (Validiert in Phase 01: infrastructure-setup)
- [x] Bereitstellung der Infrastruktur über Docker Compose (Validiert in Phase 01: infrastructure-setup)

### Active

- [ ] Implementierung des Agent-Workers (Typ A - OpenAI Realtime API) für geringe Latenz
- [ ] Bereitstellung eines Browser-Widgets (Next.js) für Voice-Interaktionen
- [ ] Anbindung an Frappe über MCP (Read-only Abfragen)

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

## Agent Rules & Guidelines

- **Primäre Datenquelle**: Cursor ist zwingend angewiesen, für alle technischen Recherchen und Implementierungsschritte bezüglich LiveKit (Server-Setup, Agent-Worker, Frontend-Hooks) vorrangig das angebundene LiveKit-Dokumentations-MCP zu nutzen. Dies stellt sicher, dass stets die aktuellsten Best Practices für WebRTC, Token-Handling und die Realtime-API verwendet werden. Manuelle Suchen oder allgemeine LLM-Kenntnisse dienen nur als Sekundärquelle, falls das MCP keine spezifische Antwort liefert.

## Key Decisions

| Decision                       | Rationale                                                                                                                                 | Outcome   |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| MCP für Frappe-Integration     | Keine eigene API nötig; standardisierte Anbindung, Tools werden dynamisch vom Frappe-MCP-Server bezogen.                                  | — Pending |
| OpenAI Realtime (Typ A) für V1 | Schnelles Feedback, geringe Latenz, keine separaten STT/TTS-Module nötig. Eignet sich für Evaluationen ohne harte EU-DSGVO Anforderungen. | — Pending |
| Template-Nutzung               | Orientierung an offiziellen LiveKit-Repos für hohe Wartbarkeit und Kompatibilität.                                                        | — Pending |
| D-A: Prompts ab Phase 4+ aus Frappe | `readme/AGENT_PROMPT.md` ist nur Demo-Übergang; ab Phase 4 erfolgt Prompt-Steuerung aus Frappe statt Filesystem. Keine Mehrinvestition in Markdown-System. | — Accepted |
| D-B: DSGVO-Ansage nicht auf Agent-Ebene | Telefon-Ansage via Zadarma vor Übergabe, Browser-Hinweis als UI-Text in späterer Frontend-Phase; keine LiveKit-Audioansage/Cloud-TTS. `NEXT_PUBLIC_GDPR_NOTICE` bleibt, Default leer. | — Accepted |
| D-C: Reverse-Proxy = Coolify-Traefik | Produktivpfad nutzt Coolify-Traefik. Caddy bleibt nur optional und auskommentiert für Nicht-Coolify-Deployments im Repo. | — Accepted |
| D-D: Universelles internes Wiring über host.docker.internal | Agent und Frontend verbinden LiveKit intern stabil über `host.docker.internal` plus `host-gateway`; harte IPs werden vermieden. | — Accepted |
| D-E: Hybrid Networking als Produktivstandard | LiveKit läuft im Host-Netz für WebRTC-Ports, Agent und Frontend im Bridge-Netz für Traefik-Integration und Betriebssicherheit. | — Accepted |

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

_Last updated: 2026-04-19 after Phase 01 gap-closure documentation (01-03)_
