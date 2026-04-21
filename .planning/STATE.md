---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: verifying
last_updated: "2026-04-21T07:51:27.085Z"
progress:
  total_phases: 7
  completed_phases: 4
  total_plans: 26
  completed_plans: 25
---

# Project State

## Project Reference

**Core Value:** Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.
**Current Focus:** Phase 05 — eu-voice-agent-typ-b

## Current Position

Phase: 05 (eu-voice-agent-typ-b) — EXECUTING
Phase 04 (frappe-integration): **TRANSITIONED / CLOSED** — Live-Betrieb bestaetigt (stdio-MCP, `MCPToolset`, Voice+E2E gegen Frappe).

Plan: 2 of 2
**Status:** Phase complete — ready for verification
Ausfuehrungslogik (verbindlich): `D -> A -> B -> E -> C -> F`.
Wave-/Gate-Plane (Auszug): `04-05-PLAN.md`, `04-06-PLAN.md`, `04-07-PLAN.md`, `04-08-PLAN.md`, `04-09-PLAN.md`, `04-10-PLAN.md`.
Phase 01 (infrastructure-setup): **COMPLETE** — Realstack-Dokumentation formalisiert durch Plan `01-03` (Gap-Closure).

```
Progress (Project):
[████████░░] 57%   (4 von 7 Phasen abgeschlossen; Phase 5 aktiv)
```

## Performance Metrics

| Run | Duration | Tasks | Files |
| --- | --- | --- | --- |
| Phase 04 P10 | 12min | 2 tasks | 6 files |

- Phases Completed (manuell): **4/7** — Phase 04 inkl. Live-Verifikation abgeschlossen; **Phase 05 gestartet**
- Requirements: INTG-01 bis INTG-05 laut REQUIREMENTS.md complete

| Phase 05 P01 | 0h 12m | 2 tasks | 7 files |
| Phase 05-eu-voice-agent-typ-b P02 | 24min | 2 tasks | 4 files |

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
- [Phase 04]: **Verbindliche Transport-Entscheidung Frappe:** Produktiv ist ausschliesslich **stdio** ueber `MCPServerStdio` mit lokalem `npx -y frappe-mcp-server` (gleiches Muster wie funktionierendes Cursor-`bgx-frappe`). **Keine** Basisannahme mehr, dass der Agent Frappe-MCP per **HTTP/SSE oder Site-Root-Pfad `/mcp`** anbindet; `FRAPPE_URL` + `FRAPPE_API_KEY` + `FRAPPE_API_SECRET` sind der ENV-Vertrag (optionaler Legacy-Fallback nur fuer Ableitung der Basis-URL aus `FRAPPE_MCP_URL` im Code, bevorzugt ist `FRAPPE_URL`).
- [Phase 04]: MCP-Credentials fuer den dokumentierten stdio-Sidecar-Pfad: `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` (konsistent mit UAT/Handover/Verification; kein Runtime-Switch).
- [Phase 04]: Missing MCP credentials fail fast with ValueError naming each missing ENV key.
- [Phase 04]: MCP wiring session-scoped: `build_frappe_mcp_server()` + `MCPToolset` als `AgentSession(tools=[...])` (deprecated `mcp_servers` entfernt).
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
- [Phase 04]: Wave F: Phase-4-Gap-Closure dokumentarisch GO; Artefakte synchronisiert.
- [Phase 04]: Verbindliche Ausfuehrungsreihenfolge D -> A -> B -> E -> C -> F in Handover, UAT, Verification, STATE.
- [GSD 2026-04-21]: **`/gsd-transition`** ausgefuehrt — Phase 04 **closed**, Phase 05 **active**; `completed_phases: 4`, `completed_plans` auf aktuellen Ist-Stand 24/24 gesetzt.
- [Phase 05]: AGENT_MODE resolves deterministically to type_b when unset.
- [Phase 05]: No silent fallback from type_b to type_a is implemented.
- [Phase 05]: Voice config prioritizes AGENT_VOICE_REF_AUDIO over AGENT_VOICE_ID.
- [Phase 05-eu-voice-agent-typ-b]: Entrypoint resolved AGENT_MODE before session startup and uses factory pipeline wiring with voice-eu identity for type_b.
- [Phase 05-eu-voice-agent-typ-b]: Type-B provider failures are hard-fail only; tests explicitly prevent fallback to type_a.

### Blockers

- Keine aktiven Phase-4-Blocker; Live-Gates (`approved-wave-d`, `approved-wave-e`) und Wave-C-403-Nachweis sind in UAT/Verification referenziert.
- **Scope Risk Guard:** Phase-5-Entscheidungen **D-11 bis D-15** sind jetzt **im Scope von Phase 05** (nicht mehr Integrations-Backlog).

### Next Steps

- Phase 05: `.planning/phases/05-eu-voice-agent/` anlegen (mindestens `05-CONTEXT.md`, Requirements aus ROADMAP schärfen).
- Ersten Plan skizzieren (`/gsd-discuss-phase` oder `/gsd-plan-phase` je nach Workflow).
- Betrieb: Checkliste in `OPERATOR-HANDOVER.md` fuer Kunden-Onboarding weiter nutzen.

## Session Continuity

- **Last Action:** Architektur-Pivot umgesetzt — Fokus auf **Phase 05 (EU-Voice-Agent Typ B)** verschoben; `STATE`/`ROADMAP`/`PROJECT` synchronisiert.
- **Current Goal:** Phase-5-Anforderungen und erste Plaene (Mistral + Voxtral STT/TTS Integration) ausarbeiten.
- **Resume File:** None
