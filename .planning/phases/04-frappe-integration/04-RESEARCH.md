# Phase 4: Frappe Integration - Research

**Researched:** 2026-04-19  
**Domain:** LiveKit Agent MCP-Client-Integration mit Frappe MCP Server  
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
- **D-11:** Beim Session-Start werden Prompt-Bausteine via MCP aus Frappe Notes geladen.
- **D-12:** Der System-Prompt wird aus zwei Quellen zusammengefuehrt: Public Notes der Instanz plus Notes, die dem Agent-Frappe-User zugewiesen sind.
- **D-13:** Falls Frappe/MCP nicht erreichbar ist, nutzt der Agent eine ENV-Baseline als Notfall-Persona.
- **D-14:** Pro Deployment gibt es genau eine Agent-Frappe-User-Identitaet und damit genau ein Persona-Set.
- **D-15:** Phase 4 startet mit Lazy Load ohne Cache; Session-Caching ist nur als spaetere Optimierung bei realem Bedarf vorgesehen.

### Claude's Discretion
- Konkrete technische Struktur fuer Session-Lifecycle-Hooks (solange D-01/D-02 eingehalten werden).
- Konkretes Wording der Permission-Fehlermeldungen je Kanal (Voice/Text), solange sie klar und nicht-technisch sind.
- Technische Umsetzung des Prompt-Merge (Reihenfolge/Trennformat), solange Public + Assigned Notes enthalten sind.

### Deferred Ideas (OUT OF SCOPE)
- Voice-Safety-Bestaetigung fuer potenziell schreibende Tool-Calls wird separat diskutiert (eigener Punkt/Topic 6).
- Multi-Agent-pro-Deployment ist Backlog fuer Phase 5+ (aktuell 1 Persona pro Deployment).
- Notes-Scoping ueber ein Custom Field auf dem Note-Doctype (z. B. `ai_agent_visibility`) als Content-Scoping-Mechanismus fuer Multi-Agent-Deployments: Notes koennen auf bestimmte Agent-IDs begrenzt werden, ohne separate Frappe-User. Das ist kein Permission-Layer. Default-Verhalten: Notes ohne dieses Feld sind fuer alle Agenten sichtbar (Firmenwissen). Phase-5+-Backlog, gemeinsam mit Multi-Agent-pro-Deployment zu betrachten.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INTG-01 | `mcp` Python SDK in den Agent Worker integrieren | Standard Stack (mcp + livekit-agents[mcp]), Codebeispiele fuer `mcp.MCPServerHTTP` |
| INTG-02 | Verbindung zum externen Frappe MCP-Server + Auth mit festen Agent-Credentials | Auth-Pattern via `headers` auf `MCPServerHTTP`, ENV-only Credential-Strategie |
| INTG-03 | Agent agiert mit uebergebenen Credentials als eigener Agenten-User | Architekturmuster "dedicated MCP identity", keine Frontend/User-Credential-Umschaltung |
| INTG-04 | Dynamische Tool-Discovery, read-only, keine direkten Frappe-API-Aufrufe/hardcoded Doctypes | MCP-Discovery nativ in LiveKit, Verzicht auf lokale Doctype-Logik, Delegation an Frappe-Server-Rollen |
| INTG-05 | Graceful Error Handling fuer 403/Opaque Errors | Pitfall-/Pattern-Abschnitt fuer 403 ohne Retry, userfreundliche Antwort + strukturiertes Logging |
</phase_requirements>

## Project Constraints (from .cursor/rules/)

- Vor Commits gilt ein verpflichtender Anti-Drift-Check (`ls -la`, Dateianzahl, kritische Git-Dateien pruefen); bei Treffern Commit abbrechen.
- Bei jeder Phase vor Transition muss eine `OPERATOR-HANDOVER.md` mit Pflichtabschnitten vorhanden sein.
- Aktive Architekturentscheidungen aus `.planning/PROJECT.md` (Key Decisions) und `.planning/STATE.md` (Accumulated Decisions) sind bindend.
- Dokumentation darf keine veralteten/abgeschalteten ENV-Funktionen als aktiv darstellen; auf jeweilige Decision verweisen.
- Uebergangsloesungen muessen explizit als temporaer markiert werden.

## Summary

Phase 4 sollte als saubere Erweiterung des bereits bestehenden `AgentSession`-Lifecycles in `apps/agent/agent.py` umgesetzt werden: MCP-Verbindung wird pro Session aufgebaut, Tools werden zur Laufzeit vom Frappe MCP Server entdeckt, und Authentifizierung erfolgt ausschliesslich ueber feste Agent-Credentials aus ENV. Die LiveKit-Dokumentation bestaetigt, dass MCP in Python nativ ueber `mcp.MCPServerHTTP(...)` in `AgentSession`/`Agent` integriert wird und Discovery automatisch erfolgt.

Die read-only-Anforderung darf nicht lokal per Toolnamen gefiltert werden (entsprechend D-06), sondern muss serverseitig durch Frappe-Rollen/Allowlist erzwungen werden. Recherche zu realen Frappe-MCP-Servern zeigt: etablierte Implementierungen bieten explizite Doctype-/Operation-Allowlists und liefern 403 bei unzulaessigen Zugriffen. Das passt direkt zu INTG-05: 403 wird als erwartete Fachgrenze behandelt (kein Retry), sprachlich nutzerfreundlich kommuniziert und strukturiert mit Korrelation geloggt.

Prompt-Ladung aus Frappe Notes kann in denselben Session-Init-Pfad gelegt werden wie MCP-Verbindungsaufbau; bei Ausfall muss ein ENV-basierter Fallback aktiv bleiben. Damit bleiben Phase-3-Funktionalitaet und Session-Stabilitaet erhalten, waehrend Phase-4-Ziele ohne Architekturbruch erreicht werden.

**Primary recommendation:** MCP-Integration direkt in `AgentSession` mit `mcp.MCPServerHTTP(url, headers=...)` implementieren, 403 als nicht-retrybaren Berechtigungsfall behandeln, und Read-only strikt an Frappe-MCP-Server-Policies delegieren.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `livekit-agents[mcp]` | 1.5.4 (published 2026-04-16) | Native MCP client support im LiveKit Agent | Offizielle LiveKit-Doku fuer MCP-Tooling und Session-Integration |
| `mcp` | 1.27.0 (published 2026-04-02) | MCP Protokoll-SDK (Python) | Referenz-SDK des MCP-Standards; transport-/lifecycle-konform |
| `livekit-plugins-openai` | 1.5.4 (published 2026-04-16) | Realtime LLM/TTS/STT Plugin-Kompatibilitaet | Version-synchron zu `livekit-agents` 1.5.x |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-dotenv` | vorhandene Projektdependency | Laden fixer Agent-Credentials aus ENV | Immer fuer lokale/dev/runtime ENV-Konfiguration |
| `pytest` + `pytest-asyncio` | vorhanden (`pytest 9.0.3`) | Async Tests fuer MCP/Auth/Fehlerpfade | Fuer INTG-02..05 Testabdeckung |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `AgentSession` MCP-Einbindung | MCP nur auf `Agent` setzen | `Agent`-Wert ueberschreibt Session-Wert; hoehere Verwechslungsgefahr im Workflow |
| Serverseitige Read-only-Policy | Client-seitige lokale Tool-Allowlist | Widerspricht D-05/D-06 und driftet von realen Serverrechten weg |
| Feste MCP-URL mit auto transport | Explizit `transport_type` forcieren | Nur noetig bei nicht-standardisierten Endpunkten (`/mcp` vs `/sse`) |

**Installation:**
```bash
pip install "livekit-agents[mcp]==1.5.4" "livekit-plugins-openai==1.5.4" "mcp==1.27.0"
```

**Version verification:**  
- `livekit-agents`: 1.5.4 (PyPI upload: 2026-04-16T04:50:43Z)  
- `livekit-plugins-openai`: 1.5.4 (PyPI upload: 2026-04-16T04:52:11Z)  
- `mcp`: 1.27.0 (PyPI upload: 2026-04-02T14:48:07Z)

## Architecture Patterns

### Recommended Project Structure
```text
apps/agent/
├── agent.py                 # Session lifecycle + MCP wiring + error mapping
├── src/                     # Optional extraction for MCP/prompt services
├── tests/
│   ├── test_agent.py        # Existing baseline
│   └── test_mcp_integration.py  # New INTG coverage
└── .env.example             # Agent credential contract
```

### Pattern 1: Session-scoped MCP lifecycle
**What:** MCP server objekt pro Agent-Session erzeugen, Session-Ende = implizites Cleanup.  
**When to use:** Immer fuer D-01/D-02 und zur Vermeidung globaler Verbindungsteilung.  
**Example:**
```python
# Source: https://docs.livekit.io/agents/logic/tools/mcp.md
from livekit.agents import AgentSession, mcp

session = AgentSession(
    llm=model,
    mcp_servers=[
        mcp.MCPServerHTTP(
            "https://frappe.example.com/mcp",
            headers={"Authorization": f"token {api_key}:{api_secret}"},
        )
    ],
)
```

### Pattern 2: Dynamic discovery, no app-side doctype logic
**What:** MCP Tools werden vom Server geladen; Client kodiert keine Doctype-Spezifika.  
**When to use:** Fuer INTG-04 und D-05/D-07 durchgehend.  
**Example:**
```python
# Source: https://docs.livekit.io/agents/logic/tools/mcp.md
# Tools are automatically loaded from MCP server and combined with function tools.
session = AgentSession(mcp_servers=[mcp.MCPServerHTTP("https://.../mcp")])
```

### Pattern 3: Permission-aware error translation
**What:** 403/Permission/Opaque-Error auf nutzerfreundliche Einschrankungsantwort mappen; kein Retry.  
**When to use:** Bei Tool-Fehlern in INTG-05.  
**Example:**
```python
# Source: project requirement INTG-05 + MCP lifecycle/error guidance
if is_permission_error(err):  # status == 403 or permission marker
    logger.warning("mcp_permission_denied", extra={"correlation_id": cid, "tool": tool_name})
    return "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff."
```

### Anti-Patterns to Avoid
- **Lokale Read-only Heuristik:** Toolnamen wie `create_*` clientseitig filtern statt serverseitiger Allowlist.
- **Credential mixing:** Frontend- oder User-Credentials fuer denselben Agent nutzen (widerspricht D-03/D-04).
- **Retry auf 403:** fuehrt zu unnutzbarer Latenz und schlechter UX ohne fachlichen Mehrwert.
- **Direkter REST-Fallback zu Frappe:** verletzt MCP-Reinheit (D-07).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP Handshake/Tool discovery | Eigene JSON-RPC Discovery-Engine | `livekit.agents.mcp.MCPServerHTTP` | Lifecycle/Capabilities sind spezifiziert und bereits robust implementiert |
| Read-only enforcement | Lokale Toolname-Filter | Frappe MCP Allowlist + Rollen | Berechtigungswahrheit liegt am Datenrand, nicht im Voice-Agent |
| Credential orchestration | Per-Request dynamische User-Token-Switches | Feste Agent-Credentials via ENV | Entspricht D-03/D-04 und reduziert Sicherheits-/State-Komplexitaet |
| Retry-Strategie fuer 403 | Generisches Exponential Backoff auf alle Fehler | 403 als terminale Fachgrenze behandeln | Schnellere, klarere UX; keine sinnlosen Wiederholungen |

**Key insight:** In dieser Domäne ist Zuverlaessigkeit primär ein Protokoll-/Policy-Thema. Eigene Zwischenlogik erzeugt Drift gegen MCP/Frappe-Policies.

## Common Pitfalls

### Pitfall 1: MCP endpoint/transport mismatch
**What goes wrong:** Verbindung klappt nicht, obwohl URL erreichbar wirkt.  
**Why it happens:** Endpunktpfad (`/mcp` vs `/sse`) passt nicht zum erwarteten Transport.  
**How to avoid:** Standardisierte Pfade verwenden oder `transport_type` explizit setzen.  
**Warning signs:** Init-Fehler vor erstem Tool-Call, keine Tools im Session-Context.

### Pitfall 2: 403 als technischer statt fachlicher Fehler behandelt
**What goes wrong:** Agent klingt "kaputt" oder bleibt stumm statt Rechtegrenze zu erklaeren.  
**Why it happens:** Fehlerbehandlung auf Exceptions-only statt UX-orientierter Mapping-Logik.  
**How to avoid:** 403 explizit abfangen, userfreundliche Antwort, kein Retry, strukturierter Logeintrag.  
**Warning signs:** Wiederholte identische Tool-Calls, lange Pausen, technische Fehlermeldungen im Voice-Kanal.

### Pitfall 3: Prompt source race at session start
**What goes wrong:** Persona ist inkonsistent oder leer beim ersten Turn.  
**Why it happens:** Prompt-Note-Laden laeuft parallel/zu spaet zum Session-Start.  
**How to avoid:** Deterministische Reihenfolge: MCP init -> Notes laden/mergen -> Session starten; fallback auf ENV.  
**Warning signs:** Erstantwort ohne erwartete Persona oder wechselnde Tonalitaet zwischen Sessions.

## Code Examples

Verified patterns from official sources:

### MCP server with auth headers
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

### MCP in session entrypoint (reference recipe)
```python
# Source: https://docs.livekit.io/reference/recipes/http_mcp_client.md
session = AgentSession(
    vad=ctx.proc.userdata["vad"],
    stt="deepgram/nova-3-general",
    llm="openai/gpt-5.3-chat-latest",
    tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
    mcp_servers=[mcp.MCPServerHTTP(url="https://shayne.app/mcp")],
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Eigene Tool-Bridge pro Datenquelle | MCP-native tool discovery direkt in Agent SDK | LiveKit Agents 1.4+ MCP support | Weniger Glue-Code, schnelleres Onboarding neuer MCP Server |
| Statische Prompt-Dateien als Hauptquelle | Laufzeit-Prompt aus Systemquelle (hier: Frappe Notes) mit Fallback | Projektentscheidung D-A + Phase-4 scope | Persona zentral administrierbar ohne Redeploy |
| "Retry everything" auf Toolfehler | Fehlerklassenspezifische Behandlung (insb. 403 terminal) | Reife von Agent-Observability + UX patterns | Niedrigere Latenz, bessere Nutzerkommunikation |

**Deprecated/outdated:**
- Direkte Frappe-REST-Aufrufe im Agenten fuer Fachdaten (nicht mehr vereinbar mit D-07).
- App-seitige Doctype-Hardcodings statt serverseitiger MCP-Policies.

## Open Questions

1. **Welcher konkrete MCP Endpoint (Path + Transport) wird pro Deployment genutzt?**
   - What we know: LiveKit kann `/mcp` und `/sse` automatisch erkennen.
   - What's unclear: Zielserver-URL/Path ist noch nicht als ENV-Vertrag dokumentiert.
   - Recommendation: In Wave 0 einen verbindlichen ENV-Key (`FRAPPE_MCP_URL`) plus Beispieldefault definieren.

2. **Welche Frappe-Tools liefern die "public + assigned notes" exakt?**
   - What we know: Decision D-11/D-12 fordert beide Quellen via MCP.
   - What's unclear: Konkrete Toolnamen/Filtersyntax des Zielservers.
   - Recommendation: Vor Implementierung mit `tools/list` gegen Zielserver inventarisieren und in Tests fixieren.

3. **Wie wird "read-only trotz write-tools im Server" policy-seitig garantiert?**
   - What we know: Reale Frappe-MCP-Server bieten operation-level Allowlist.
   - What's unclear: Konfiguration der Zielinstanz fuer Agent-User.
   - Recommendation: Operator-Checkliste um expliziten Allowlist-Audit fuer Agent-User erweitern.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Agent worker + MCP SDK | ✓ | 3.13.7 | — |
| pip | Dependency install | ✓ | 25.2 | uv/pipx optional |
| Node.js | Optional MCP ecosystem tooling | ✓ | 22.22.0 | — |
| npm | Optional toolchain | ✓ | 11.5.1 | — |
| pytest | Nyquist tests | ✓ | 9.0.3 | — |
| Docker | Containerized local validation | ✗ | — | Lokal ohne Docker testen; CI/Operator fuer container-run |
| Frappe MCP endpoint URL | INTG-02 runtime connection | ✗ (nicht konfiguriert) | — | Blocker fuer echte E2E-Integration |
| Agent Frappe credentials in env | INTG-02/03 auth | ✗ (nicht in .env.example) | — | Wave-0 ENV-Erweiterung erforderlich |

**Missing dependencies with no fallback:**
- Konkrete MCP Ziel-URL + produktive Agent-Credentials fuer echtes Integrations-E2E.

**Missing dependencies with fallback:**
- Docker lokal fehlt; Unit-/Integrationstests koennen dennoch direkt in Python laufen.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` + `pytest-asyncio` |
| Config file | `apps/agent/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest apps/agent/tests/test_mcp_integration.py -x -q` |
| Full suite command | `pytest apps/agent/tests -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INTG-01 | MCP SDK wired into agent session | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_session_has_mcp_server -x -q` | ❌ Wave 0 |
| INTG-02 | MCP HTTP connection uses fixed env credentials | unit/integration | `pytest apps/agent/tests/test_mcp_integration.py::test_mcp_headers_from_env -x -q` | ❌ Wave 0 |
| INTG-03 | Agent acts with dedicated identity only | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_no_runtime_credential_switch -x -q` | ❌ Wave 0 |
| INTG-04 | Dynamic tool discovery, no direct Frappe API fallback | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_no_direct_frappe_api_calls -x -q` | ❌ Wave 0 |
| INTG-05 | 403 handled gracefully without crash/retry | unit | `pytest apps/agent/tests/test_mcp_integration.py::test_permission_error_user_friendly_no_retry -x -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest apps/agent/tests/test_mcp_integration.py -x -q`
- **Per wave merge:** `pytest apps/agent/tests -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `apps/agent/tests/test_mcp_integration.py` — deckt INTG-01..05 ab
- [ ] `apps/agent/.env.example` — MCP-spezifische ENV keys (`FRAPPE_MCP_URL`, Credentials)
- [ ] Fehlerklassifikation helper (z. B. `is_permission_error`) + Tests fuer 403/Opaque

## Sources

### Primary (HIGH confidence)
- LiveKit docs: MCP integration (`https://docs.livekit.io/agents/logic/tools/mcp.md`) - `MCPServerHTTP`, headers, tool discovery, placement semantics
- LiveKit recipe (`https://docs.livekit.io/reference/recipes/http_mcp_client.md`) - end-to-end session wiring pattern
- MCP lifecycle spec (`https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle`) - initialization/capability/shutdown rules
- PyPI JSON + index (`https://pypi.org/pypi/livekit-agents/json`, `https://pypi.org/pypi/mcp/json`) - current package versions/dates
- Local project artifacts (`.planning/phases/04-frappe-integration/04-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/PROJECT.md`, `apps/agent/agent.py`)

### Secondary (MEDIUM confidence)
- `https://raw.githubusercontent.com/appliedrelevance/frappe-mcp-server/main/README.md` - Frappe MCP server capabilities/auth patterns
- `https://raw.githubusercontent.com/mascor/frappe-mcp-server/main/README.md` - allowlist/read-only/403 behavior in production-like setup

### Tertiary (LOW confidence)
- Web search result aggregation for Frappe MCP auth patterns (nur als Seed, anschliessend durch README-Quellen verifiziert)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verifiziert via LiveKit + PyPI live data
- Architecture: HIGH - direkt aus LiveKit MCP docs + bestehenden Projektentscheidungen
- Pitfalls: MEDIUM - Mischung aus Spezifikation, Praxisquellen und Projektspezifika

**Research date:** 2026-04-19  
**Valid until:** 2026-05-19
