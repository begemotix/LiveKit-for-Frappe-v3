# Architecture Research

**Domain:** Voice-Assistent für Frappe (LiveKit / OpenAI Realtime / MCP)
**Researched:** 2026-04-18
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Next.js Browser Widget                │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Realtime Infra & Ingress                 │
│  ┌──────────┐  ┌───────────────────────────────────────┐    │
│  │  Caddy   │  │             LiveKit Server            │    │
│  └──────────┘  └───────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                         Agent Layer                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Python LiveKit Agent (OpenAI Realtime + MCP Client) │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Integration & Data Layer                 │
│  ┌──────────────────┐       ┌──────────────────────────┐    │
│  │ Frappe MCP Server│ ──────│     Frappe / ERPNext     │    │
│  └──────────────────┘       └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Next.js Browser Widget | User UI, mic capture, audio playback, token request (auth exchange) | Next.js with `@livekit/components-react` |
| Caddy / Ingress | Reverse proxy, SSL termination for Next.js and LiveKit | `caddy` Docker container |
| LiveKit Server | WebRTC room management, SFU, routing audio tracks | Official `livekit/livekit-server` |
| Python LiveKit Agent | Connects to LiveKit, manages OpenAI Realtime WebSocket, executes MCP tool calls | Python with `livekit-agents` and `livekit.agents.llm.mcp` |
| Frappe MCP Server | Exposes Frappe REST APIs as MCP tools, handles Frappe authentication | Node.js or Python MCP SDK |
| Frappe / ERPNext | Actual ERP backend, processes business logic, enforces permissions | Frappe Framework |

## Recommended Project Structure

```text
src/
├── frontend/               # Next.js Browser Widget
│   ├── components/         # UI Components (LiveKit Room, Voice Button)
│   ├── app/api/token/      # Token generation API (Frappe Auth Validation)
│   └── Dockerfile          # Next.js container build
├── agent/                  # Python LiveKit Agent Worker
│   ├── agent.py            # Main agent logic (OpenAI Realtime setup)
│   ├── requirements.txt    # Dependencies (livekit-agents, etc.)
│   └── Dockerfile          # Agent container build
├── mcp-server/             # Frappe MCP Server (Standalone)
│   ├── index.ts            # MCP Server setup
│   ├── tools/              # Frappe specific tool definitions
│   └── Dockerfile          # MCP Server container
├── infra/                  # Infrastructure configuration
│   ├── caddy/Caddyfile     # Reverse proxy rules
│   ├── livekit.yaml        # LiveKit server config
│   └── docker-compose.yml  # System orchestrator
```

### Structure Rationale

- **Multi-container setup:** Follows the "external Standalone-Lösung" constraint. The architecture is fully decoupled from Frappe's internal bench/app structure.
- **Separation of Concerns:** The `agent/` handles voice/LLM orchestration, while the `mcp-server/` encapsulates all Frappe-specific API knowledge. The `frontend/` acts purely as the user interface bridging Frappe context with LiveKit.

## Architectural Patterns

### Pattern 1: Delegated Authentication via Connection Metadata

**What:** The Frappe Session ID or API Key is captured by the Next.js widget (which is embedded in Frappe) and passed to the LiveKit Server as connection metadata during token generation. The Agent receives this metadata when joining the room and forwards it to the MCP Server.
**When to use:** To ensure the Agent only acts with the strict permissions of the currently logged-in Frappe user.
**Trade-offs:** Requires secure transport of Frappe tokens. Keeps the Agent Worker completely stateless regarding user identity.

**Example:**
```python
# In agent.py when handling a new room connection
@worker.on("room_joined")
async def on_room_joined(room: rtc.Room):
    metadata = room.metadata # Contains Frappe Auth Context
    # Initialize MCP Client with this auth context
```

### Pattern 2: Dynamic Tool Discovery (MCP)

**What:** The Python LiveKit Agent does not hardcode Frappe tools. It uses `livekit.agents.llm.mcp.MCPServerHTTP` to dynamically discover available tools from the Frappe MCP Server.
**When to use:** Standard pattern for LiveKit Agents in 2026 interacting with external systems.
**Trade-offs:** Adds a network hop for tool execution, but perfectly decouples the voice agent from the rapidly changing ERP schema.

### Pattern 3: Speech-to-Speech Streaming (OpenAI Realtime)

**What:** Bypassing traditional STT -> LLM -> TTS pipelines by using the OpenAI Realtime API via WebSockets.
**When to use:** When low latency (< 500ms) voice interaction is critical (Typ A Agent).
**Trade-offs:** Tightly couples the implementation to OpenAI's specific API. Can be more expensive than modular approaches.

## Data Flow

### Request Flow (Voice & Tool Invocation)

```text
[User Speaks]
    ↓ (WebRTC Audio Track)
[LiveKit Server]
    ↓ (Audio Stream)
[Python Agent Worker]
    ↓ (WebSocket Streaming)
[OpenAI Realtime API]
    ↓ (Function Call JSON)
[Python Agent (MCP Client)]
    ↓ (HTTP JSON-RPC)
[Frappe MCP Server]
    ↓ (REST API Call)
[Frappe / ERPNext]
```

### Suggested Build Order (Phase Dependencies)

1. **Infrastructure:** LiveKit Server + Caddy Reverse Proxy.
2. **Frontend Component:** Next.js Widget capable of connecting to a LiveKit room.
3. **Agent Core:** Python Agent Worker implementing OpenAI Realtime (able to speak back, no tools yet).
4. **Integration Layer:** Frappe MCP Server defining read-only tools.
5. **Orchestration:** Connecting the Python Agent to the MCP Server and handling the Authentication pass-through from Frontend to Frappe.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-50 concurrent calls | Single Docker Compose host (monolith deployment) is perfectly fine. |
| 50-500 concurrent calls | Split Agent Workers to multiple replicas. LiveKit can stay on a single robust node. |
| 500+ concurrent calls | LiveKit distributed deployment backed by Redis. Agent Workers auto-scaled based on active rooms. |

### Scaling Priorities

1. **First bottleneck:** OpenAI Realtime API rate limits. Ensure tier limits are raised before scaling infrastructure.
2. **Second bottleneck:** Python Agent Worker CPU usage. Since Python has the GIL, each room typically runs concurrently but heavy processing blocks the event loop. Scale by adding more worker containers.

## Anti-Patterns

### Anti-Pattern 1: Hardcoding Frappe Logic in the Agent

**What people do:** Writing Frappe API endpoints directly inside `agent.py` using `@agent.tool`.
**Why it's wrong:** Tightly couples the voice infrastructure with ERP business logic. Makes it impossible to reuse the tools for text-based chats or other LLMs without rewriting the agent.
**Do this instead:** Expose all Frappe interactions via the isolated Frappe MCP Server and connect to it dynamically.

### Anti-Pattern 2: Local VAD/STT with Realtime API

**What people do:** Implementing local Voice Activity Detection (VAD) or Speech-to-Text before sending to OpenAI.
**Why it's wrong:** OpenAI Realtime API handles VAD natively for much lower latency and better interruption handling (barge-in).
**Do this instead:** Stream raw audio tracks directly from LiveKit to the OpenAI Realtime WebSocket.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI Realtime | WebSocket streaming via `livekit.agents` | Requires `OPENAI_API_KEY` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Frontend ↔ LiveKit | WebRTC | Handled by LiveKit React SDK |
| Agent ↔ LiveKit | WebRTC / Server SDK | Handled by LiveKit Python SDK |
| Agent ↔ MCP Server | HTTP / SSE (JSON-RPC) | Standardized via `MCPServerHTTP` |
| MCP Server ↔ Frappe | HTTP REST | Requires passing the Frappe Auth token |

## Sources

- LiveKit Agents Documentation (MCP Integration)
- Model Context Protocol (MCP) Specification
- OpenAI Realtime API Documentation

---
*Architecture research for: Voice-Assistent für Frappe*
*Researched: 2026-04-18*