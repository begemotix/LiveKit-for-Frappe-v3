# Phase 3: Agent Core - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Implementierung des zentralen Voice-Agenten (Typ A) basierend auf der OpenAI Realtime API. Fokus liegt auf geringer Latenz, natürlicher Konversation (VAD/Unterbrechungen) und der architektonischen Vorbereitung für spätere Tool-Calls. Der Agent agiert in dieser Phase als reiner Gesprächspartner ohne echten Datenzugriff.

</domain>

<decisions>
## Implementation Decisions

### 1. Persona & White-Labeling
- **D-01:** Dynamische Konfiguration — Die Persona wird ausschließlich über Environment-Variablen gesteuert (`AGENT_NAME`, `COMPANY_NAME`, `ROLE_DESCRIPTION`, `INITIAL_GREETING`, `MANDATORY_ANNOUNCEMENT`).
- **D-02:** DSGVO-Compliance — Die Pflichtansage ist ein separater ENV-Eintrag mit einem rechtlich sicheren Default-Text (kein Hardcoding).

### 2. Konversations-Flow & Filler
- **D-03:** Filler-Audio Prompt-Trick — Überbrückungssätze vor Tool-Calls werden über eine feste System-Prompt-Regel realisiert ("Sage kurz, dass du kurz nachschaust...").
- **D-04:** Architektur-Vorbereitung — Vorbereitung eines leeren `on_function_call_start` Hooks. Verifizierung der Architektur mittels eines Mock-Tools (3 Sek. Delay).

### 3. Voice Activity Detection (VAD) & Unterbrechungen
- **D-05:** Sofortiger Stopp — Bei Benutzer-Unterbrechung stoppt der Agent die Audio-Ausgabe unmittelbar.
- **D-06:** Konfigurierbare Schwellwerte — VAD-Parameter werden über ENV konfigurierbar gemacht (`VAD_THRESHOLD`, `VAD_SILENCE_DURATION_MS`).

### 4. Lifecycle & Dispatch
- **D-07:** Participant-Triggered Join — Der Agent tritt dem Raum erst bei einem `ParticipantJoined` Event bei (LiveKit Standard Dispatch), um Ressourcen in leeren Räumen zu sparen.

### 5. Dokumentation & Logging
- **D-08:** ENV-Variablen-Katalog — Erstellung eines umfassenden Katalogs in `.env.example` und einer Markdown-Doku für White-Label-Partner.
- **D-09:** Strukturiertes JSON-Logging — Nutzung der Standard-Bibliotheken `logging` und `python-json-logger`.
- **D-10:** Korrelations-ID — Ableitung einer ID aus dem LiveKit-Room-Name zur session-übergreifenden Nachverfolgbarkeit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### LiveKit Documentation
- `https://docs.livekit.io/agents/models/realtime/plugins/openai/` — OpenAI Realtime Plugin Guide
- `https://docs.livekit.io/agents/logic/turns/` — Turn detection & Interruption handling
- `https://docs.livekit.io/agents/logic/dispatch/` — Agent Dispatching & Lifecycle
- `https://github.com/livekit-examples/agent-starter-python` — Official Template (Basis der Implementierung)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Basis-Template: livekit-examples/agent-starter-python (GitHub-Repo). Muss nach apps/agent geklont werden, .git entfernen, strikt template-nah bleiben — keine architektonischen Code-Änderungen außerhalb der explizit notwendigen Erweiterungen (Persona-ENV, Filler-Hook, Logging). Die Basis-Konversationslogik und der LiveKit-Worker-Lifecycle kommen unverändert aus dem Template.

### Integration Points
- LiveKit Server (Phase 1) — Ziel für das WebRTC Signaling und Dispatching.
- Next.js Frontend (Phase 2) — Interaktionspartner für den Agenten.

</code_context>

<specifics>
## Specific Ideas
- Der Verifier für Phase 3 muss explizit prüfen, ob der Agent bei Unterbrechungen sofort schweigt.
- Die Mock-Tool Implementierung dient als "Smoke Test" für die spätere Frappe-Integration.
- Der Verifier prüft, dass die Template-Struktur erkennbar bleibt (z. B. agent.py als Entry-Point, keine eigene Orchestrierung neben livekit-agents).

</specifics>

<deferred>
## Deferred Ideas

### Out of Scope
- **A. Frappe-MCP-Anbindung:** Keine echte Datenanbindung in Phase 3. Dies ist exklusiv für Phase 4 reserviert.
- **B. Frappe-ENV-Variablen:** Variablen wie `FRAPPE_URL` oder `FRAPPE_API_KEY` werden erst in Phase 4 eingeführt.

</deferred>

---

*Phase: 03-agent-core*
*Context gathered: 2026-04-18*
