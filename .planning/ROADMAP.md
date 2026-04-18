# Project Roadmap

## Phases

- [x] **Phase 1: Infrastructure Setup** - Self-hosted LiveKit WebRTC engine and proxy deployment (completed 2026-04-18)
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
**Plans**: 5 plans
**UI hint**: yes
Plans:
- [x] 02-01-PLAN.md — Setup Next.js, shadcn/ui and LiveKit SDKs.
- [ ] 02-02-PLAN.md — Implement secure Token API and Room Provider.
- [ ] 02-03-PLAN.md — Build Floating Action Button and Chat Panel UI.
- [ ] 02-04-PLAN.md — Integrate LiveKit WebRTC and Voice Visualizer.
- [ ] 02-05-PLAN.md — Finalize Dynamic Styling and Phase Verification.

### Phase 3: Agent Core
**Goal**: Users can converse naturally with a voice agent that responds with low latency
**Depends on**: Phase 2
**Requirements**: AGNT-01, AGNT-02, AGNT-03, AGNT-04
**Success Criteria** (what must be TRUE):
  1. User can speak to the agent and hear AI-generated spoken responses with minimal delay
  2. User can interrupt the agent while it is speaking, and the agent stops and listens
  3. User hears "filler audio" when the agent is thinking for a long time to prevent dead air
**Plans**: TBD

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

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Setup | 0 | Complete    | 2026-04-18 |
| 2. Frontend Widget | 0 | Not started | - |
| 3. Agent Core | 0 | Not started | - |
| 4. Frappe Integration | 0 | Not started | - |
