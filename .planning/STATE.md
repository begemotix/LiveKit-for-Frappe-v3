---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: ready
last_updated: "2026-04-19T23:59:00.000Z"
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 24
  completed_plans: 23
---

# Project State

## Project Reference

**Core Value:** Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.
**Current Focus:** Phase 04 — frappe-integration **GAP-CLOSURE COMPLETE**; naechster logischer Schritt: Phase 05 (Persona) nach `/gsd-transition`.

## Current Position

Phase: 04 (frappe-integration) — **COMPLETE** (Gap-Closure inkl. Wave E Live-Evidenz + Wave F Doku-Sync, Plan `04-10-PLAN.md`).
Plan: 10 of 10
**Status:** Phase-4-Freigabe dokumentarisch **GO** — konsistent in `04-VERIFICATION.md`, `04-HUMAN-UAT.md`, `OPERATOR-HANDOVER.md`.
Ausfuehrungslogik (verbindlich): `D -> A -> B -> E -> C -> F`.
Wave-/Gate-Plane (Auszug): `04-05-PLAN.md`, `04-06-PLAN.md`, `04-07-PLAN.md`, `04-08-PLAN.md`, `04-09-PLAN.md`, `04-10-PLAN.md`.
Phase 01 (infrastructure-setup): **COMPLETE** — Realstack-Dokumentation formalisiert durch Plan `01-03` (Gap-Closure).

```
Progress (Project):
[███████   ] 70%
```

## Performance Metrics

- Phases Completed: 4/5 (Phase 4 frappe-integration dokumentarisch abgeschlossen)
- Plans Completed: 23/24 (inkl. `04-10-PLAN.md`)
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
- [Phase 04]: MCP-Credentials fuer den dokumentierten stdio-Sidecar-Pfad: `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` (konsistent mit UAT/Handover/Verification; kein Runtime-Switch).
- [Phase 04]: Missing MCP credentials fail fast with ValueError naming each missing ENV key.
- [Phase 04]: MCP wiring stays session-scoped through build_frappe_mcp_server() in AgentSession.
- [Phase 04]: Disconnect cleanup tolerates callback ordering by treating <=1 participants as terminal for one-shot MCP shutdown.
- [Phase 04]: Permission-Fehler werden zentral erkannt und ohne Retry auf eine feste nutzerfreundliche Antwort gemappt.
- [Phase 04]: Phase-04-Handover bleibt auf MCP-Core begrenzt; Prompting-Migration bleibt in Phase 5 (Decision D-A).
- [Phase 04]: Use livekit-agents MCP extras in both uv and pip dependency contracts to prevent pre-session import failures.
- [Phase 04]: Track live UAT checks as retest-required-unblocked after dependency blocker removal.
- [Phase 04]: Hardening-Gate eingefuehrt: kein Execute/Testing vor dokumentierten Betriebsfakten (Session-Grenze, Endpoint, Tool-Inventar).
- [Phase 04]: Verbindliche Wave-Reihenfolge festgelegt: D (blockierend) -> A -> B -> E -> C -> F.
- [Phase 04]: Wave D wird als freigegeben behandelt, sobald das Human-Verify-Signal approved-wave-d vorliegt.
- [Phase 04]: Folgeschritte 04-06 bis 04-10 bleiben formal an die dokumentierte Reihenfolge D -> A -> B -> E -> C -> F gekoppelt.
- [Phase 04]: INTG-01/INTG-02 are tied to explicit Wave-A UAT evidence for stdio-sidecar and ENV-only credentials.
- [Phase 04]: Verification now repeats architecture guardrails explicitly to prevent drift in follow-up waves.
- [Phase 04]: Wave-B-Abschluss verlangt konsistente room-basierte Session-Grenze in UAT und Verification mit Referenzkette bis OPERATOR-HANDOVER.
- [Phase 04]: Scope-Guardrails bleiben unveraendert: stdio-sidecar, kein HTTP Agent-zu-MCP, keine lokale Bridge, kein REST-Fallback, keine lokale Tool-Allowlist.
- [Phase 04]: INTG-04 wird erst nach freigegebenem Wave-E-Live-Nachweis auf GO gesetzt (Signal approved-wave-e).
- [Phase 04]: INTG-05 bleibt bis Wave C (Plan 04-08) ausstehend und wird nicht in Wave E abgeschlossen.
- [Phase 04]: 403-Fehlerpfad bleibt als produktives Verhalten mit identischer Voice/Text-Botschaft dokumentiert.
- [Phase 04]: INTG-05 wird nur per referenzierter Wave-C-Live-Evidenz auf GO gesetzt.
- [Phase 04]: Wave F (Plan `04-10-PLAN.md`) synchronisiert OPERATOR-HANDOVER, `04-VERIFICATION.md`, `04-HUMAN-UAT.md` mit finalem GO und Wave-Reihenfolge `D -> A -> B -> E -> C -> F`.

### Blockers

- Keine aktiven Phase-4-Blocker; Live-Gates (`approved-wave-d`, `approved-wave-e`) und Wave-C-403-Nachweis sind in UAT/Verification referenziert.
- **Scope Risk Guard:** Phase-5-Entscheidungen D-11 bis D-15 bleiben bis `/gsd-transition` nach Phase 5 out of scope fuer Integrationsphase.

### Next Steps

- Optional: `/gsd-transition` nach Freigabe durch Mensch — Phase 5 (Frappe-Persona) starten.
- Betrieb: Checkliste in `OPERATOR-HANDOVER.md` fuer Kunden-Onboarding abarbeiten.

## Session Continuity

- **Last Action:** Plan `04-10-PLAN.md` (Wave F) — STATE/Roadmap und Abschlussartefakte auf GO synchronisiert.
- **Current Goal:** Phase 4 dokumentarisch abgeschlossen; Transition-Vorbereitung Phase 5.
- **Resume File:** None
