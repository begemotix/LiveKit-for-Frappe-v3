---
phase: 04-frappe-integration
verified: 2026-04-19T16:16:17Z
status: human_needed
score: 4/4 must-haves verified
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

**Phase Goal:** The voice agent connects to Frappe using its own dedicated credentials and securely relays read-only data
**Verified:** 2026-04-19T16:16:17Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Agent verbindet sich mit Frappe MCP und nutzt dynamische Tool-Discovery (read-only) | ? UNCERTAIN | `AgentSession(..., mcp_servers=[build_frappe_mcp_server()])` ist vorhanden; keine statische Allowlist, aber Discovery gegen Live-MCP nicht lokal nachweisbar |
| 2 | MCP-Authentifizierung erfolgt mit festen Agent-Credentials aus ENV | ✓ VERIFIED | `build_frappe_mcp_server()` liest exakt `FRAPPE_MCP_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` und setzt `Authorization: token key:secret`; Tests gruen |
| 3 | Nutzeranfragen koennen lesend ueber Frappe-MCP beantwortet werden | ? UNCERTAIN | Session-MCP-Wiring ist vorhanden, aber E2E gegen echte Instanz nicht automatisiert in Repo nachweisbar |
| 4 | Bei Permission-Fehlern reagiert der Agent stabil und nutzerfreundlich statt zu crashen | ✓ VERIFIED | `map_mcp_error_to_user_message` + `is_permission_error` + Tests fuer Marker/Logging/No-Retry vorhanden |

**Score:** 4/4 truths automated-verified within repository scope (2 davon mit externem Human-Nachweisbedarf)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `apps/agent/src/frappe_mcp.py` | MCP-Factory fuer URL/Auth-Vertrag | ✓ VERIFIED | Existiert, substantiell, ENV-Validation + Header-Format implementiert |
| `apps/agent/.env.example` | Verbindlicher ENV-Vertrag fuer MCP | ✓ VERIFIED | Enthalten: `FRAPPE_MCP_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` |
| `apps/agent/tests/test_mcp_integration.py` | Guard- und Integrations-Tests | ✓ VERIFIED | 13 Tests, inkl. Header, Missing ENV, Cleanup, Discovery-Guard, Permission-Handling |
| `apps/agent/agent.py` | Session-scoped MCP-Lifecycle + Error-Wiring | ✓ VERIFIED | MCP-Server wired, Cleanup-Hook, Permission-Mapping, keine direkte Frappe-REST-Nutzung |
| `apps/agent/src/mcp_errors.py` | Permission-Klassifikation | ✓ VERIFIED | Marker-basiert (`403`, `permission denied`, etc.) + User-Message Helper |
| `.planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md` | Pflicht-Handover inkl. 4 Sektionen | ✓ VERIFIED | Alle Pflichtabschnitte und Decision-Verweise vorhanden |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `apps/agent/.env.example` | `apps/agent/src/frappe_mcp.py` | `FRAPPE_MCP_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` | ✓ WIRED | ENV-Keys deklariert und exakt per `os.getenv(...)` gelesen |
| `apps/agent/agent.py` | `apps/agent/src/frappe_mcp.py` | `mcp_servers=[build_frappe_mcp_server()]` | ✓ WIRED | Direkter Import und Session-Wiring vorhanden |
| `apps/agent/agent.py` | `apps/agent/tests/test_mcp_integration.py` | Cleanup-Pfad (`aclose/close/shutdown`) | ✓ WIRED | Test `test_session_end_cleans_up_mcp_server` validiert deterministischen Cleanup |
| `apps/agent/agent.py` | `apps/agent/src/mcp_errors.py` | `is_permission_error(err)` | ✓ WIRED | Mapping-Funktion nutzt Permission-Klassifikation vor User-Antwort |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `apps/agent/src/frappe_mcp.py` | `url`, `api_key`, `api_secret` | Prozess-ENV (`os.getenv`) | Ja (konfigurationsgetrieben) | ✓ FLOWING |
| `apps/agent/agent.py` | `session.mcp_servers` | `build_frappe_mcp_server()` | Ja (MCP-Serverobjekt wird injiziert) | ✓ FLOWING |
| `apps/agent/agent.py` | Tool-Discovery/Read-Daten | Externer Frappe-MCP-Server zur Laufzeit | Nicht lokal beweisbar ohne Live-Endpoint | ? EXTERNAL_HUMAN_CHECK |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| MCP-Integrationsguards bestehen | `python -m pytest apps/agent/tests/test_mcp_integration.py -q` | `13 passed` | ✓ PASS |
| Agent-Basistests kompatibel mit MCP-Wiring | `python -m pytest apps/agent/tests/test_agent.py -q` | `4 passed` | ✓ PASS |
| Live-MCP Discovery/Read-only Response | nicht offline testbar | externer MCP/Frappe-Endpoint erforderlich | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| INTG-01 | `04-01-PLAN.md` | `mcp` Python SDK im Agent Worker integrieren | ✓ SATISFIED | `src/frappe_mcp.py` baut `mcp.MCPServerHTTP`; Integrationstest vorhanden |
| INTG-02 | `04-01-PLAN.md` | Verbindung + Auth mit dedizierten Agent-Credentials | ✓ SATISFIED | Exakte ENV-Keys + Header-Format + Missing-ENV-Failfast |
| INTG-03 | `04-02-PLAN.md` | Agent agiert mit eigener Agent-Identitaet | ✓ SATISFIED | Kein Runtime-Credential-Switch; MCP-Credentials nur aus Factory |
| INTG-04 | `04-02-PLAN.md` | Dynamische MCP-Discovery, read-only, keine direkten API-Bypaesse | ? NEEDS HUMAN | Wiring + No-Bypass verifiziert; Live-Discovery/Read-only real gegen Zielsystem offen |
| INTG-05 | `04-03-PLAN.md` | Graceful Error Handling fuer 403/Opaque Errors | ✓ SATISFIED | `mcp_errors.py`, Mapping in `agent.py`, Logging + Tests vorhanden |

Alle in den Plan-Frontmattern genannten Requirement-IDs (`INTG-01` bis `INTG-05`) sind in `.planning/REQUIREMENTS.md` vorhanden und damit vollstaendig accounted for. Keine orphaned Requirement-ID fuer Phase 4 gefunden.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| - | - | Keine blockierenden Stub-/Placeholder-Pattern in den verifizierten Phase-4-Codepfaden gefunden | - | - |

### Human Verification Required

### 1. Live Discovery auf Kundeninstanz
**Test:** Agent gegen echte Frappe-MCP-URL starten und Toolliste zur Laufzeit pruefen.  
**Expected:** Agent nutzt die vom MCP gelieferten read-only Tools ohne lokale Allowlist.  
**Why human:** Externe Endpoint- und Rechtekonfiguration sind nicht rein statisch verifizierbar.

### 2. E2E Datenfrage read-only
**Test:** Nutzer fragt nach konkreten Frappe-Daten (z. B. Kundenliste), Agent antwortet mit MCP-Resultat.  
**Expected:** Antwort kommt aus Frappe-Datenzugriff des Agent-Users; keine direkten REST-Bypaesse.  
**Why human:** Benoetigt laufenden Frappe-Server und reale Daten/ACLs.

### 3. Permission-Negativtest (403)
**Test:** Absichtlich verbotenen Datensatz/Tool aufrufen.  
**Expected:** Feste Meldung "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff." ohne Retry-Loop oder Crash.  
**Why human:** Reale 403-/Opaque-Antworten haengen von Zielsystem und Rollen ab.

### Gaps Summary

Keine Code-Gaps oder fehlenden Artefakte im Repository gefunden; die verbleibenden offenen Punkte sind externe Laufzeitnachweise (Live-MCP Discovery, echte Read-only Datenabfrage, reale 403-Situation). Daher `human_needed` statt `gaps_found`.

---

_Verified: 2026-04-19T16:16:17Z_  
_Verifier: Claude (gsd-verifier)_
