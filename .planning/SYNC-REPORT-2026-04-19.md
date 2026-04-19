# SYNC-REPORT-2026-04-19

## A. Top-Level Struktur

```bash
ls -la
ls -1 | wc -l
```

```
total 125
drwxr-xr-x 1 schwa 197609    0 Apr 19 16:12 .
drwxr-xr-x 1 schwa 197609    0 Apr 18 12:45 ..
drwxr-xr-x 1 schwa 197609    0 Apr 18 12:58 .cursor
-rw-r--r-- 1 schwa 197609  577 Apr 19 11:58 .env.example
drwxr-xr-x 1 schwa 197609    0 Apr 19 16:12 .git
drwxr-xr-x 1 schwa 197609    0 Apr 18 16:25 .github
-rw-r--r-- 1 schwa 197609  665 Apr 19 13:08 .gitignore
drwxr-xr-x 1 schwa 197609    0 Apr 19 16:15 .planning
drwxr-xr-x 1 schwa 197609    0 Apr 18 19:11 apps
-rw-r--r-- 1 schwa 197609   78 Apr 18 16:23 Caddyfile
-rw-r--r-- 1 schwa 197609 2583 Apr 19 15:13 docker-compose.yml
drwxr-xr-x 1 schwa 197609    0 Apr 19 12:14 infrastructure
drwxr-xr-x 1 schwa 197609    0 Apr 19 15:15 readme
-rw-r--r-- 1 schwa 197609 5230 Apr 18 16:25 README.md
-rw-r--r-- 1 schwa 197609 8337 Apr 19 16:12 REPO_TRIAGE_PHASENLISTE.md
-rw-r--r-- 1 schwa 197609 6350 Apr 19 16:12 REPO_TRIAGE_STUFE1.md
8
```

## B. Verzeichnis-Tree (2 Ebenen, ohne Müll)

```bash
tree -L 2 -a -I 'node_modules|.next|.git|__pycache__|.venv|venv|dist|build' || find . -maxdepth 2 -not -path '*/node_modules/*' -not -path '*/.next/*' -not -path '*/.git/*' -not -path '*/__pycache__/*'
```

```
.
./.cursor
./.cursor/rules
./.env.example
./.git
./.github
./.github/assets
./.github/workflows
./.gitignore
./.planning
./.planning/config.json
./.planning/phases
./.planning/PROJECT.md
./.planning/REQUIREMENTS.md
./.planning/research
./.planning/ROADMAP.md
./.planning/STATE.md
./.planning/_build_sync_report.py
./.planning/_diff_name_status.txt
./apps
./apps/agent
./apps/frontend
./Caddyfile
./docker-compose.yml
./infrastructure
./infrastructure/.env.example
./infrastructure/Caddyfile
./infrastructure/docker-compose.yml
./infrastructure/package.json
./infrastructure/README.md
./readme
./readme/AGENT_PROMPT.md
./readme/COOLIFY-KONFIGURATION.md
./readme/SCHULUNG_GUIDE.md
./README.md
./REPO_TRIAGE_PHASENLISTE.md
./REPO_TRIAGE_STUFE1.md
/usr/bin/bash: line 1: tree: command not found
```

## C. GSD-State

### `.planning/STATE.md` (vollständig)

```
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

### `.planning/ROADMAP.md` (vollständig)

```
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

### SUMMARY-Dateien mit letztem Commit

```bash
for f in .planning/phases/*/*-SUMMARY.md; do echo "=== $f ==="; git log -1 --format="%h %ai %s" -- "$f"; done
```

```
=== .planning/phases/01-infrastructure-setup/01-01-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning/phases/01-infrastructure-setup/01-02-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning/phases/02-frontend-widget/02-01-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning/phases/02-frontend-widget/02-02-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning/phases/02-frontend-widget/02-03-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning/phases/02-frontend-widget/02-04-SUMMARY.md ===
c272d4c 2026-04-18 16:19:06 +0200 chore(02-06): remove orphaned layout.tsx
=== .planning/phases/02-frontend-widget/02-05-SUMMARY.md ===
e69b5df 2026-04-18 16:13:56 +0200 docs(02-05): complete branding and phase 02 verification
=== .planning/phases/02-frontend-widget/02-06-SUMMARY.md ===
8dc8c0e 2026-04-18 16:19:21 +0200 docs(02-06): complete dynamic branding injection plan
=== .planning/phases/03-agent-core/03-00-SUMMARY.md ===
33ec3f8 2026-04-18 17:40:47 +0200 fix(phase-3): gap-closure CP — session.start await, fallback consistency, test imports, docs drift.
=== .planning/phases/03-agent-core/03-01-SUMMARY.md ===
33ec3f8 2026-04-18 17:40:47 +0200 fix(phase-3): gap-closure CP — session.start await, fallback consistency, test imports, docs drift.
=== .planning/phases/03-agent-core/03-02-SUMMARY.md ===
70727c2 2026-04-18 17:17:53 +0200 docs(03-02): complete core agent logic implementation
=== .planning/phases/03-agent-core/03-03-SUMMARY.md ===
0b66829 2026-04-18 19:00:16 +0200 triage begin
```

## D. Was tatsächlich deployt ist

kein Server-Zugang verfügbar (lokal: `docker` nicht im PATH / nicht ausführbar; kein SSH/Coolify-Kontext in dieser Cursor-Session).

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

```
docker: FileNotFoundError: executable not found (docker nicht im PATH / nicht installiert)
```

```bash
find . -name "docker-compose*.yml" -not -path "*/node_modules/*"
```

```
./docker-compose.yml
./infrastructure/docker-compose.yml
```

### `./docker-compose.yml` (vollständig)

```
# LiveKit Stack — Unified Deployment (Host Networking)
# This includes the LiveKit Server, the Python Agent, and the Next.js Frontend.
# network_mode: host is used for optimal WebRTC and internal communication performance.

version: "3.9"

services:
  livekit:
    image: livekit/livekit-server:latest
    restart: unless-stopped
    command:
      - --config-body
      - |
        port: 7880
        log_level: info
        rtc:
          tcp_port: 7881
          port_range_start: 50000
          port_range_end: 50100
          use_external_ip: true
        turn:
          enabled: true
          domain: ${DOMAIN}
          tls_port: 5349
          udp_port: 3478
          external_tls: true
        keys:
          ${LIVEKIT_API_KEY}: ${LIVEKIT_API_SECRET}
    network_mode: host
    env_file:
      - .env
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.livekit.rule=Host(`live.begemotix.cloud`)"
      - "traefik.http.routers.livekit.entrypoints=websecure"
      - "traefik.http.routers.livekit.tls=true"
      - "traefik.http.routers.livekit.tls.certresolver=letsencrypt"
      - "traefik.http.services.livekit.loadbalancer.server.url=http://host.docker.internal:7880"

  agent:
    build:
      context: ./apps/agent
      dockerfile: Dockerfile
    restart: unless-stopped
    # Use bridge mode for the agent, it only needs to reach LiveKit via the gateway
    env_file:
      - .env
    environment:
      - LIVEKIT_URL=ws://host.docker.internal:7880
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./readme:/app/readme:ro
    depends_on:
      - livekit

  frontend:
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_LIVEKIT_URL: ${NEXT_PUBLIC_LIVEKIT_URL}
        NEXT_PUBLIC_APP_CONFIG_ENDPOINT: ${NEXT_PUBLIC_APP_CONFIG_ENDPOINT:-}
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - NEXT_PUBLIC_LIVEKIT_URL=${NEXT_PUBLIC_LIVEKIT_URL}
    # Frontend in bridge mode for Traefik SSL auto-discovery
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - livekit

  caddy:
    profiles:
      - with-caddy
    image: caddy:latest
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    env_file:
      - .env
    depends_on:
      - frontend
      - livekit

volumes:
  caddy_data:
  caddy_config:
```

### `./infrastructure/docker-compose.yml` (vollständig)

```
version: '3.9'

services:
  livekit:
    image: livekit/livekit-server:latest
    container_name: livekit
    restart: unless-stopped
    command:
      - --config-body
      - |
        port: 7880
        log_level: info
        rtc:
          tcp_port: 7881
          port_range_start: 50000
          port_range_end: 60000
          use_external_ip: true
        turn:
          enabled: true
          domain: ${DOMAIN}
          tls_port: 5349
          udp_port: 3478
          external_tls: true
        keys:
          ${LIVEKIT_API_KEY}: ${LIVEKIT_API_SECRET}
    ports:
      - '7880:7880'
      - '7881:7881'
      - '3478:3478/udp'
      - '5349:5349/tcp'
      - '50000-60000:50000-60000/udp'
    env_file:
      - .env

  agent:
    build:
      context: ../apps/agent
      dockerfile: Dockerfile
    container_name: agent
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      - livekit

  frontend:
    build:
      context: ../apps/frontend
      dockerfile: Dockerfile
    container_name: frontend
    restart: unless-stopped
    ports:
      - '3000:3000'
    env_file:
      - .env
    depends_on:
      - livekit

  caddy:
    image: caddy:latest
    container_name: caddy
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    env_file:
      - .env
    depends_on:
      - frontend
      - livekit

volumes:
  caddy_data:
  caddy_config:
```

## E. Code-Deviations und Stubs

```bash
git grep -n "TODO\|FIXME\|STUB\|Wave 0\|auto-fixed\|deviation\|HACK\|XXX" -- ':!node_modules' ':!.next' ':!.planning/research' || true
```

```
.planning/phases/02-frontend-widget/02-01-PLAN.md:36:      provides: 'Wave 0 Test-Stub für Widget'
.planning/phases/02-frontend-widget/02-01-PLAN.md:38:      provides: 'Wave 0 Test-Stub für API-Token'
.planning/phases/02-frontend-widget/02-01-PLAN.md:69:  <name>Task 0: Erstellung der Test-Stubs (Wave 0)</name>
.planning/phases/02-frontend-widget/02-01-PLAN.md:84:  <done>Wave 0 Test-Stubs sind erstellt.</done>
.planning/phases/02-frontend-widget/02-01-PLAN.md:130:  <name>Task 3: Test-Infrastruktur Setup (Vitest) & Wave 0 Stubs</name>
.planning/phases/02-frontend-widget/02-01-PLAN.md:134:    Einrichtung von Vitest und Erstellung der Wave 0 Test-Stubs laut VALIDATION.md.
.planning/phases/02-frontend-widget/02-01-PLAN.md:139:    5. Erstellung von `tests/widget.test.tsx` und `tests/api-token.test.ts` mit Platzhalter-Tests (Nyquist Wave 0).
.planning/phases/02-frontend-widget/02-01-SUMMARY.md:64:- `tests/widget.test.tsx`: Wave 0 Test-Stub (Nyquist Anforderung).
.planning/phases/02-frontend-widget/02-01-SUMMARY.md:65:- `tests/api-token.test.ts`: Wave 0 Test-Stub (Nyquist Anforderung).
.planning/phases/02-frontend-widget/02-RESEARCH.md:207:| WIDG-01 | FAB ist sichtbar und klickbar | Component   | `vitest FloatingButton.test.tsx` | ❌ Wave 0    |
.planning/phases/02-frontend-widget/02-RESEARCH.md:208:| WIDG-02 | Verbindung wird aufgebaut     | Integration | `vitest Connection.test.tsx`     | ❌ Wave 0    |
.planning/phases/02-frontend-widget/02-RESEARCH.md:209:| WIDG-03 | API gibt gültiges JWT zurück  | API         | `vitest api/token.test.ts`       | ❌ Wave 0    |
.planning/phases/02-frontend-widget/02-VALIDATION.md:21:| **Config file**        | {path or "none — Wave 0 installs"} |
.planning/phases/02-frontend-widget/02-VALIDATION.md:49:## Wave 0 Requirements
.planning/phases/02-frontend-widget/02-VALIDATION.md:71:- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
.planning/phases/02-frontend-widget/02-VALIDATION.md:73:- [ ] Wave 0 covers all MISSING references
.planning/phases/03-agent-core/03-00-SUMMARY.md:34:- Created `apps/agent/tests/test_agent.py` with test stubs for `test_join`, `test_interruption`, `test_mock_tool`, `test_persona_injection`. Note: Test stubs were later extended into full implementations during Plan 01/02 execution, documented here as deviation.
.planning/phases/03-agent-core/03-01-SUMMARY.md:46:- Additional deviation: test_agent.py was expanded from stubs to full implementations during this wave, which was Plan 03 Task 1 scope. This anticipation is explicitly noted so Plan 03 Task 1 becomes 'audit and complete' instead of 'write from scratch'.
.planning/phases/03-agent-core/03-03-PLAN.md:52:    Update `apps/agent/tests/test_agent.py` (stubs created in Wave 0).
.planning/phases/03-agent-core/03-CP-PLAN.md:39:   - Extend deviations in `03-01-SUMMARY.md` with explicit scope anticipation note.
.planning/phases/03-agent-core/03-RESEARCH.md:170:| AGNT-01 | Agent tritt Raum bei | Integration | `pytest -k test_join` | ❌ Wave 0 |
.planning/phases/03-agent-core/03-RESEARCH.md:171:| AGNT-03 | Unterbrechung stoppt Audio | Smoke Test | `pytest -k test_interruption` | ❌ Wave 0 |
.planning/phases/03-agent-core/03-RESEARCH.md:172:| AGNT-04 | Mock-Tool wird aufgerufen | Unit | `pytest -k test_mock_tool` | ❌ Wave 0 |
.planning/phases/03-agent-core/03-VALIDATION.md:21:| **Config file** | none — Wave 0 installs |
.planning/phases/03-agent-core/03-VALIDATION.md:53:## Wave 0 Requirements
.planning/phases/03-agent-core/03-VALIDATION.md:71:- [x] All tasks have `<automated>` verify or Wave 0 dependencies
.planning/phases/03-agent-core/03-VALIDATION.md:73:- [x] Wave 0 covers all MISSING references
apps/frontend/components/embed-iframe/session-view.tsx:44:    // FIXME: how do I explicitly ensure only the microphone channel is used?
apps/frontend/components/embed-iframe/session-view.tsx:142:              {/* FIXME: do I need to handle the other channels here? */}
apps/frontend/components/embed-popup/standalone-bundle-root.tsx:21:  // FIXME: this includes styles for the welcome page / etc, not just the popup embed!
```

## F. Plan-vs-Reality Diff

```bash
git log --oneline -30
```

```
3b92e68 docs: sync report for CTO review
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
```

```bash
git diff --name-status $(git log --grep="02-06" --format=%H -1)..HEAD
```

```
M	.env.example
M	.gitignore
M	.planning/REQUIREMENTS.md
M	.planning/ROADMAP.md
M	.planning/STATE.md
A	.planning/SYNC-REPORT-2026-04-19.md
M	.planning/phases/02-frontend-widget/02-VERIFICATION.md
A	.planning/phases/03-agent-core/03-00-PLAN.md
A	.planning/phases/03-agent-core/03-00-SUMMARY.md
A	.planning/phases/03-agent-core/03-01-PLAN.md
A	.planning/phases/03-agent-core/03-01-SUMMARY.md
A	.planning/phases/03-agent-core/03-02-PLAN.md
A	.planning/phases/03-agent-core/03-02-SUMMARY.md
A	.planning/phases/03-agent-core/03-03-PLAN.md
A	.planning/phases/03-agent-core/03-03-SUMMARY.md
A	.planning/phases/03-agent-core/03-CONTEXT.md
A	.planning/phases/03-agent-core/03-CP-PLAN.md
A	.planning/phases/03-agent-core/03-DISCUSSION-LOG.md
A	.planning/phases/03-agent-core/03-RESEARCH.md
A	.planning/phases/03-agent-core/03-UAT.md
A	.planning/phases/03-agent-core/03-VALIDATION.md
M	.planning/research/SUMMARY.md
A	Caddyfile
D	HEAD
A	REPO_TRIAGE_PHASENLISTE.md
A	REPO_TRIAGE_STUFE1.md
D	agent-client.tsx
D	api/connection-details/route.ts
D	app-icon.png
D	app/(app)/layout.tsx
D	app/(app)/page.tsx
D	app/(iframe)/embed/page.tsx
D	app/(iframe)/layout.tsx
D	app/api/connection-details/route.ts
D	applypatch-msg.sample
A	apps/agent/.agents/skills/livekit-agents/SKILL.md
A	apps/agent/.agents/skills/livekit-agents/references/freshness-rules.md
A	apps/agent/.claude/skills/livekit-agents/SKILL.md
A	apps/agent/.claude/skills/livekit-agents/references/freshness-rules.md
A	apps/agent/.dockerignore
A	apps/agent/.env.example
A	apps/agent/.github/assets/livekit-mark.png
A	apps/agent/.github/workflows/ruff.yml
A	apps/agent/.github/workflows/template-check.yml
A	apps/agent/.github/workflows/tests.yml
A	apps/agent/.gitignore
A	apps/agent/AGENTS.md
A	apps/agent/CLAUDE.md
A	apps/agent/Dockerfile
A	apps/agent/GEMINI.md
R100	LICENSE	apps/agent/LICENSE
A	apps/agent/README.md
A	apps/agent/WHITE_LABELING.md
A	apps/agent/agent.py
A	apps/agent/conftest.py
A	apps/agent/pyproject.toml
A	apps/agent/requirements.txt
A	apps/agent/taskfile.yaml
A	apps/agent/tests/test_agent.py
R100	.eslintrc.json	apps/frontend/.eslintrc.json
R100	.prettierignore	apps/frontend/.prettierignore
R100	.prettierrc	apps/frontend/.prettierrc
A	apps/frontend/Dockerfile
A	apps/frontend/LICENSE
R100	TEMPLATE.md	apps/frontend/TEMPLATE.md
R100	app-config.ts	apps/frontend/app-config.ts
R100	(app)/layout.tsx	apps/frontend/app/(app)/layout.tsx
R100	(app)/page.tsx	apps/frontend/app/(app)/page.tsx
R100	(iframe)/embed/page.tsx	apps/frontend/app/(iframe)/embed/page.tsx
R100	(iframe)/layout.tsx	apps/frontend/app/(iframe)/layout.tsx
R097	connection-details/route.ts	apps/frontend/app/api/connection-details/route.ts
R091	app/api/token/route.ts	apps/frontend/app/api/token/route.ts
R100	app/favicon.ico	apps/frontend/app/favicon.ico
R100	app/test/layout.tsx	apps/frontend/app/test/layout.tsx
R100	app/test/popup/page.tsx	apps/frontend/app/test/popup/page.tsx
R100	app/test/popup/styles.css	apps/frontend/app/test/popup/styles.css
R100	build-and-test.yaml	apps/frontend/build-and-test.yaml
R100	components.json	apps/frontend/components.json
R100	components/LiveKitProvider.tsx	apps/frontend/components/LiveKitProvider.tsx
R100	components/embed-iframe/agent-client.tsx	apps/frontend/components/embed-iframe/agent-client.tsx
R100	components/embed-iframe/session-view.tsx	apps/frontend/components/embed-iframe/session-view.tsx
R100	components/embed-iframe/theme-provider.tsx	apps/frontend/components/embed-iframe/theme-provider.tsx
R100	components/embed-iframe/welcome-view.tsx	apps/frontend/components/embed-iframe/welcome-view.tsx
R100	action-bar.tsx	apps/frontend/components/embed-popup/action-bar.tsx
R099	components/embed-popup/agent-client.tsx	apps/frontend/components/embed-popup/agent-client.tsx
R100	audio-visualizer.tsx	apps/frontend/components/embed-popup/audio-visualizer.tsx
R100	components/embed-popup/error-message.tsx	apps/frontend/components/embed-popup/error-message.tsx
R100	components/embed-popup/microphone-toggle.tsx	apps/frontend/components/embed-popup/microphone-toggle.tsx
R099	popup-view.tsx	apps/frontend/components/embed-popup/popup-view.tsx
R097	components/embed-popup/standalone-bundle-root.tsx	apps/frontend/components/embed-popup/standalone-bundle-root.tsx
R100	components/embed-popup/transcript.tsx	apps/frontend/components/embed-popup/transcript.tsx
R100	components/embed-popup/trigger.tsx	apps/frontend/components/embed-popup/trigger.tsx
R100	chat-entry.tsx	apps/frontend/components/livekit/chat/chat-entry.tsx
R094	components/livekit/chat/chat-input.tsx	apps/frontend/components/livekit/chat/chat-input.tsx
R100	chat/hooks/utils.ts	apps/frontend/components/livekit/chat/hooks/utils.ts
R100	components/livekit/device-select.tsx	apps/frontend/components/livekit/device-select.tsx
R100	components/livekit/track-toggle.tsx	apps/frontend/components/livekit/track-toggle.tsx
R100	components/popup-page-dynamic.tsx	apps/frontend/components/popup-page-dynamic.tsx
R100	components/popup-page.tsx	apps/frontend/components/popup-page.tsx
R085	components/root-layout.tsx	apps/frontend/components/root-layout.tsx
R100	components/theme-toggle.tsx	apps/frontend/components/theme-toggle.tsx
R100	components/ui/avatar.tsx	apps/frontend/components/ui/avatar.tsx
R100	button.tsx	apps/frontend/components/ui/button.tsx
R100	components/ui/card.tsx	apps/frontend/components/ui/card.tsx
R100	components/ui/scroll-area.tsx	apps/frontend/components/ui/scroll-area.tsx
R100	components/ui/select.tsx	apps/frontend/components/ui/select.tsx
R100	components/ui/toggle.tsx	apps/frontend/components/ui/toggle.tsx
R100	components/welcome-dynamic.tsx	apps/frontend/components/welcome-dynamic.tsx
R100	components/welcome.tsx	apps/frontend/components/welcome.tsx
R076	components/widget/ChatPanel.tsx	apps/frontend/components/widget/ChatPanel.tsx
R100	components/widget/FloatingButton.tsx	apps/frontend/components/widget/FloatingButton.tsx
R100	components/widget/VoiceVisualizer.tsx	apps/frontend/components/widget/VoiceVisualizer.tsx
R100	components/widget/index.tsx	apps/frontend/components/widget/index.tsx
R100	eslint.config.mjs	apps/frontend/eslint.config.mjs
R100	hooks/use-agent-control-bar.ts	apps/frontend/hooks/use-agent-control-bar.ts
R100	hooks/use-chat-and-transcription.ts	apps/frontend/hooks/use-chat-and-transcription.ts
R100	hooks/use-connection-details.ts	apps/frontend/hooks/use-connection-details.ts
R100	hooks/use-publish-permissions.ts	apps/frontend/hooks/use-publish-permissions.ts
R100	hooks/useDebug.ts	apps/frontend/hooks/useDebug.ts
R100	hooks/useDelayedValue.ts	apps/frontend/hooks/useDelayedValue.ts
R100	env.ts	apps/frontend/lib/env.ts
R100	lib/styles.ts	apps/frontend/lib/styles.ts
R100	lib/types.ts	apps/frontend/lib/types.ts
R100	lib/utils.ts	apps/frontend/lib/utils.ts
R100	next.config.ts	apps/frontend/next.config.ts
R096	package.json	apps/frontend/package.json
A	apps/frontend/pnpm-lock.yaml
R100	postcss.config.mjs	apps/frontend/postcss.config.mjs
R100	file.svg	apps/frontend/public/file.svg
R100	CommitMono-400-Italic.otf	apps/frontend/public/fonts/CommitMono-400-Italic.otf
R100	CommitMono-400-Regular.otf	apps/frontend/public/fonts/CommitMono-400-Regular.otf
R100	CommitMono-700-Italic.otf	apps/frontend/public/fonts/CommitMono-700-Italic.otf
R100	CommitMono-700-Regular.otf	apps/frontend/public/fonts/CommitMono-700-Regular.otf
R100	globe.svg	apps/frontend/public/globe.svg
R100	lk-logo-dark.svg	apps/frontend/public/lk-logo-dark.svg
R100	lk-logo.svg	apps/frontend/public/lk-logo.svg
R100	next.svg	apps/frontend/public/next.svg
R100	public/vercel.svg	apps/frontend/public/vercel.svg
R100	public/window.svg	apps/frontend/public/window.svg
R100	renovate.json	apps/frontend/renovate.json
R100	globals.css	apps/frontend/styles/globals.css
R100	sync-to-production.yaml	apps/frontend/sync-to-production.yaml
R100	taskfile.yaml	apps/frontend/taskfile.yaml
R100	tests/api-token.test.ts	apps/frontend/tests/api-token.test.ts
R100	tests/setup.ts	apps/frontend/tests/setup.ts
R100	tests/widget.test.tsx	apps/frontend/tests/widget.test.tsx
R091	tsconfig.json	apps/frontend/tsconfig.json
R100	tsconfig.webpack.json	apps/frontend/tsconfig.webpack.json
R100	vitest.config.ts	apps/frontend/vitest.config.ts
R095	webpack.config.js	apps/frontend/webpack.config.js
R100	workflows/build-and-test.yaml	apps/frontend/workflows/build-and-test.yaml
R100	workflows/sync-to-production.yaml	apps/frontend/workflows/sync-to-production.yaml
D	assets/app-icon.png
D	assets/readme-hero-dark.webp
D	assets/readme-hero-light.webp
D	assets/screenshot-dark.webp
D	assets/screenshot-light.webp
D	assets/template-graphic.svg
D	chat-input.tsx
D	chat/chat-entry.tsx
D	chat/chat-input.tsx
D	commit-msg.sample
D	components/embed-popup/action-bar.tsx
D	components/embed-popup/audio-visualizer.tsx
D	components/embed-popup/popup-view.tsx
D	components/livekit/chat/chat-entry.tsx
D	components/livekit/chat/hooks/utils.ts
D	components/ui/button.tsx
D	config
D	description
D	device-select.tsx
A	docker-compose.yml
D	embed-iframe/agent-client.tsx
D	embed-iframe/session-view.tsx
D	embed-iframe/theme-provider.tsx
D	embed-iframe/welcome-view.tsx
D	embed-popup/action-bar.tsx
D	embed-popup/agent-client.tsx
D	embed-popup/audio-visualizer.tsx
D	embed-popup/error-message.tsx
D	embed-popup/microphone-toggle.tsx
D	embed-popup/popup-view.tsx
D	embed-popup/standalone-bundle-root.tsx
D	embed-popup/transcript.tsx
D	embed-popup/trigger.tsx
D	embed/page.tsx
D	error-message.tsx
D	exclude
D	favicon.ico
D	fonts/CommitMono-400-Italic.otf
D	fonts/CommitMono-400-Regular.otf
D	fonts/CommitMono-700-Italic.otf
D	fonts/CommitMono-700-Regular.otf
D	fsmonitor-watchman.sample
D	heads/main
D	hooks/applypatch-msg.sample
D	hooks/commit-msg.sample
D	hooks/fsmonitor-watchman.sample
D	hooks/post-update.sample
D	hooks/pre-applypatch.sample
D	hooks/pre-commit.sample
D	hooks/pre-merge-commit.sample
D	hooks/pre-push.sample
D	hooks/pre-rebase.sample
D	hooks/pre-receive.sample
D	hooks/prepare-commit-msg.sample
D	hooks/push-to-checkout.sample
D	hooks/sendemail-validate.sample
D	hooks/update.sample
D	hooks/utils.ts
D	index
D	info/exclude
M	infrastructure/README.md
M	infrastructure/docker-compose.yml
D	infrastructure/livekit.yaml
D	lib/env.ts
D	livekit/chat/chat-entry.tsx
D	livekit/chat/chat-input.tsx
D	livekit/chat/hooks/utils.ts
D	livekit/device-select.tsx
D	livekit/track-toggle.tsx
D	logs/HEAD
D	logs/refs/heads/main
D	logs/refs/remotes/origin/HEAD
D	main
D	microphone-toggle.tsx
D	objects/pack/pack-fe97193e4f09082fb52e466c709935d4caaefba6.idx
D	objects/pack/pack-fe97193e4f09082fb52e466c709935d4caaefba6.pack
D	objects/pack/pack-fe97193e4f09082fb52e466c709935d4caaefba6.rev
D	origin/HEAD
D	pack-fe97193e4f09082fb52e466c709935d4caaefba6.idx
D	pack-fe97193e4f09082fb52e466c709935d4caaefba6.pack
D	pack-fe97193e4f09082fb52e466c709935d4caaefba6.rev
D	pack/pack-fe97193e4f09082fb52e466c709935d4caaefba6.idx
D	pack/pack-fe97193e4f09082fb52e466c709935d4caaefba6.pack
D	pack/pack-fe97193e4f09082fb52e466c709935d4caaefba6.rev
D	package-lock.json
D	packed-refs
D	page.tsx
D	popup-page-dynamic.tsx
D	popup-page.tsx
D	popup/page.tsx
D	popup/styles.css
D	post-update.sample
D	pre-applypatch.sample
D	pre-commit.sample
D	pre-merge-commit.sample
D	pre-push.sample
D	pre-rebase.sample
D	pre-receive.sample
D	prepare-commit-msg.sample
D	public/file.svg
D	public/globe.svg
D	public/lk-logo-dark.svg
D	public/lk-logo.svg
D	public/next.svg
D	push-to-checkout.sample
D	readme-hero-dark.webp
D	readme-hero-light.webp
A	readme/AGENT_PROMPT.md
A	readme/COOLIFY-KONFIGURATION.md
A	readme/SCHULUNG_GUIDE.md
D	refs/heads/main
D	refs/remotes/origin/HEAD
D	remotes/origin/HEAD
D	root-layout.tsx
D	route.ts
D	screenshot-dark.webp
D	screenshot-light.webp
D	select.tsx
D	sendemail-validate.sample
D	session-view.tsx
D	standalone-bundle-root.tsx
D	styles.css
D	styles.d.ts
D	styles.ts
D	styles/globals.css
D	template-graphic.svg
D	test/layout.tsx
D	test/popup/page.tsx
D	test/popup/styles.css
D	theme-provider.tsx
D	theme-toggle.tsx
D	toggle.tsx
D	track-toggle.tsx
D	transcript.tsx
D	trigger.tsx
D	types.ts
D	update.sample
D	use-agent-control-bar.ts
D	use-chat-and-transcription.ts
D	use-connection-details.ts
D	use-publish-permissions.ts
D	useDebug.ts
D	useDelayedValue.ts
D	utils.ts
D	vercel.svg
D	welcome-dynamic.tsx
D	welcome-view.tsx
D	welcome.tsx
D	window.svg
```

## G. Repo-Hygiene-Check (gegen die Phase-2-Katastrophen-Muster)

```bash
git ls-files | grep -E "^(HEAD|packed-refs|pre-commit\.sample|ORIG_HEAD|FETCH_HEAD|index)$" || echo "CLEAN: keine git internals tracked"
```

```
CLEAN: keine git internals tracked
```

```bash
find . -maxdepth 2 -name "docker-compose*.yml" -not -path "*/node_modules/*"
```

```
./docker-compose.yml
./infrastructure/docker-compose.yml
```

```bash
find . -maxdepth 2 -name "Caddyfile" -not -path "*/node_modules/*"
```

```
./Caddyfile
./infrastructure/Caddyfile
```

```bash
find . -maxdepth 3 -name "package.json" -not -path "*/node_modules/*"
```

```
./apps/frontend/package.json
./infrastructure/package.json
```

## H. Funktional verifizierter Stand

Bekannt verifiziert (vom User Hermann in dieser Session am laufenden System bestätigt):

- Voice-Loop Browser ↔ Agent auf live.begemotix.cloud ist sprechbar.

Ungeklärt (keine weiteren manuellen Verifikationen in dieser Session dokumentiert):

- alles andere

## I. Bekanntes Offenes

- MCP-Verbindung zu begemotix.pro: ?
- Frappe-Auth-Passthrough: ?
- Filler-Audio gegen Dead Air: ?
- Interruption-Handling getestet: ?
- Welche Phase-3-Plans wurden ausgeführt: ?
