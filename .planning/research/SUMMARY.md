# Project Research Summary

**Project:** LiveKit for Frappe
**Domain:** Voice Assistant for ERP (Frappe/ERPNext)
**Researched:** 2026-04-18
**Confidence:** HIGH

## Executive Summary

The product is a 100% self-hosted, cloud-independent voice assistant for Frappe/ERPNext business software. It bridges a Next.js floating browser widget, a LiveKit WebRTC engine, a Python-based Agent Worker (Type A using OpenAI Realtime API), and the Frappe ERP via the Model Context Protocol (MCP). Experts build this with decoupled, external standalone microservices to avoid Frappe monolith coupling and to ensure hardware-agnostic deployment.

The recommended approach relies on a multi-container Docker Compose setup with Caddy for reverse proxying and SSL. The Agent uses the Frappe MCP Server for dynamic tool discovery, fully delegating ERP business logic. Crucially, the Next.js widget captures the Frappe session token and passes it to the LiveKit Server as connection metadata, ensuring the Agent acts strictly within the user's permission boundaries.

Key risks include "dead air" during latent Frappe API queries (which breaks conversational UX) and the temptation to use global API keys that bypass user permissions. To mitigate these risks, the Agent must employ asynchronous "filler words" before blocking tool calls and strictly enforce token-based impersonation for all MCP requests.

## Research & Knowledge Enforcement

- **Primäre Datenquelle**: Für alle technischen Implementierungen bezüglich LiveKit (Server-Setup, Agent-Worker-Syntax, Frontend-Hooks) MUSS Cursor vorrangig das angebundene LiveKit-Dokumentations-MCP nutzen.
- **Vorgehensweise**: Vor dem Schreiben von Code für LiveKit-Komponenten ist ein Suchlauf über das MCP zwingend erforderlich, um sicherzustellen, dass die aktuellsten SDK-Versionen und Best Practices verwendet werden.
- **Sekundärquellen**: Allgemeines LLM-Wissen darf nur genutzt werden, wenn das MCP keine spezifischen Informationen liefert oder für allgemeine Programmierlogik außerhalb des LiveKit-Ökosystems.


## Research & Knowledge Enforcement

- **Primäre Datenquelle**: Für alle technischen Implementierungen bezüglich LiveKit (Server-Setup, Agent-Worker-Syntax, Frontend-Hooks) MUSS Cursor vorrangig das angebundene **LiveKit-Dokumentations-MCP** nutzen.
- **Vorgehensweise**: Vor dem Schreiben von Code für LiveKit-Komponenten ist ein Suchlauf über das MCP zwingend erforderlich, um sicherzustellen, dass die aktuellsten SDK-Versionen und Best Practices verwendet werden.
- **Sekundärquellen**: Allgemeines LLM-Wissen darf nur genutzt werden, wenn das MCP keine spezifischen Informationen liefert oder für allgemeine Programmierlogik außerhalb des LiveKit-Ökosystems.

## Key Findings

### Recommended Stack

The architecture is built around a robust, self-hosted WebRTC stack and modern Python AI orchestration, connected to Frappe via standardized protocols rather than direct REST integrations.

**Core technologies:**
- **Python 3.12+ & `livekit-agents`:** Agent Worker (Type A) - Standard language/framework for orchestration and OpenAI Realtime integration.
- **Next.js (App Router) 15.x:** Web-Frontend - Easiest way to build a scalable, embeddable floating voice widget.
- **LiveKit Server v1.10.x & Caddy:** Realtime Infra & Ingress - Self-hosted WebRTC backend with auto-HTTPS, fulfilling the core self-hosting requirement.
- **MCP v1.27.x:** Frappe API Integration - Standardizes tool calling, dynamically pulling Frappe capabilities to keep the agent agnostic.

### Expected Features

**Must have (table stakes):**
- Low-Latency Voice Interaction (<1s delay via OpenAI Realtime API)
- Strict Permission Passthrough (RBAC from Frappe)
- Interruption Handling (VAD - native to LiveKit)
- Natural Language ERP Queries via MCP tools

**Should have (competitive):**
- 100% Self-Hosted & White-Label deployment
- Dynamic Tooling via MCP (decoupled from ERP schema)
- External Embeddability (B2B customer self-service outside Frappe Desk)

**Defer (v2+):**
- Direct SIP/Phone trunking
- Write operations (Start with read-only to validate architecture)
- Local LLM/TTS integration (Type B/C pipelines)

### Architecture Approach

The architecture is deeply decoupled from the Frappe internal bench/app structure, enforcing the "external Standalone-Lösung" constraint through a 4-tier model.

**Major components:**
1. **Frontend (Next.js Widget):** User UI, mic capture, and token request/auth exchange.
2. **Infrastructure (LiveKit & Caddy):** WebRTC room management, SFU, audio routing, and SSL termination.
3. **Agent Core (Python):** Connects to LiveKit, manages OpenAI Realtime WebSocket, and executes MCP tool calls.
4. **Integration Layer (Frappe MCP Server):** Exposes Frappe APIs as MCP tools and handles authentication passthrough.

### Critical Pitfalls

1. **Dead Air During Frappe Tool Calls:** OpenAI Realtime pauses audio during function calling. Prevent by implementing asynchronous "filler words" before executing the MCP call.
2. **Auth Bypass via Global API Keys:** Never use a master key for the Agent. Prevent by passing the Frappe session token from the widget to the Agent and MCP server for strict user-permission enforcement.
3. **WebRTC/TURN Routing in Docker:** Connection fails externally due to NAT leakage. Prevent by properly configuring `node_ip` in `livekit.yaml` and testing WebRTC Fallbacks early.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Self-Hosted Infrastructure & LiveKit Setup
**Rationale:** The foundational WebRTC engine and proxy layer are prerequisites for any frontend or agent connection.
**Delivers:** Docker Compose setup running Caddy and LiveKit Server.
**Addresses:** 100% Self-Hosted & White-Label deployment.
**Avoids:** WebRTC/TURN routing issues in Docker setups.

### Phase 2: Next.js Frontend Voice Widget
**Rationale:** Validates WebRTC connectivity and Frappe token capture before introducing AI complexity.
**Delivers:** Embeddable floating button (`agent-starter-embed`) capable of joining a LiveKit room.
**Uses:** Next.js 15.x, `@livekit/components-react`.
**Implements:** Client Layer and Auth token extraction.

### Phase 3: Agent Core (Type A Voice Response)
**Rationale:** Introduces the AI layer (OpenAI Realtime) for low-latency STT/TTS without yet integrating Frappe data.
**Delivers:** Python Agent Worker able to converse with the user and handle interruptions.
**Uses:** Python 3.12+, `livekit-agents`, `livekit-plugins-openai`.
**Implements:** Agent Layer logic and VAD configuration.

### Phase 4: Frappe MCP Integration & Auth Passthrough
**Rationale:** Connects the conversing agent to ERP data securely as the final integration step.
**Delivers:** Frappe MCP Server with read-only tools and full token passthrough from Frontend to Agent to MCP.
**Uses:** MCP v1.27.x.
**Implements:** Integration Layer and dynamic tool discovery.
**Avoids:** Auth bypass and "Dead air" during tool calls (implement filler words here).

### Phase Ordering Rationale

- Infrastructure must precede clients.
- The UI must capture tokens before the agent can impersonate the user.
- Basic conversational AI must work smoothly (VAD/latency) before complicating the LLM with custom tools and structured data retrieval from Frappe.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4:** Frappe MCP token passthrough and handling Frappe Link-Field Permission errors (Opaque 403s). Needs validation on exact token flow.

Phases with standard patterns (skip research-phase):
- **Phase 1 & 2:** Standard LiveKit Docker & React UI patterns are well-documented and established.
- **Phase 3:** Standard OpenAI Realtime API implementation via `livekit-agents`.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified with LiveKit official docs and standard MCP specifications |
| Features | HIGH | Table stakes match standard voice AI and Frappe requirements |
| Architecture | HIGH | Standard decoupled multi-container pattern for LiveKit |
| Pitfalls | HIGH | Sourced from LiveKit GitHub issues and typical Frappe auth patterns |

**Overall confidence:** HIGH

### Gaps to Address

- **Frappe Link-Field Permissions:** Handling opaque 403s elegantly in the MCP server so the Agent can inform the user properly.
- **Token Transport:** Exact mechanics of passing the Frappe session cookie/token via LiveKit Room Metadata into the Python agent context securely.

## Sources

### Primary (HIGH confidence)
- [LiveKit Agents Python SDK](https://github.com/livekit/agents) - Core framework & MCP integration
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Tool calling architecture
- [.planning/PROJECT.md] - Authoritative requirements
- Frappe Forum & Docs - Authentication mechanisms and Link Field architecture

### Secondary (MEDIUM confidence)
- Frappe Cloud Marketplace - ChatNext & Frappe Assistant Core comparisons
- OpenAI Developer Forums - Realtime API VAD issues and truncation handling

---
*Research completed: 2026-04-18*
*Ready for roadmap: yes*