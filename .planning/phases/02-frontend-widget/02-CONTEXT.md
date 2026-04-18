# Phase 2: Frontend Widget - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Bereitstellung eines Next.js-basierten Frontend-Widgets (Voice & Text Hybrid), das als Floating Action Button (FAB) agiert. Es ermöglicht Gast-Nutzern den Aufbau einer WebRTC-Verbindung zum LiveKit-Server über eine sichere API-Route.

</domain>

<decisions>
## Implementation Decisions

### 1. Widget-Integration & Layout

- **D-01:** Start-Zustand: Eingeklappt als FAB-Icon unten rechts.
- **D-02:** Panel-Verhalten: Öffnet sich bei Klick als Chat/Voice-Interface.

### 2. User Interface & Branding

- **D-03:** Hybrid-Mode: Unterstützung von Text-Historie (Transkription) parallel zu Voice-Interaktion (Waveforms).
- **D-04:** Status-Indikatoren: Visuelle Rückmeldung über Verbindungsstatus und Agenten-Aktivität.
- **D-05:** Dynamic Styling: CSS-Variablen (Primärfarbe, Hintergründe) werden direkt aus `.env` (z.B. `WIDGET_PRIMARY_COLOR`) gespeist für maximales White-Labeling.

### 3. Verbindungs-Logik (Guest Access)

- **D-06:** Server-side Token: Absolutes Verbot von Client-side Token-Generierung. Implementierung einer Next.js API-Route (z.B. `/api/token`), die das `LIVEKIT_API_SECRET` sicher hält.
- **D-07:** Gast-Zugang: Das Widget generiert über die API-Route einen Token für einen anonymen Gast-User.

### 4. Interaktions-Modus

- **D-08:** Initialer Connect: Expliziter "Start/Connect"-Knopf im geöffneten Widget (notwendig für Browser-Audio-Context & Mic-Permissions).
- **D-09:** Voice-First: Nach Verbindungsaufbau startet direkt der VAD (Voice Activity Detection) Modus.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### LiveKit Documentation (via MCP)

- `https://docs.livekit.io/realtime/quickstart/nextjs/` — Next.js integration guide
- `https://docs.livekit.io/agents/quickstart/tokens/` — Secure token generation

### Project Internals

- `.planning/phases/01-infrastructure-setup/01-CONTEXT.md` — Infrastructure decisions (Coolify/Env logic)
- `.env.example` — Environment variable definitions

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- Keine — Das Frontend wird neu in `app/` oder `src/` (Next.js App Router) aufgesetzt.

### Integration Points

- `/api/token` — Neue API-Route für Token-Handshake.
- LiveKit Server (Phase 1) — Ziel für WebRTC Signaling.

</code_context>

<specifics>
## Specific Ideas

- Die Text-Historie ist essentiell für Fallbacks in lauten Umgebungen.
- Das Design muss strikt hardware-agnostisch bleiben und ausschließlich über generische CSS-Variablen gesteuert werden.

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)

- None — discussion stayed within phase scope

</deferred>

---

_Phase: 02-frontend-widget_
_Context gathered: 2026-04-18_
