# Phase 1: Infrastructure Setup - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Bereitstellung der Server-Infrastruktur für LiveKit (Self-hosted WebRTC Engine) inkl. Reverse Proxy und TURN-Server-Setup über Docker Compose.
</domain>

<decisions>
## Implementation Decisions

### Basis Setup

- **D-01:** Standard Setup (Single Node) — Ohne Redis. Ausreichend für V1.

### Reverse Proxy & Networking

- **D-02:** Caddy als Standard-Proxy im Stack für das HTTPS-Signaling integrieren.
- **D-03:** LiveKit UDP-Ports direkt auf dem Host binden (Host-Anbindung) für Media-Traffic.
- **D-04:** In der Umgebungskonfiguration dokumentieren, wie Coolify-Nutzer ihren globalen Traefik-Proxy stattdessen direkt anbinden können.

### TURN-Server

- **D-05:** Integrierter LiveKit TURN-Server — Kein separater Coturn-Container.

### Environment Variables

- **D-06:** Zentrale `.env` Struktur. Muss über die Coolify-Variablen-Maske anpassbar sein (keine hartcodierten Secrets in Repo-Dateien).

### Arbeitsweise (Development)

- **D-07:** _Primäre Datenquelle:_ Cursor ist angewiesen, für alle technischen Recherchen und Implementierungsschritte bezüglich LiveKit (Server-Setup, Agent-Worker, Frontend-Hooks) vorrangig das angebundene LiveKit-Dokumentations-MCP zu nutzen. Allgemeine LLM-Kenntnisse dienen nur als Sekundärquelle. (Wird auch in `PROJECT.md` festgehalten).
  </decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above.
</canonical_refs>

<code_context>

## Existing Code Insights

No existing infrastructure code to reuse.
</code_context>

<specifics>
## Specific Ideas

- Coolify-Kompatibilität ist ein wichtiges Kriterium (Traefik-Anbindung dokumentieren, Environment-Variablen-Handling).
  </specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope
</deferred>

---

_Phase: 01-infrastructure-setup_
_Context gathered: 2026-04-18_
