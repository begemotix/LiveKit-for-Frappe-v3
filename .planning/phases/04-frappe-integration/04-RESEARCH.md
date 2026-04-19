# Phase 4: Frappe Integration - Research

**Researched:** 2026-04-19
**Domain:** LiveKit Agent + Frappe MCP (read-only voice data relay)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### MCP Session Lifecycle
- **D-01:** MCP-Verbindung wird pro Agent-Session aufgebaut und innerhalb dieser Session wiederverwendet.
- **D-02:** Session-lokale MCP-Verbindung wird sauber beendet, sobald die Agent-Session endet.

### Credential Strategy
- **D-03:** Der Agent authentifiziert sich ausschliesslich mit festen Agent-Credentials aus ENV.
- **D-04:** Es gibt keinen Runtime-Switch auf Frontend- oder User-Credentials.

### Tool Discovery and MCP Purity
- **D-05:** Tools werden dynamisch ueber MCP Discovery bezogen; es gibt keine app-seitige Allowlist.
- **D-06:** Read-only ist Verantwortung des Frappe-MCP-Servers und der Rollen des Agent-Frappe-Users, nicht einer lokalen Tool-Filterlogik.
- **D-07:** Strikte MCP-Reinheit bleibt bestehen: keine direkten Frappe-API-Aufrufe und keine hardcodierten Doctype-Annahmen.

### Permission and Error Handling
- **D-08:** Bei 403/Permission-Problemen antwortet der Agent mit einer klaren, nutzerfreundlichen Einschrankungs-Meldung.
- **D-09:** 403-Fehler werden nicht erneut versucht (kein Retry auf fehlende Berechtigung).
- **D-10:** Fehlerpfade werden strukturiert geloggt (inkl. Korrelationsbezug), ohne Crash der Session.

### Prompt Source from Frappe Notes
- **D-11 (deferred to Phase 5):** Beim Session-Start werden Prompt-Bausteine via MCP aus Frappe Notes geladen.
- **D-12 (deferred to Phase 5):** Der System-Prompt wird aus zwei Quellen zusammengefuehrt: Public Notes der Instanz plus Notes, die dem Agent-Frappe-User zugewiesen sind.
- **D-13 (deferred to Phase 5):** Falls Frappe/MCP nicht erreichbar ist, nutzt der Agent eine ENV-Baseline als Notfall-Persona.
- **D-14 (deferred to Phase 5):** Pro Deployment gibt es genau eine Agent-Frappe-User-Identitaet und damit genau ein Persona-Set.
- **D-15 (deferred to Phase 5):** Phase 4 startet mit Lazy Load ohne Cache; Session-Caching ist nur als spaetere Optimierung bei realem Bedarf vorgesehen.

### Claude's Discretion
- Konkrete technische Struktur fuer Session-Lifecycle-Hooks (solange D-01/D-02 eingehalten werden).
- Konkretes Wording der Permission-Fehlermeldungen je Kanal (Voice/Text), solange sie klar und nicht-technisch sind.
- Prompting-Implementierung bleibt in Phase 4 unveraendert (Phase-3-Stand via Python-Konstanten/ENV); Details zu Notes-Merge werden in Phase 5 entschieden.

### Deferred Ideas (OUT OF SCOPE)
- Voice-Safety-Bestaetigung fuer potenziell schreibende Tool-Calls wird separat diskutiert (eigener Punkt/Topic 6).
- Multi-Agent-pro-Deployment ist Backlog fuer Phase 5+ (aktuell 1 Persona pro Deployment).
- Notes-Scoping ueber ein Custom Field auf dem Note-Doctype (z. B. `ai_agent_visibility`) als Content-Scoping-Mechanismus fuer Multi-Agent-Deployments: Notes koennen auf bestimmte Agent-IDs begrenzt werden, ohne separate Frappe-User. Das ist kein Permission-Layer. Default-Verhalten: Notes ohne dieses Feld sind fuer alle Agenten sichtbar (Firmenwissen). Phase-5+-Backlog, gemeinsam mit Multi-Agent-pro-Deployment zu betrachten.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INTG-01 | `mcp` Python SDK in den Agent Worker integrieren | Standard Stack + LiveKit MCP Pattern (`mcp.MCPServerHTTP`) |
| INTG-02 | Verbindung zum externen Frappe MCP-Server + Auth mit festen Agent-Credentials | ENV-only Credential Pattern + Auth Header Pattern |
| INTG-03 | Agent agiert mit uebergebenen Credentials als eigener Agenten-User | Architekturpattern "dedicated agent credentials only" |
| INTG-04 | Dynamische Tool-Discovery, read-only, keine direkten Frappe-API-Aufrufe/hardcoded Doctypes | MCP native discovery, keine lokale Allowlist, serverseitige read-only Policy |
| INTG-05 | Graceful Error Handling fuer 403/Opaque Errors | Permission marker mapping + no-retry + structured logging |
</phase_requirements>

## Project Constraints (from .cursor/rules/)

- Vor jedem Commit ist ein Anti-Drift-Reality-Check im Terminal Pflicht (`ls -la`, Dateianzahl, kritische Git-Dateien prüfen); bei Treffern Commit abbrechen.
- Vor Phase-Transition ist `OPERATOR-HANDOVER.md` in der Phase verpflichtend.
- Aktive Entscheidungen aus `.planning/PROJECT.md` und `.planning/STATE.md` gelten als bindend.
- Dokumentation darf keine laut Decision deaktivierten/späteren ENV-Funktionen als aktiv darstellen.
- Übergangslösungen müssen explizit als Übergang markiert werden.

## Summary

Die Kernfrage fuer diese Phase ist nicht mehr "ob MCP", sondern "wie strikt die vorhandenen Decisions operationalisiert werden". Der aktuelle Code in `apps/agent/agent.py` und `apps/agent/src/frappe_mcp.py` ist bereits nah am Zielbild: Session-scoped `mcp_servers`, feste ENV-Credentials, und zentrale Permission-Mapping-Logik. Die Planung sollte daher auf Luecken zwischen "funktioniert technisch" und "planbar/robust/verifizierbar in Betrieb" fokussieren.

LiveKit dokumentiert, dass MCP-Tools automatisch discovered werden, wenn `mcp.MCPServerHTTP(...)` auf `AgentSession` oder `Agent` gesetzt ist, inklusive Header-basierter Auth und optionaler Tool-Filter. Fuer dieses Projekt sind lokale Filter aber explizit unerwuenscht (D-05/D-06): read-only muss serverseitig ueber den Frappe-Agent-User und dessen Rechte erzwungen werden. Clientseitig bleibt nur saubere Fehleruebersetzung (403 -> nutzerfreundliche Antwort, kein Retry, korrelierter Log).

Da Prompt-Notes laut Context auf Phase 5 verschoben wurden, bleibt Phase 4 bewusst beim Phase-3-Promptpfad (Datei/ENV-Fallback). Das reduziert Scope-Risiko und erlaubt einen klaren Plan mit Fokus auf MCP-Verbindungs- und Berechtigungsverhalten.

**Primary recommendation:** Plane Phase 4 als Hardening-Phase der bereits vorhandenen MCP-Integration: Session-Lifecycle absichern, Dedicated-Credential-Vertrag fixieren, 403/opaque Fehlerpfade testbar machen und E2E gegen einen realen Frappe-MCP-Endpunkt verifizieren.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `livekit-agents[mcp]` | 1.5.4 | MCP-Client in `AgentSession`/`Agent`, Tool Discovery | Offizielle LiveKit MCP-Integration |
| `mcp` | 1.27.0 | MCP-Protokoll-Layer fuer HTTP/SSE/streamable transport | Referenzimplementierung des Protokolls |
| `livekit-plugins-openai` | 1.5.4 | Realtime-LMM/TTS/STT plugin alignment zu LiveKit 1.5.x | Vermeidet Plugin-Core Drift |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-dotenv` | installed (project dependency) | Laden fixer ENV-Credentials | Immer beim Worker-Start |
| `python-json-logger` | 2.0.7 installed (`4.1.0` latest) | Strukturierte Logs fuer Korrelation/Fehlerpfade | Bei allen MCP-Errorpfaden |
| `pytest` + `pytest-asyncio` | 9.0.3 / 1.3.0 | Async-Verifikation von Session/MCP/Cleanup | Fuer alle INTG-Reqs und Gate |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `mcp_servers` auf `AgentSession` | `mcp_servers` direkt auf `Agent` | `Agent` ueberschreibt Session-Defaults; hoehere Verwechslungsgefahr |
| Serverseitige read-only Policy | Lokale `allowed_tools` Filterung | Widerspricht D-06, verschiebt Security ins falsche System |
| Kein custom error mapping | Raw Exception an Nutzer weitergeben | Schlechtere UX, unklare Fachgrenze |

**Installation:**
```bash
pip install "livekit-agents[mcp]==1.5.4" "livekit-plugins-openai==1.5.4" "mcp==1.27.0"
```

**Version verification:** per `python -m pip index versions ...` und PyPI (`2026-04-19`):
- `livekit-agents` latest `1.5.4` (PyPI release date: 2026-04-16)
- `mcp` latest `1.27.0`
- `livekit-plugins-ai-coustics` latest `0.2.7` (Projekt nutzt `~=0.2`)
- Projektstand lokal: `livekit-agents 1.5.2` installiert -> Upgrade ist planbar, aber nicht zwingend fuer Phase-4-Planung

## Architecture Patterns

### Recommended Project Structure
```text
apps/agent/
├── agent.py                     # AgentSession lifecycle + event hooks
├── src/frappe_mcp.py            # ENV contract + MCPServerHTTP builder
├── src/mcp_errors.py            # Permission marker/mapping
├── tests/test_mcp_integration.py
└── .env.example                 # Runtime contract fuer dedicated creds
```

### Pattern 1: Session-scoped MCP server
**What:** MCP server wird pro Session erzeugt und beim Session-Ende geschlossen.  
**When to use:** Immer (D-01/D-02).  
**Example:**
```python
# Source: https://docs.livekit.io/agents/logic/tools/mcp.md
from livekit.agents import AgentSession, mcp

session = AgentSession(
    mcp_servers=[
        mcp.MCPServerHTTP(
            "https://frappe.example.com/mcp",
            headers={"Authorization": f"token {api_key}:{api_secret}"},
        )
    ]
)
```

### Pattern 2: Dynamic MCP discovery without app-side allowlist
**What:** Toolset kommt zur Laufzeit vom Server; Client kodiert keine festen Toolnamen.  
**When to use:** Immer fuer INTG-04 / D-05.  
**Example:**
```python
# Source: https://docs.livekit.io/agents/logic/tools/mcp.md
session = AgentSession(mcp_servers=[mcp.MCPServerHTTP("https://frappe.example.com/mcp")])
# Tools are auto-discovered by LiveKit.
```

### Pattern 3: Permission-aware error UX
**What:** Permissionfehler werden als fachliche Grenze kommuniziert, nicht als technischer Absturz.  
**When to use:** INTG-05 Fehlerpfad.  
**Example:**
```python
if is_permission_error(err):
    logger.warning("mcp_permission_denied", extra={"correlation_id": cid, "tool": tool_name})
    return "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff."
```

### Anti-Patterns to Avoid
- **Credential-Switching zur Laufzeit:** verletzt D-03/D-04.
- **Direkte Frappe REST Calls im Agent:** verletzt D-07 (MCP purity).
- **Retry auf 403:** erzeugt Latenz ohne Erfolg und degradiert UX.
- **Lokale read-only Heuristik:** driftet gegen serverseitige Rechtequelle.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP Discovery + Invocation | Eigene JSON-RPC Tool-Broker-Schicht | `mcp.MCPServerHTTP` in LiveKit | Standardisiert, stabil, weniger Wartung |
| Read-only enforcement | Lokale Regex/Allowlist fuer Toolnamen | Frappe-MCP Rollen/Permissions | Rechtehoheit bleibt am Datenrand |
| Fehlerklassifizierung | Ad-hoc Exception parsing in mehreren Files | Zentrales `is_permission_error` + message mapping | Konsistente UX + testbar |

**Key insight:** Das Risiko liegt weniger im Coding als in inkonsistenter Policy-Verteilung. MCP + Frappe-Rechte müssen die einzige Wahrheit bleiben.

## Common Pitfalls

### Pitfall 1: Transport mismatch (`/sse` vs `/mcp`)
**What goes wrong:** Server erreichbar, aber keine nutzbare MCP-Session.  
**Why it happens:** URL/Transport passt nicht zur Serverkonfiguration.  
**How to avoid:** Endpoint klar dokumentieren; ggf. `transport_type` explizit setzen.  
**Warning signs:** Toolliste leer, Setup-/Connect-Fehler vor erstem Call.

### Pitfall 2: Permissionfehler nicht als Produktverhalten modelliert
**What goes wrong:** Agent wirkt defekt statt limitiert.  
**Why it happens:** 403 wird als generischer technischer Fehler behandelt.  
**How to avoid:** 403 Marker zentral erkennen, klare Nutzerantwort, kein Retry, structured log.  
**Warning signs:** Wiederholte identische Aufrufe, technische Fehltexte in Voice-Antworten.

### Pitfall 3: Session cleanup race
**What goes wrong:** Offene MCP-Verbindung oder doppelte Cleanup-Aufrufe.  
**Why it happens:** Event-Reihenfolge bei `participant_disconnected` variiert.  
**How to avoid:** idempotentes Cleanup + terminale Bedingung (`<=1 participants`) wie im aktuellen Code.  
**Warning signs:** Intermittierende Flakes in Disconnect-Tests.

## Code Examples

Verified patterns from official sources:

### Authenticated MCP HTTP server
```python
# Source: https://docs.livekit.io/agents/logic/tools/mcp.md
from livekit.agents import AgentSession, mcp

session = AgentSession(
    mcp_servers=[
        mcp.MCPServerHTTP(
            "https://actions.zapier.com/mcp/sse",
            headers={"Authorization": f"Bearer {os.environ['ZAPIER_API_KEY']}"},
        )
    ]
)
```

### Session entrypoint with MCP server
```python
# Source: https://docs.livekit.io/recipes/http_mcp_client.md
session = AgentSession(
    stt="deepgram/nova-3-general",
    llm="openai/gpt-5.3-chat-latest",
    tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
    mcp_servers=[mcp.MCPServerHTTP(url="https://shayne.app/mcp")],
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Eigene Tool-Bridges je Datenquelle | MCP-native discovery in Agent SDK | LiveKit Agents 1.4+ | Weniger Glue-Code, klarere Verantwortung |
| SSE als impliziter Standard | streamable HTTP (`/mcp`) bevorzugt, SSE deprecating | In LiveKit MCP docs markiert | Endpoint-Design sollte `/mcp` priorisieren |
| Generische Retry-Strategie | Fehlerklassenspezifisch (403 terminal) | Observability/UX Reife in Agent-Systemen | Schnellere und verständlichere Nutzerantworten |

**Deprecated/outdated:**
- Direkte Datenzugriffe am MCP vorbei fuer Business-Queries.
- Lokale Tool-Allowlist als Security-Hauptmechanismus (in diesem Projekt-Setup).

## Open Questions

1. **Welche konkreten Toolnamen liefert der Ziel-Frappe-MCP-Server im Deployment?**
   - What we know: Discovery ist dynamisch und automatisch.
   - What's unclear: Reale Tool-Inventarliste der Zielinstanz.
   - Recommendation: In Wave 0 einmalige Tool-Inventory-Validierung gegen Zielsystem.

2. **Ist der produktive Endpoint als `/mcp` oder `/sse` konfiguriert?**
   - What we know: LiveKit erkennt automatisch.
   - What's unclear: Ziel-URL-Konvention im Operator-Setup.
   - Recommendation: In ENV-Dokumentation verbindlich festlegen.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Agent Worker Runtime | ✓ | 3.13.7 | — |
| pip | Package installation | ✓ | 25.2 | `uv pip` |
| uv | dependency workflow | ✓ | 0.11.7 | pip |
| pytest | Validation architecture | ✓ | 9.0.3 | — |
| Node.js/npm | optional MCP tooling ecosystem | ✓ | 22.22.0 / 11.5.1 | — |
| Docker | containerized local smoke checks | ✗ | — | lokale Python-Tests ohne Container |
| `FRAPPE_MCP_URL` | INTG-02 runtime connection | ⚠ (key vorhanden, Wert runtime-offen) | — | keine echte E2E ohne Ziel-URL |
| `FRAPPE_API_KEY` / `FRAPPE_API_SECRET` | INTG-02/03 authentication | ⚠ (keys vorhanden, Werte runtime-offen) | — | keine echte E2E ohne Secrets |

**Missing dependencies with no fallback:**
- Produktive Frappe-MCP-URL plus Agent-Credentials fuer echtes Integrations-E2E.

**Missing dependencies with fallback:**
- Docker fehlt lokal; Unit/Integrationstests laufen direkt via `pytest`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` + `pytest-asyncio` |
| Config file | `apps/agent/pyproject.toml` |
| Quick run command | `pytest apps/agent/tests/test_mcp_integration.py -x -q` |
| Full suite command | `pytest apps/agent/tests -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INTG-01 | MCP SDK wiring vorhanden | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_mcp_module_import_available -x -q` | ✅ |
| INTG-02 | ENV-basierte Auth-Header | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_build_frappe_mcp_server_uses_env_headers -x -q` | ✅ |
| INTG-03 | dedicated credentials, kein runtime switch | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_no_runtime_credential_switch -x -q` | ✅ |
| INTG-04 | dynamic discovery + no direct API fallback | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_dynamic_tool_discovery_runtime_evidence -x -q` | ✅ |
| INTG-05 | graceful permission handling | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_permission_error_user_friendly_no_retry -x -q` | ✅ |

### Sampling Rate
- **Per task commit:** `pytest apps/agent/tests/test_mcp_integration.py -x -q`
- **Per wave merge:** `pytest apps/agent/tests -q`
- **Phase gate:** Full suite green vor `/gsd-verify-work`

### Wave 0 Gaps
- [ ] E2E-Test gegen echten Frappe-MCP-Endpunkt (inkl. absichtlichem 403-Fall) fehlt.
- [ ] Optional: contract test fuer leere Toolliste (Server erreichbar, aber keine freigegebenen Tools).

## Sources

### Primary (HIGH confidence)
- [LiveKit MCP docs](https://docs.livekit.io/agents/logic/tools/mcp.md) - MCPServerHTTP, Auth-Header, Discovery, Placement rules.
- [LiveKit MCP recipe](https://docs.livekit.io/recipes/http_mcp_client.md) - End-to-end Session-Wiring.
- [LiveKit Python MCP API reference](https://docs.livekit.io/reference/python/livekit/agents/llm/mcp.html) - Klassenparameter, Transportverhalten, `allowed_tools`.
- [PyPI livekit-agents](https://pypi.org/project/livekit-agents/) - aktuelle Version und Veröffentlichungsdatum.
- Lokale Projektquellen: `.planning/phases/04-frappe-integration/04-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `apps/agent/agent.py`, `apps/agent/src/frappe_mcp.py`, `apps/agent/tests/test_mcp_integration.py`.

### Secondary (MEDIUM confidence)
- [PyPI mcp](https://pypi.org/project/mcp/) - Versionsabgleich für MCP-Protokollbibliothek.

### Tertiary (LOW confidence)
- Keine unverifizierten Tertiärquellen genutzt.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - offizielle LiveKit-Doku + PyPI live verifiziert.
- Architecture: HIGH - deckungsgleich mit lock decisions und aktuellem Code.
- Pitfalls: MEDIUM - teils aus Produktionsmustern abgeleitet, aber plausibel und testbar.

**Research date:** 2026-04-19
**Valid until:** 2026-05-19
