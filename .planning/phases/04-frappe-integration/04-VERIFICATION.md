---
phase: 04-frappe-integration
verified: 2026-04-19T16:47:00Z
status: human_needed
score: 3/3 must-haves verified
human_verification:
  - test: "Live-MCP Discovery gegen Zielinstanz"
    expected: "Agent sieht zur Laufzeit die realen read-only MCP-Tools der Frappe-Instanz"
    why_human: "Externer MCP-Server und reale Toolliste sind lokal nicht deterministisch pruefbar"
  - test: "End-to-End Read-Only Datenabfrage"
    expected: "Agent beantwortet eine echte Frappe-Datenfrage mit MCP-Tooldaten und ohne direkte REST-Bypaesse"
    why_human: "Erfordert laufende Frappe-Datenbasis, MCP-Endpoint und Voice-Session"
  - test: "403-Rechtefall in Live-System"
    expected: "Bei fehlender Berechtigung kommt die nutzerfreundliche Meldung ohne Retry/Crash"
    why_human: "Realer Permission-Zustand muss gegen echte Rollen/Policies validiert werden"
---

# Phase 4: Frappe Integration Verification Report

**Phase Goal:** The voice agent connects to Frappe using dedicated credentials and securely relays read-only data.
**Verified:** 2026-04-19T16:47:00Z
**Status:** human_needed
**Re-verification:** No - initial verification (vorherige VERIFICATION ohne `gaps`-Block)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Agent verbindet sich mit Frappe MCP und nutzt dynamische Tool-Discovery (read-only) | ? UNCERTAIN | `agent.py` nutzt `AgentSession(..., mcp_servers=[build_frappe_mcp_server()])`, statische Allowlist fehlt; Live-Discovery gegen echte Instanz ist offline nicht beweisbar |
| 2 | MCP-Authentifizierung erfolgt mit festen Agent-Credentials aus ENV | ✓ VERIFIED | `build_frappe_mcp_server()` liest exakt `FRAPPE_MCP_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET`, bildet Header `token {api_key}:{api_secret}` |
| 3 | Nutzeranfragen koennen lesend ueber Frappe-MCP beantwortet werden | ? UNCERTAIN | MCP-Wiring, No-Bypass-Guards und Tests vorhanden; echter read-only Datenabruf braucht laufende Zielinstanz |
| 4 | Bei Permission-Fehlern reagiert der Agent stabil und nutzerfreundlich statt zu crashen | ✓ VERIFIED | `map_mcp_error_to_user_message` + `is_permission_error` + Logging mit `correlation_id` + Tests fuer Marker und No-Retry |

**Score:** 4/4 Roadmap-Success-Criteria im Repo statisch abgedeckt; 2 davon mit zwingendem Live-Nachweis.

### Must-Haves (Plan 04-04)

| # | Must-have truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Agent-Worker startet ohne MCP-ImportError und bleibt bis Session-Join lauffaehig | ✓ VERIFIED | `python -m pytest apps/agent/tests/test_mcp_integration.py -q` (15 passed), inkl. `test_mcp_module_import_available` und `test_agent_module_import_does_not_raise_mcp_import_error` |
| 2 | MCP-Anbindung bleibt mit dedizierten Agent-Credentials konfigurierbar und testbar | ✓ VERIFIED | ENV-Contract in `.env.example`; Factory und Header-Format in `src/frappe_mcp.py`; Guard-Tests fuer fehlende ENV-Werte |
| 3 | UAT kann Discovery, read-only Abfrage und 403-Verhalten wieder real pruefen | ✓ VERIFIED | Runtime-Blocker (MCP-Import) beseitigt, Testpfad gruen; reale UAT-Schritte dokumentiert in `04-HUMAN-UAT.md` und weiter als Human-Check offen |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `apps/agent/pyproject.toml` | UV-Dependency-Contract mit MCP-Support | ✓ VERIFIED | `livekit-agents[mcp,openai,silero,turn-detector]~=1.5` vorhanden |
| `apps/agent/requirements.txt` | Pip-Runtime-Contract mit MCP-Support | ✓ VERIFIED | `livekit-agents[mcp,openai]~=1.5` vorhanden |
| `apps/agent/tests/test_mcp_integration.py` | Regression- und Integrationsnachweise | ✓ VERIFIED | 15 Tests, inkl. Import/ENV/Cleanup/Discovery/Permission |
| `apps/agent/src/frappe_mcp.py` | ENV+Auth-Factory fuer MCP-Server | ✓ VERIFIED | ValueError bei fehlenden Keys, Header-Format korrekt |
| `apps/agent/agent.py` | Session-scoped MCP-Wiring und Cleanup | ✓ VERIFIED | `mcp_servers=[build_frappe_mcp_server()]`, Cleanup via `aclose/close/shutdown` |
| `apps/agent/src/mcp_errors.py` | Permission-Fehlerklassifikation | ✓ VERIFIED | Marker-basierte Erkennung (`403`, `permission denied`, `not permitted`, `insufficient permissions`) |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `apps/agent/pyproject.toml` | `apps/agent/agent.py` | `livekit-agents[...mcp...]` | ✓ WIRED | MCP-Extra in Haupt-Dependencies vorhanden |
| `apps/agent/requirements.txt` | `apps/agent/agent.py` | `livekit-agents[...mcp...]` | ✓ WIRED | MCP-Extra im Pip-Runtime-Pfad vorhanden |
| `apps/agent/tests/test_mcp_integration.py` | `apps/agent/src/frappe_mcp.py` | `build_frappe_mcp_server`/MCP-Import | ✓ WIRED | Direkter Import + Assertions auf Header und Missing-ENV |
| `apps/agent/agent.py` | `apps/agent/src/mcp_errors.py` | `is_permission_error(err)` | ✓ WIRED | Mapping im Fehlerpfad vor Nutzerantwort |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `apps/agent/src/frappe_mcp.py` | `url`, `api_key`, `api_secret` | Prozess-ENV via `os.getenv` | Ja (konfigurationsgetrieben) | ✓ FLOWING |
| `apps/agent/agent.py` | `session.mcp_servers` | `build_frappe_mcp_server()` | Ja (Serverobjekt wird injiziert) | ✓ FLOWING |
| `apps/agent/agent.py` | MCP-Tool-Discovery/Antwortdaten | Externer Frappe-MCP zur Laufzeit | Nicht offline nachweisbar | ? EXTERNAL_HUMAN_CHECK |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| MCP-Integrationsguards inkl. Import-Regression | `python -m pytest apps/agent/tests/test_mcp_integration.py -q` | `15 passed in 1.55s` | ✓ PASS |
| Agent-Basistests kompatibel mit MCP-Wiring | `python -m pytest apps/agent/tests/test_agent.py -q` | `4 passed in 4.41s` | ✓ PASS |
| Direkter MCP-Import im Runtime-Interpreter | `python -c "from livekit.agents import mcp; print('mcp-ok')"` | `mcp-ok` | ✓ PASS |
| Live-MCP Discovery + read-only Datenfluss | nicht offline testbar | laufende Zielinstanz/Voice-Session notwendig | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| INTG-01 | `04-01-PLAN.md`, `04-04-PLAN.md` | `mcp` Python SDK in Agent Worker integrieren | ✓ SATISFIED | MCP-Imports/Factory + Integrationstests vorhanden |
| INTG-02 | `04-01-PLAN.md`, `04-04-PLAN.md` | Verbindung + Auth mit dedizierten Agent-Credentials | ✓ SATISFIED | ENV-Contract + Header-Pattern + Fail-Fast bei fehlenden Keys |
| INTG-03 | `04-02-PLAN.md`, `04-04-PLAN.md` | Agent agiert mit eigener Agent-Identitaet | ✓ SATISFIED | Kein Runtime-Credential-Switch, Session-Wiring nur via Factory |
| INTG-04 | `04-02-PLAN.md`, `04-04-PLAN.md` | Dynamische read-only Discovery, keine API-Bypaesse | ? NEEDS HUMAN | Kein direkter REST-Bypass im Code; Live-Discovery/Read-only auf Zielsystem offen |
| INTG-05 | `04-03-PLAN.md`, `04-04-PLAN.md` | Graceful Error Handling fuer 403/Opaque Errors | ✓ SATISFIED | `mcp_errors.py`, User-Mapping in `agent.py`, Logging/Tests vorhanden |

Alle Requirement-IDs aus allen Phase-04-PLAN-Frontmattern (`INTG-01` bis `INTG-05`) sind in `.planning/REQUIREMENTS.md` vorhanden und in der obigen Tabelle accounted for. Keine orphaned Requirement-ID fuer Phase 4 gefunden.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| - | - | Keine blockierenden TODO/FIXME/Placeholder- oder Stub-Pattern in den verifizierten Phase-4-Codepfaden gefunden | - | - |

### Human Verification Required

### 1. Live Discovery auf Zielinstanz
**Test:** Agent gegen echte Frappe-MCP-URL starten und Toolliste zur Laufzeit pruefen.  
**Expected:** Agent nutzt die vom MCP gelieferten read-only Tools ohne lokale Allowlist.  
**Why human:** Externe Endpoint- und Rechtekonfiguration sind nicht rein statisch verifizierbar.

### 2. End-to-End read-only Datenabfrage
**Test:** Nutzer fragt nach konkreten Frappe-Daten; Agent antwortet mit MCP-Resultat.  
**Expected:** Antwort basiert auf Datenzugriff des Agent-Users, ohne direkte REST-Bypaesse.  
**Why human:** Benoetigt laufenden Frappe-Server, reale Daten und Voice-Session.

### 3. Permission-Negativtest (403)
**Test:** Verbotenen Tool-Call oder Datensatz gezielt ausloesen.  
**Expected:** Meldung "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff." ohne Retry-Loop oder Crash.  
**Why human:** Reale 403-/Opaque-Antworten haengen von Zielsystem und Rollen ab.

### Gaps Summary

Keine Code-Gaps gefunden; Artefakte, Wiring und Import-Runtime sind im Repository nachweisbar. Verbleibend ist ausschliesslich externer Laufzeitnachweis auf der echten Frappe-Instanz, daher `human_needed` statt `gaps_found`.

---

_Verified: 2026-04-19T16:47:00Z_  
_Verifier: Claude (gsd-verifier)_
