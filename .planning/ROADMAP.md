# Project Roadmap

## Phases

- [ ] **Phase 1: Infrastructure Setup** - Self-hosted LiveKit WebRTC engine and proxy deployment
- [ ] **Phase 2: Frontend Widget** - Next.js voice widget with Frappe session capture
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
  4. Deployment can be customized (API keys, labels) via environment variables without code changes
**Plans**: TBD

### Phase 2: Frontend Widget
**Goal**: Users can initiate a voice connection to the LiveKit server from their browser
**Depends on**: Phase 1
**Requirements**: WIDG-01, WIDG-02, WIDG-03
**Success Criteria** (what must be TRUE):
  1. User sees a floating voice/text widget in their browser
  2. User can click the widget to successfully establish a WebRTC connection to the local LiveKit server
  3. The widget automatically captures the user's active Frappe session and passes it as Room Metadata to the connection
**Plans**: TBD
**UI hint**: yes

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
**Goal**: The voice agent can securely read and relay the user's Frappe data based on their permissions
**Depends on**: Phase 3
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04, INTG-05
**Success Criteria** (what must be TRUE):
  1. The agent connects to the Frappe MCP server and dynamically discovers available read-only tools
  2. The agent successfully authenticates its MCP requests using the Frappe session token provided by the widget
  3. User can ask the agent about their Frappe data, and the agent retrieves and speaks the correct information
  4. If a user asks for data they lack permissions for, the agent gracefully informs them of the restriction instead of crashing
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Setup | 0 | Not started | - |
| 2. Frontend Widget | 0 | Not started | - |
| 3. Agent Core | 0 | Not started | - |
| 4. Frappe Integration | 0 | Not started | - |
