# Feature Landscape

**Domain:** Voice Assistant for ERP (Frappe/ERPNext)
**Researched:** 2026-04-18

## Table Stakes

Features users expect in a modern voice assistant for business software. Missing these makes the product feel incomplete or untrustworthy.

| Feature                             | Why Expected                                                                                          | Complexity | Notes                                                               |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| **Low-Latency Voice Interaction**   | Users expect natural conversations (<1s delay). Slow STT/TTS pipelines break immersion.               | High       | Requires OpenAI Realtime API or highly optimized STT/TTS pipelines. |
| **Strict Permission Passthrough**   | Enterprise users cannot risk data leaks. The agent must inherit exact Frappe user permissions (RBAC). | High       | Crucial requirement.                                                |
| **Interruption Handling (VAD)**     | Users naturally interrupt AI. The agent must stop speaking instantly when interrupted.                | Medium     | Built into LiveKit agents natively.                                 |
| **Dual-Mode Widget (Voice + Text)** | Users in noisy or public environments need a text fallback.                                           | Low        | Combine chat and voice UI in one widget.                            |
| **Natural Language ERP Queries**    | Users want to ask "What is the status of my order?" instead of writing SQL or navigating reports.     | Medium     | Powered by LLM tool calling.                                        |
| **Multilingual Support**            | Business happens globally; at minimum German and English are required for the DACH market.            | Low        | Most modern LLMs handle this natively.                              |

## Differentiators

Features that set this product apart from existing Frappe AI tools (which are mostly text-based or deeply coupled to the Frappe UI).

| Feature                            | Value Proposition                                                                                                         | Complexity | Notes                                         |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------- |
| **100% Self-Hosted & White-Label** | Deep competitive advantage for DSGVO/GDPR compliance. No LiveKit Cloud lock-in.                                           | High       | Requires robust Docker Compose setups.        |
| **Dynamic Tooling via MCP**        | Instead of hardcoded API integrations, the agent dynamically learns Frappe capabilities via the Model Context Protocol.   | High       | Extremely scalable for custom Frappe modules. |
| **Hardware-Agnostic Deployment**   | Can run on standard KVM VPS without mandatory GPU requirements by leveraging external API providers.                      | Medium     | Broadens the addressable market.              |
| **External Embeddability**         | The widget can live outside the Frappe Desk (e.g., in customer portals or external frontends) using standard auth tokens. | Medium     | Empowers B2B customer self-service.           |

## Anti-Features

Features to explicitly NOT build to maintain the project's core value and architectural constraints.

| Anti-Feature                          | Why Avoid                                                                                    | What to Do Instead                                                                          |
| ------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Agent-Side Authorization**          | Duplicating permission logic is a massive security risk and maintenance nightmare.           | Pass the Frappe authentication token to the MCP server.                                     |
| **Internal Frappe App (Monolith)**    | Tight coupling breaks if the customer upgrades Frappe or uses custom frontend architectures. | Build as a strictly external, standalone Node/Python service interacting via standard APIs. |
| **Cloud-Only Telemetry/SaaS Lock-in** | Violates the primary "self-hosted" constraint of the product.                                | Use standard OSS observability (e.g., self-hosted Grafana/Prometheus or simple logs).       |
| **Proprietary Frontend Frameworks**   | Makes white-labeling and community contributions difficult.                                  | Use standard React/Next.js LiveKit templates (e.g., `agent-starter-embed`).                 |

## Feature Dependencies

- **Real-Time Voice** → requires **LiveKit Server** and **OpenAI Realtime API**.
- **ERP Data Access** → requires **Frappe MCP Server** and **Auth Token Passthrough**.
- **Browser Widget** → requires **LiveKit Token Generation** via a secure backend endpoint.

## MVP Recommendation

Prioritize:

1. **Self-Hosted LiveKit Infrastructure:** Docker Compose setup for LiveKit server.
2. **Next.js Voice/Text Widget:** Embeddable floating button based on LiveKit templates.
3. **Agent Worker (Type A):** OpenAI Realtime API integration with low latency.
4. **Frappe MCP (Read-only):** Connect agent to Frappe to read user-specific records.

Defer:

- Direct SIP/Phone trunking (focus on browser widget first).
- Write operations (Start with read-only to validate the architecture safely).
- Local LLM/TTS integration (Type B/C) - validate latency with OpenAI Realtime first.

## Sources

- [LiveKit Voice Agents (HIGH)](https://livekit.com/voice-agents)
- [Frappe Cloud Marketplace - ChatNext & Frappe Assistant Core (MEDIUM)](https://frappecloud.com/marketplace)
- [Project Requirements Context (HIGH)](.planning/PROJECT.md)
