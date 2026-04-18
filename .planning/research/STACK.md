# Technology Stack

**Project:** LiveKit for Frappe
**Researched:** 2026-04-18
**Overall Confidence:** HIGH

## Recommended Stack

### Core Framework
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12+ | Agent Worker (Type A) | Standard language for `livekit-agents`. Provides best support for MCP and backend orchestration. | HIGH |
| Next.js (App Router) | 15.x | Web-Frontend (Widget/Chatbot) | Foundation of LiveKit's `agent-starter-embed`. Easiest way to build scalable floating voice widgets. | HIGH |
| Model Context Protocol (MCP) | v1.27.x | Frappe API Integration | Standardizes tool calling. Agent dynamically pulls tools from Frappe without hardcoding endpoints. | HIGH |

### Database
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| N/A | - | Data Storage | Agent is stateless. All persistent data, permissions, and logic live strictly within the Frappe backend. | HIGH |

### Infrastructure
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| LiveKit Server | v1.10.x | WebRTC Engine | Fulfills core requirement of a self-hosted, cloud-independent WebRTC backend. | HIGH |
| Docker Compose | v2.x | Deployment | Ensures easy, hardware-agnostic rollout on customer infrastructure (VPS/On-Prem). | HIGH |
| Caddy | v2.7+ | Reverse Proxy & SSL | Automatic HTTPS via Let's Encrypt. LiveKit WebRTC strictly requires SSL. Caddy is the lowest-friction solution for Docker. | HIGH |

### Supporting Libraries
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `livekit-agents` | 1.5.x | Orchestration | Core Python framework for building the real-time interaction logic. | HIGH |
| `livekit-plugins-openai` | 1.5.x | AI Integration | Required for Type A (OpenAI Realtime API) voice-to-voice bridging. | HIGH |
| `mcp` (Python SDK) | 1.27.x | MCP Client | Used within the LiveKit Python agent to connect to the Frappe MCP server. | HIGH |
| `@livekit/components-react` | 2.9.x | Frontend UI | Required for React-based WebRTC rooms and microphone management. | HIGH |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| AI Pipeline | OpenAI Realtime API | Modular Pipeline (STT -> LLM -> TTS) | Requirement explicitly defines "Type A" (OpenAI Realtime) for initial low latency. Modular pipeline is "Type B" and planned for later DSGVO compliance. |
| Integration | MCP (Model Context Protocol) | Direct Frappe REST API | Direct REST API requires maintaining specific endpoints in the agent. MCP delegates tool definitions to Frappe, keeping the agent agnostic. |
| Routing/Proxy | Caddy | Nginx | Nginx requires external tools (certbot) for SSL. Caddy's auto-HTTPS reduces setup friction for customer-hosted instances. |
| Frontend | Next.js Standalone | Frappe App integration | Constraints specify the product is a "strikt externe Standalone-Lösung". Integrating deeply into Frappe benches violates this. |

## Installation

```bash
# Agent Worker (Python)
pip install livekit-agents==1.5.2 livekit-plugins-openai==1.5.x mcp[cli]==1.27.x

# Frontend (Next.js)
npx create-next-app@latest my-voice-widget
npm install @livekit/components-react@2.9.x @livekit/components-styles livekit-client
```

## Sources

- [LiveKit Agents Python SDK](https://github.com/livekit/agents) (HIGH)
- [LiveKit Components React](https://github.com/livekit/components-js) (HIGH)
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) (HIGH)
- [.planning/PROJECT.md] (Authoritative requirements)
