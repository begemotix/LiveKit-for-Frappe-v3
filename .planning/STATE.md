---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-04-19T16:53:19.595Z"
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 18
  completed_plans: 17
---

# Project State

## Project Reference

**Core Value:** Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.
**Current Focus:** Phase 04 — frappe-integration

## Current Position

Phase: 04 (frappe-integration) — EXECUTING
Plan: 2 of 4
**Status:** Ready to execute
Phase 01 (infrastructure-setup): **COMPLETE** — Realstack-Dokumentation formalisiert durch Plan `01-03` (Gap-Closure).

```
Progress (Project):
[██████    ] 60%
```

## Performance Metrics

- Phases Completed: 3/4
- Plans Completed: 13/14
- Requirements Mapped: 16/16
- Known Bugs: 0

## Accumulated Context

### Decisions

- Phase boundaries follow the recommended separation of concerns: Infrastructure -> Frontend -> Agent -> Integration.
- 100% of v1 requirements have been successfully mapped to the 4 phases.
- [Phase 01]: Integrated TURN server used for connectivity without external dependencies
- [Phase 01]: Redis omitted to simplify single-node setup
- [Phase 01-infrastructure-setup]: Explicit port mapping used in docker-compose for standard compatibility
- [Phase 01-infrastructure-setup]: Caddy remains optional via profile; production default is Coolify-Traefik.
- [Phase 01]: Realer Produktivstack nutzt Coolify-Traefik + host.docker.internal-Wiring (formalisiert in Plan 01-03).
- [Phase 02]: Consolidate UI components in components/ui to match shadcn standard while keeping template compatibility.
- [Phase 02-frontend-widget]: D-06: Tokens werden ausschließlich serverseitig über /api/token generiert.
- [Phase 02-frontend-widget]: D-07: Gast-Identitäten werden zufällig generiert, um unauthentifizierten Zugang zu ermöglichen.
- [Phase 02-frontend-widget]: D-05: Branding via CSS variables and environment variables implemented.
- [Phase 02]: Migrated branding injection logic from orphaned layout.tsx to components/root-layout.tsx
- [Phase 03]: D-01: Dynamische Persona-Konfiguration via ENV
- [Phase 03]: D-02: DSGVO-Ansage als separater ENV
- [Phase 03]: D-03: Filler Prompt-Trick
- [Phase 03]: D-04: on_function_call_start Hook + Mock-Tool
- [Phase 03]: D-05: Sofort-Stopp bei Interrupt
- [Phase 03]: D-06: VAD via ENV
- [Phase 03]: D-07: Participant-Trigger
- [Phase 03]: D-08: ENV-Katalog + Markdown-Doku
- [Phase 03]: D-09: Strukturiertes JSON-Logging
- [Phase 03]: D-10: Korrelations-ID aus Room-Name
- [Phase 03-agent-core]: Added pytest-asyncio to enable asynchronous testing of the LiveKit agent.
- [Architektur]: D-A angepasst: Agent-Prompts bleiben in Phase 4 unveraendert (Phase-3-Stand via Python-Konstanten/ENV); Notes-basierte Prompt-Verwaltung wurde auf Phase 5 verschoben.
- [Architektur]: D-B: DSGVO-Ansagen liegen nicht auf LiveKit/Agent-Ebene; Telefon via Zadarma, Browser-Hinweis später im Frontend, `NEXT_PUBLIC_GDPR_NOTICE` bleibt mit leerem Default.
- [Architektur]: D-C: Reverse-Proxy im Produktivpfad ist Coolify-Traefik; Caddy bleibt nur optional auskommentiert für Nicht-Coolify-Deployments.
- [Phase 03]: CP-Abschluss erfordert eigene SUMMARY-Artefakte fuer konsistente Planzaehlung.
- [Phase 03]: Interruption-Tests validieren gegen beobachtbares Verhalten (generate_reply) statt veralteter API-Mocks.
- [Phase 04]: MCP credentials are read exclusively from FRAPPE_MCP_URL, FRAPPE_API_KEY, and FRAPPE_API_SECRET.
- [Phase 04]: Missing MCP credentials fail fast with ValueError naming each missing ENV key.
- [Phase 04]: MCP wiring stays session-scoped through build_frappe_mcp_server() in AgentSession.
- [Phase 04]: Disconnect cleanup tolerates callback ordering by treating <=1 participants as terminal for one-shot MCP shutdown.
- [Phase 04]: Permission-Fehler werden zentral erkannt und ohne Retry auf eine feste nutzerfreundliche Antwort gemappt.
- [Phase 04]: Phase-04-Handover bleibt auf MCP-Core begrenzt; Prompting-Migration bleibt in Phase 5 (Decision D-A).
- [Phase 04]: Use livekit-agents MCP extras in both uv and pip dependency contracts to prevent pre-session import failures.
- [Phase 04]: Track live UAT checks as retest-required-unblocked after dependency blocker removal.

### Blockers

- None currently.

### Next Steps

- Execute Phase 04 (frappe-integration) mit MCP-Core-Scope.
- Start discuss/planning fuer Phase 05 (frappe-basierte Persona-Verwaltung).

## Session Continuity

- **Last Action:** Scopedown von Phase 04 auf MCP-Core und Anlage von Phase 05 fuer Persona-Verwaltung.
- **Current Goal:** Execute Phase 04 plans (MCP connection, discovery, permission handling).
- **Resume File:** None
