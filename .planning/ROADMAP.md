# Project Roadmap

## Phases

- [x] **Phase 1: Infrastructure Setup** - Self-hosted LiveKit WebRTC engine and proxy deployment
      (completed 2026-04-18)
- [x] **Phase 2: Frontend Widget** - Next.js voice widget mit unauthentifiziertem Gast-Token
      (completed 2026-04-18)
- [x] **Phase 3: Agent Core** - Low-latency OpenAI Realtime voice agent with interruption handling
      (completed 2026-04-19)
- [x] **Phase 4: Frappe Integration** - Secure MCP connection for read-only Frappe data access
      (Gap-Closure complete 2026-04-19; Live-Verifikation stdio+MCP bestaetigt 2026-04-20)
- [ ] **Phase 5: EU-Voice-Agent (Typ B)** - Mistral LLM + Voxtral STT/TTS als zweiter Agent-Mode
      **(ACTIVE seit /gsd-transition 2026-04-21)**
- [ ] **Phase 6: Dynamisches Prompt-Management** - MCP-neutrale System-Prompt-Steuerung
- [ ] **Phase 7: Self-Hosted TTS Alternative** - (Backlog) Piper für lokale Sprachsynthese

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
- [x] 03-03-PLAN.md — Verify the implementation through automated tests and partner documentation.

### Phase 4: Frappe Integration

**Goal**: The voice agent connects to Frappe using its own dedicated credentials and securely relays read-only data
**Depends on**: Phase 3
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04, INTG-05
**Success Criteria** (what must be TRUE):

1. The agent connects to the Frappe MCP server and dynamically discovers available read-only tools
2. The agent successfully authenticates its MCP requests using its own fixed credentials (e.g. API-Key from .env)
3. User can ask the agent about Frappe data, and the agent retrieves and speaks information accessible to the agent user
4. If the agent asks for data it lacks permissions for, it gracefully informs the user of the restriction instead of crashing
   **Plans**: 10/10 plans complete
   Plans:

- [x] 04-01-PLAN.md — MCP foundation: ENV contract, factory, and baseline integration tests.
- [x] 04-02-PLAN.md — Wire session-scoped MCP lifecycle with dedicated agent identity and discovery guards.
- [x] 04-03-PLAN.md — Add graceful permission/error handling and operator handover.
- [x] 04-04-PLAN.md — Gap closure: fix MCP runtime dependency/import blocker and unblock live UAT retests.
- [x] 04-05-PLAN.md — Wave D gate closure: finalize G1/G2/G3 evidence and unlock execution order.
- [x] 04-06-PLAN.md — Wave A closure: validate endpoint-bound ENV/auth contract evidence.
- [x] 04-07-PLAN.md — Wave B closure: document session-boundary and cleanup behavior evidence.
- [x] 04-08-PLAN.md — Wave C closure: complete 403 no-retry product-behavior evidence.
- [x] 04-09-PLAN.md — Wave E closure: run final live UAT evidence checks against target system.
- [x] 04-10-PLAN.md — Wave F closure: synchronize final handover, state, and roadmap readiness.

### Phase 5: EU-Voice-Agent (Typ B)

**Goal**: Ein zweiter Agent-Modus basierend auf Mistral LLM und Voxtral (STT/TTS) wird integriert und kann im selben Docker-Image per ENV umgeschaltet werden.
**Depends on**: Phase 4
**Requirements**: AGNT-05
**Success Criteria** (what must be TRUE):

1. Der Agent-Worker kann per Environment-Variable zwischen OpenAI-Realtime (Typ A) und Mistral/Voxtral (Typ B) umgeschaltet werden.
2. Das bestehende MCP-Toolset funktioniert nahtlos mit beiden Agent-Modi.
3. Der Typ B Agent unterstützt Sprache-zu-Text und Text-zu-Sprache über die lokalen/EU-konformen Voxtral-Schnittstellen.
4. Beide Agent-Modi laufen im selben Docker-Image, ohne dass unterschiedliche Container gebaut werden müssen.
5. Der EU-Modus (Typ B, Mistral + Voxtral) ist der Default-Mode für Neu-Deployments. Typ A (OpenAI Realtime) bleibt per ENV wählbar für Kunden, die geringere Latenz über DSGVO-Konformität priorisieren.
   **Plans**: 2 plans
   Plans:

- [x] 05-01-PLAN.md — Mode-Vertrag, Factory-Basis und Wave-0-Tests für Typ-A/Typ-B-Umschaltung umsetzen.
- [ ] 05-02-PLAN.md — Entrypoint-Integration, Hard-Fail-Policy und technische AGNT-05-Verifikation finalisieren.

### Phase 6: Dynamisches Prompt-Management

**Goal**: Der System-Prompt des Agenten kann flexibel und extern (z.B. über das MCP) verwaltet werden, um Frappe-Zentrierung zu vermeiden.
**Depends on**: Phase 5
**Requirements**: TBD
**Success Criteria** (what must be TRUE):

1. Der Agent bezieht seinen System-Prompt dynamisch über eine MCP-neutrale Schnittstelle (z.B. MCP Resources, ENV, Config-Endpoint). Die konkrete Quelle ist pro Deployment konfigurierbar und nicht an einen bestimmten ERP-Anbieter gebunden.
2. Es gibt einen stabilen lokalen Fallback-Mechanismus, falls die externe Prompt-Quelle nicht erreichbar ist.
3. Das Prompt-Management ist architektonisch entkoppelt vom spezifischen ERP-System.
   **Plans**: TBD

### Phase 7: Self-Hosted TTS Alternative (Backlog)

**Goal**: Evaluation und optionale Integration von Piper als vollständig lokal gehostete TTS-Alternative ohne Cloud-Abhängigkeiten. Zielsegment: Kunden mit self-hosted LLM und vollständiger Datenresidenz-Anforderung (z.B. öffentliche Hand, Konzern-IT mit Air-Gapped-Setup).
**Depends on**: Phase 5
**Requirements**: TBD
**Success Criteria** (what must be TRUE):

1. Der Agent kann optional Piper für die Sprachsynthese verwenden, ohne Cloud-Abhängigkeit, in mindestens drei Sprachen (DE/EN/FR).
   **Plans**: TBD

## Progress

| Phase                   | Plans Complete | Status      | Completed  |
| ----------------------- | -------------- | ----------- | ---------- |
| 1. Infrastructure Setup | 2/2            | Complete    | 2026-04-18 |
| 2. Frontend Widget      | 6/6            | Complete    | 2026-04-18 |
| 3. Agent Core           | 4/4            | Complete    | 2026-04-19 |
| 4. Frappe Integration   | 10/10          | Complete    | 2026-04-19 |
| 5. EU-Voice-Agent       | 0/TBD          | In progress | 2026-04-21 |
| 6. Prompt-Management    | 0/TBD          | Pending     | -          |
| 7. Piper TTS (Backlog)  | 0/TBD          | Pending     | -          |
