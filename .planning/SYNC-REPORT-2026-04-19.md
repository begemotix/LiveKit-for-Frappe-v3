# SYNC-REPORT-2026-04-19

## A. Top-Level Struktur
```bash
ls -la
```
```text
    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          18.04.2026    12:58                .cursor
d----          18.04.2026    16:25                .github
d----          18.04.2026    17:51                .planning
d----          18.04.2026    19:11                apps
d----          19.04.2026    12:14                infrastructure
d----          19.04.2026    15:15                readme
-a---          19.04.2026    11:58            577 .env.example
-a---          19.04.2026    13:08            665 .gitignore
-a---          18.04.2026    16:23             78 Caddyfile
-a---          19.04.2026    15:13           2583 docker-compose.yml
-a---          18.04.2026    16:25           5230 README.md
-a---          18.04.2026    18:59           8337 REPO_TRIAGE_PHASENLISTE.md
-a---          18.04.2026    18:41           6350 REPO_TRIAGE_STUFE1.md
```

```bash
ls -1 | wc -l
```
```text
13
```

## B. Verzeichnis-Tree (2 Ebenen, ohne Müll)
```bash
tree -L 2 -a -I 'node_modules|.next|.git|__pycache__|.venv|venv|dist|build' || find . -maxdepth 2 -not -path '*/node_modules/*' -not -path '*/.next/*' -not -path '*/.git/*' -not -path '*/__pycache__/*'
```
```text
    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          18.04.2026    12:58                .cursor
d----          18.04.2026    16:25                .github
d----          18.04.2026    17:51                .planning
d----          18.04.2026    19:11                apps
d----          19.04.2026    12:14                infrastructure
d----          19.04.2026    15:15                readme

    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3\.cursor

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          18.04.2026    13:44           6462 rules

    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3\.github

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          18.04.2026    16:25                assets
d----          18.04.2026    16:25                workflows

    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3\.planning

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          18.04.2026    16:47                phases
d----          18.04.2026    16:25                research
-a---          18.04.2026    17:51            980 config.json
-a---          18.04.2026    16:25           5340 PROJECT.md
-a---          18.04.2026    17:17           4476 REQUIREMENTS.md
-a---          18.04.2026    17:39           4383 ROADMAP.md
-a---          18.04.2026    17:39           2928 STATE.md

    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3\apps

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
da---          18.04.2026    17:56                agent
d----          19.04.2026    13:11                frontend

    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3\infrastructure

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          18.04.2026    16:25            359 .env.example
-a---          18.04.2026    16:25             78 Caddyfile
-a---          19.04.2026    12:19           1592 docker-compose.yml
-a---          18.04.2026    16:25            619 package.json
-a---          19.04.2026    15:15           1313 README.md

    Directory: C:\Users\schwa\Documents\LiveKit for Frappe v3\readme

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          19.04.2026    15:21           1920 AGENT_PROMPT.md
-a---          19.04.2026    15:15           5228 COOLIFY-KONFIGURATION.md
-a---          19.04.2026    15:12           1832 SCHULUNG_GUIDE.md
```

## C. GSD-State
- Vollständiger Inhalt von `.planning/STATE.md`.
```markdown
---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-04-18T15:17:49.774Z"
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 12
  completed_plans: 11
---

# Project State

## Project Reference

**Core Value:** Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.
**Current Focus:** Phase 03 — agent-core

## Current Position

Phase: 03 (agent-core) — EXECUTING
Plan: 4 of 4
**Status:** Ready to execute

```
Progress (Project):
[██▌       ] 25%
```

## Performance Metrics

- Phases Completed: 2/4
- Plans Completed: 11/12
- Requirements Mapped: 16/16
- Known Bugs: 0

## Accumulated Context

### Decisions

- Phase boundaries follow the recommended separation of concerns: Infrastructure -> Frontend -> Agent -> Integration.
- 100% of v1 requirements have been successfully mapped to the 4 phases.
- [Phase 01]: Integrated TURN server used for connectivity without external dependencies
- [Phase 01]: Redis omitted to simplify single-node setup
- [Phase 01-infrastructure-setup]: Explicit port mapping used in docker-compose for standard compatibility
- [Phase 01-infrastructure-setup]: Caddy selected for automatic Let's Encrypt certificates and simplicity
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

### Blockers

- None currently.

### Next Steps

- Complete Phase 03 (agent-core): Plan 03 pending.

## Session Continuity

- **Last Action:** Completed Phase 03 Plans 00-02 (agent foundation, core logic, server VAD).
- **Current Goal:** Execute Plan 03 (tests + white-label docs) after gap-closure.
- **Resume File:** .planning/phases/03-agent-core/03-CP-PLAN.md
```

- Vollständiger Inhalt von `.planning/ROADMAP.md`.
```markdown
# Project Roadmap

## Phases

- [x] **Phase 1: Infrastructure Setup** - Self-hosted LiveKit WebRTC engine and proxy deployment
      (completed 2026-04-18)
- [ ] **Phase 2: Frontend Widget** - Next.js voice widget mit unauthentifiziertem Gast-Token
- [ ] **Phase 3: Agent Core** - Low-latency OpenAI Realtime voice agent with interruption handling
- [ ] **Phase 4: Frappe Integration** - Secure MCP connection for read-only Frappe data access

## Phase Details

### Phase 1: Infrastructure Setup

**Goal**: The self-hosted LiveKit WebRTC engine is running and accessible securely
**Depends on**: None
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04
**Success Criteria** (what must be TRUE):

1. Administrator can deploy the LiveKit server and Caddy proxy via Docker Compose
2. WebRTC connections can be established from external networks (via TURN/STUN)
3. The server is accessible via HTTPS using an automatically provisioned Let's Encrypt certificate
   **Plans:** 2/2 plans complete
   Plans:

- [x] 01-01-PLAN.md — Create the base LiveKit configuration and environment structure.
- [x] 01-02-PLAN.md — Create the Docker Compose and Reverse Proxy setup for deployment.

### Phase 2: Frontend Widget

**Goal**: Users can initiate a voice connection to the LiveKit server from their browser
**Depends on**: Phase 1
**Requirements**: WIDG-01, WIDG-02, WIDG-03
**Success Criteria** (what must be TRUE):

1. User sees a floating voice/text widget in their browser
2. User can click the widget to successfully establish a WebRTC connection to the local LiveKit server
3. Das Widget generiert einen unauthentifizierten Gast-Token, um dem Raum beizutreten (Nutzer ist ein anonymer Gast im LiveKit-Kontext)
   **Plans**: 6 plans
   **UI hint**: yes
   Plans:

- [x] 02-01-PLAN.md — Setup Next.js, shadcn/ui and LiveKit SDKs.
- [x] 02-02-PLAN.md — Implement secure Token API and Room Provider.
- [x] 02-03-PLAN.md — Build Floating Action Button and Chat Panel UI.
- [x] 02-04-PLAN.md — Integrate LiveKit WebRTC and Voice Visualizer.
- [x] 02-05-PLAN.md — Finalize Dynamic Styling and Phase Verification.
- [x] 02-06-PLAN.md — Gap Closure: Dynamic Branding Injection.

### Phase 3: Agent Core

**Goal**: Users can converse naturally with a voice agent that responds with low latency
**Depends on**: Phase 2
**Requirements**: AGNT-01, AGNT-02, AGNT-03, AGNT-04
**Success Criteria** (what must be TRUE):

1. User can speak to the agent and hear AI-generated spoken responses with minimal delay
2. User can interrupt the agent while it is speaking, and the agent stops and listens
3. User hears "filler audio" when the agent is thinking for a long time to prevent dead air
   **Plans**: 4 plans
   Plans:

- [x] 03-00-PLAN.md — Initialize the testing infrastructure and framework.
- [x] 03-01-PLAN.md — Setup the foundation for the Python Agent Worker and configuration interface.
- [x] 03-02-PLAN.md — Implement the core voice agent logic using OpenAI Realtime and LiveKit.
- [ ] 03-03-PLAN.md — Verify the implementation through automated tests and partner documentation.

### Phase 4: Frappe Integration

**Goal**: The voice agent connects to Frappe using its own dedicated credentials and securely relays read-only data
**Depends on**: Phase 3
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04, INTG-05
**Success Criteria** (what must be TRUE):

1. The agent connects to the Frappe MCP server and dynamically discovers available read-only tools
2. The agent successfully authenticates its MCP requests using its own fixed credentials (e.g. API-Key from .env)
3. User can ask the agent about Frappe data, and the agent retrieves and speaks information accessible to the agent user
4. If the agent asks for data it lacks permissions for, it gracefully informs the user of the restriction instead of crashing
   **Plans**: TBD

## Progress

| Phase                   | Plans Complete | Status      | Completed  |
| ----------------------- | -------------- | ----------- | ---------- |
| 1. Infrastructure Setup | 2/2            | Complete    | 2026-04-18 |
| 2. Frontend Widget      | 6/6            | Complete    | 2026-04-18 |
| 3. Agent Core           | 3/4            | In Progress | -          |
| 4. Frappe Integration   | 0/TBD          | Not started | -          |
```

- Liste aller SUMMARY-Dateien mit jeweils letztem Commit:
```bash
for f in .planning/phases/*/*-SUMMARY.md; do echo "=== $f ==="; git log -1 --format="%h %ai %s" -- "$f"; done
```
```text
=== .planning\phases\01-infrastructure-setup\01-01-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning\phases\01-infrastructure-setup\01-02-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning\phases\02-frontend-widget\02-01-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning\phases\02-frontend-widget\02-02-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning\phases\02-frontend-widget\02-03-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning\phases\02-frontend-widget\02-04-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning\phases\02-frontend-widget\02-05-SUMMARY.md ===
e69b5df 2026-04-18 16:13:56 +0200 docs(02-05): complete branding and phase 02 verification
=== .planning\phases\02-frontend-widget\02-06-SUMMARY.md ===
8dc8c0e 2026-04-18 16:19:21 +0200 docs(02-06): complete dynamic branding injection plan
=== .planning\phases\03-agent-core\03-00-SUMMARY.md ===
33ec3f8 2026-04-18 17:40:47 +0200 fix(phase-3): gap-closure CP — session.start await, fallback consistency, test imports, docs drift.
=== .planning\phases\03-agent-core\03-01-SUMMARY.md ===
33ec3f8 2026-04-18 17:40:47 +0200 fix(phase-3): gap-closure CP — session.start await, fallback consistency, test imports, docs drift.
=== .planning\phases\03-agent-core\03-02-SUMMARY.md ===
70727c2 2026-04-18 17:17:53 +0200 docs(03-02): complete core agent logic implementation
=== .planning\phases\03-agent-core\03-03-SUMMARY.md ===
0b66829 2026-04-18 19:00:16 +0200 triage begin
```

## D. Was tatsächlich deployt ist
kein Server-Zugang verfügbar
```bash
find . -name "docker-compose*.yml" -not -path "*/node_modules/*"
```
```text
docker-compose.yml
infrastructure/docker-compose.yml
```

## E. Code-Deviations und Stubs
```bash
git grep -n "TODO\|FIXME\|STUB\|Wave 0\|auto-fixed\|deviation\|HACK\|XXX" -- ':!node_modules' ':!.next' ':!.planning/research' || true
```
```text
.planning/phases/02-frontend-widget/02-01-PLAN.md:36:      provides: 'Wave 0 Test-Stub für Widget'
.planning/phases/02-frontend-widget/02-01-PLAN.md:38:      provides: 'Wave 0 Test-Stub für API-Token'
.planning/phases/02-frontend-widget/02-01-PLAN.md:69:  <name>Task 0: Erstellung der Test-Stubs (Wave 0)</name>
.planning/phases/02-frontend-widget/02-01-PLAN.md:84:  <done>Wave 0 Test-Stubs sind erstellt.</done>
.planning/phases/02-frontend-widget/02-01-PLAN.md:130:  <name>Task 3: Test-Infrastruktur Setup (Vitest) & Wave 0 Stubs</name>
.planning/phases/02-frontend-widget/02-01-PLAN.md:134:    Einrichtung von Vitest und Erstellung der Wave 0 Test-Stubs laut VALIDATION.md.
.planning/phases/02-frontend-widget/02-01-PLAN.md:139:    5. Erstellung von `tests/widget.test.tsx` und `tests/api-token.test.ts` mit Platzhalter-Tests (Nyquist Wave 0).
.planning/phases/02-frontend-widget/02-01-SUMMARY.md:64:- `tests/widget.test.tsx`: Wave 0 Test-Stub (Nyquist Anforderung).
.planning/phases/02-frontend-widget/02-01-SUMMARY.md:65:- `tests/api-token.test.ts`: Wave 0 Test-Stub (Nyquist Anforderung).
.planning/phases/03-agent-core/03-00-SUMMARY.md:34:- Created `apps/agent/tests/test_agent.py` with test stubs for `test_join`, `test_interruption`, `test_mock_tool`, `test_persona_injection`. Note: Test stubs were later extended into full implementations during Plan 01/02 execution, documented here as deviation.
.planning/phases/03-agent-core/03-01-SUMMARY.md:46:- Additional deviation: test_agent.py was expanded from stubs to full implementations during this wave, which was Plan 03 Task 1 scope. This anticipation is explicitly noted so Plan 03 Task 1 becomes 'audit and complete' instead of 'write from scratch'.
.planning/phases/03-agent-core/03-03-PLAN.md:52:    Update `apps/agent/tests/test_agent.py` (stubs created in Wave 0).
apps/frontend/components/embed-iframe/session-view.tsx:44:    // FIXME: how do I explicitly ensure only the microphone channel is used?
apps/frontend/components/embed-iframe/session-view.tsx:142:              {/* FIXME: do I need to handle the other channels here? */}
apps/frontend/components/embed-popup/standalone-bundle-root.tsx:21:  // FIXME: this includes styles for the welcome page / etc, not just the popup embed!
```

## F. Plan-vs-Reality Diff
```bash
git log --oneline -30
```
```text
1e5096e 3rd popup deletion
c0ae0ec chatpopup
5f6bcf0 fix(frontend): resolve linting and dependency errors in ChatPanel
70b2f18 docs: move COOLIFY-KONFIGURATION.md to readme/ directory
fac7319 feat(agent): implement markdown-based training via readme/AGENT_PROMPT.md with volume mount
5ae49f6 refactor(agent): use native generate_reply for greetings instead of separate TTS plugin
10d4db8 docs: add NEXT_PUBLIC_GDPR_NOTICE to configuration guide
ac54031 feat(agent,frontend): implement GDPR-compliant start and restore agent greetings
099fc64 fix(agent): remove cloud-tts based announcements for GDPR compliance
6dae097 docs: lock in verified working variables in COOLIFY-KONFIGURATION.md
bbb1f38 docs: finalize coolify configuration with verified host.docker.internal wiring
d009e6a refactor(infra): remove hardcoded IPs and use host.docker.internal for universal wiring
14d86d3 fix(infra): separate internal and external LiveKit URLs for browser connectivity
a5c5ee4 refactor(infra): switch to hybrid wired stack (LiveKit Host, Agent/Frontend Bridge) for SSL stability
b1098b0 refactor(infra): switch to hybrid host/bridge networking for performance and SSL
5840f64 refactor(infra): switch stack to bridge networking for universal SSL support and multi-tenancy
45eac35 fix(frontend): remove network_mode: host to allow traefik ssl routing
259b05d fix(agent): use dynamic port for worker to prevent bind conflicts
8b26c66 fix: resolve remaining typescript errors
d2d5677 fix(frontend): restore package and tsconfig properly
bd0de84 Revert "fix(frontend): resolve ts/lint errors and webpack script path"
b82377a chore: fix .gitignore to correctly ignore nested node_modules and .next directories
7fb443d fix(frontend): resolve ts/lint errors and webpack script path
7276272 fix(deploy): restore official pnpm setup from templates and generate lockfile
efec7b3 fix(deploy): switch frontend from pnpm to npm to resolve deployment failures
260b42b fix(deploy): fix frontend build by adding pnpm to Docker and correcting path aliases
4a91fa7 fix(deploy): optimize Dockerfiles for Coolify build process
92783f5 feat(deploy): unified multi-container stack with frontend and agent
3636727 fix(deploy): remove invalid 'bind' field from livekit config-body
46cb552 fix(deploy): use --config-body in docker-compose to avoid volume mount issues in Coolify
```

Letzten Commit von Phase 2 finden und gegen HEAD diffen:
```bash
git diff --name-status $(git log --grep="02-06" --format=%H -1)..HEAD
```
```text
M	.planning/STATE.md
M	.planning/phases/03-00-SUMMARY.md
M	.planning/phases/03-01-SUMMARY.md
M	apps/agent/main.py
M	apps/agent/tests/test_agent.py
M	apps/frontend/package.json
M	docker-compose.yml
M	infrastructure/docker-compose.yml
A	readme/AGENT_PROMPT.md
A	readme/COOLIFY-KONFIGURATION.md
A	readme/SCHULUNG_GUIDE.md
```

## G. Repo-Hygiene-Check (gegen die Phase-2-Katastrophen-Muster)
```bash
git ls-files | grep -E "^(HEAD|packed-refs|pre-commit\.sample|ORIG_HEAD|FETCH_HEAD|index)$" || echo "CLEAN: keine git internals tracked"
```
```text
CLEAN: keine git internals tracked
```

```bash
find . -maxdepth 2 -name "docker-compose*.yml" -not -path "*/node_modules/*"
find . -maxdepth 2 -name "Caddyfile" -not -path "*/node_modules/*"
find . -maxdepth 3 -name "package.json" -not -path "*/node_modules/*"
```
```text
docker-compose.yml
infrastructure/docker-compose.yml
Caddyfile
infrastructure/Caddyfile
apps/frontend/package.json
infrastructure/package.json
```

## H. Funktional verifizierter Stand
Bekannt verifiziert (vom User in dieser Session bestätigt):
- Voice-Loop Browser ↔ Agent auf live.begemotix.cloud ist sprechbar.

Ungeklärt:
- Alles andere.

## I. Bekanntes Offenes
- MCP-Verbindung zu begemotix.pro: unklar
- Frappe-Auth-Passthrough: unklar
- Filler-Audio gegen Dead Air: unklar
- Interruption-Handling getestet: unklar
- Welche Phase 3 Plans wurden ausgeführt: Phase 3 Plans 00, 01, 02 abgeschlossen. Plan 03 (Tests & Doku) offen.
