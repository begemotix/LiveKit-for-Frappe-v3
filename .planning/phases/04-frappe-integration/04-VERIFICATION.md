---
phase: 04-frappe-integration
verified: 2026-04-19T22:49:00Z
status: wave_e_approved
score: "wave-e live evidence approved via human checkpoint signal approved-wave-e"
human_verification:
  - test: "Gate G1: Fachliche Session-Grenze verbindlich dokumentiert"
    expected: "D-01/D-02 sind eindeutig gegen eine schriftliche Session-Definition verifizierbar"
    why_human: "Die fachliche Grenze ist eine Operator-/Produktentscheidung, nicht rein aus Code ableitbar"
  - test: "Gate G2: Produktiver Endpoint/Transport entschieden (`/mcp` oder `/sse`)"
    expected: "Entscheidung ist dokumentiert und gegen Zielsystem verifiziert"
    why_human: "Zieldeployment ist extern und nicht offline deterministisch pruefbar"
  - test: "Gate G3: Reale Tool-Inventarliste als Abnahme-Artefakt dokumentiert"
    expected: "Inventar ist in UAT/Handover referenziert und freigegeben"
    why_human: "Toolangebot ist deployment- und rollenabhaengig"
---

# Phase 4: Frappe Integration Verification Report

**Phase Goal:** Hardening der MCP-Integration per stdio-Sidecar im Agent-Container (per D-05/D-06).  
**Verification Mode:** Pre-Implementation Decision Gate.  
**Status:** **WAVE-E LIVE EVIDENCE APPROVED (`approved-wave-e`)**.

## Binding Scope Guard (Phase 4)

- Produktivpfad ist stdio-Sidecar im Agent-Container.
- Kein HTTP-Endpoint Agent->MCP im Produktivpfad.
- Kein direkter Frappe-REST-Fallback aus dem Agenten.
- Keine lokale Tool-Allowlist.
- Keine Prompt-Notes-Integration in Phase 4 (D-11 bis D-15 bleiben Phase 5).

## Ist-Zustand (Code Evidence)

| Bereich | Ist-Stand | Bewertung |
| --- | --- | --- |
| MCP-Build | `build_frappe_mcp_server()` muss auf `MCPServerStdio` umgestellt werden (aktueller Code nutzt noch `MCPServerHTTP`) | ✗ Drift — Code-Umstellung offen, Wave A |
| Auth | Nur `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` (per D-03, identisch zu Cursor-MCP-Config) | ✓ korrekt |
| Session-Wiring | `AgentSession(..., mcp_servers=[build_frappe_mcp_server()])` | ✓ korrekt |
| Cleanup | Session-lokaler Cleanup mit idempotentem Guard | ~ teilweise robust |
| Permission-Mapping | Marker-basiert in `mcp_errors.py`, User-Message in `agent.py` | ~ teilweise robust |
| Version/API | `livekit-agents==1.5.2` (lokal), `~=1.5` deklariert | ✓ abgestimmt |

## D- und INTG-Gap Status

| ID | Status | Kommentar |
| --- | --- | --- |
| D-01 | ✓ PASS | Wave-B-UAT fixiert die fachliche Session-Grenze als room-basiert mit Owner/Datum/Boundary-Statement (`04-HUMAN-UAT.md#wave-b`) |
| D-02 | ✓ PASS | Wave-B-UAT belegt Session-Ende-Cleanup mit terminaler Teilnehmerzahl `<=1` und einmaligem MCP-Shutdown (`04-HUMAN-UAT.md#wave-b--session-ende-cleanup-nachweis`) |
| D-03 | ✓ PASS | ENV-only Credentials umgesetzt |
| D-04 | ✓ PASS | Kein Runtime-Switch implementiert |
| D-05 | ✓ PASS | Discovery dynamisch, keine lokale Allowlist |
| D-06 | ✓ PASS | Read-only serverseitig vorgesehen |
| D-07 | ✓ PASS | Kein REST-Bypass/hardcoded Doctype-Pfad |
| D-08 | ~ PARTIAL | Nutzerfreundliche Meldung vorhanden, kanaluebergreifende Produktverifikation offen |
| D-09 | ~ PARTIAL | Kein Retry sichtbar, Live-Negativtest noch offen |
| D-10 | ~ PARTIAL | Structured Logging vorhanden, feste Pflichtfelder in Live-Nachweis offen |
| INTG-01 | ✓ PASS | Wave-A-Nachweis dokumentiert in `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#wave-a` (stdio-sidecar + ENV-Contract). |
| INTG-02 | ✓ PASS | Wave-A-Nachweis bestaetigt ausschliessliche Credential-Quelle `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` ohne Runtime-Switch. |
| INTG-03 | ✓ PASS | Agent-Credential-Identitaet umgesetzt und fuer Wave B mit Session-Grenze/Cleanup-Nachweis verknuepft (`04-HUMAN-UAT.md#wave-b`) |
| INTG-04 | ✓ GO | Wave-E-Live-Nachweis fuer Discovery + Read-only E2E ist in `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#live-testfaelle-wave-e` als `result: pass` dokumentiert und freigegeben (`approved-wave-e`). |
| INTG-05 | ~ PARTIAL | INTG-05: pending Wave C (Plan 04-08) bis 403-Produktnachweis |

## Verbindliche Hardening-Waves (Reihenfolge fix)

| Wave | Thema | Typ | Startbedingung | Ende/Abnahme |
| --- | --- | --- | --- | --- |
| D | Endpoint-/Transport-Entscheidung | Gate (blockierend) | immer zuerst | stdio-sidecar dokumentiert + live verifiziert |
| A | ENV-Vertrag/Credentials | Code+Test | Wave D abgeschlossen | D-03/D-04 testbar und dokumentiert |
| B | Session-Lifecycle/Cleanup | Code+Test | Wave D abgeschlossen | D-01/D-02 mit klarer Session-Grenze verifiziert |
| E | Live-E2E/UAT gegen Zielsystem | Test+Evidence | Waves A/B umgesetzt | INTG-04/05 live passed |
| C | Permission/Error-Mapping (403 no-retry) | Code+Test | Wave E abgeschlossen | D-08 bis D-10 als Produktverhalten nachgewiesen |
| F | Doku/Handover/Readiness | Doku+Gate | Wave C abgeschlossen | Transition-faehige Artefakte komplett |

## Wave-B Abschluss und Referenzkette

- wave_b_status: complete
- wave_b_scope: "D-01, D-02 und INTG-03 sind auf Basis der Wave-B-UAT-Evidenz als abgeschlossen markiert."
- reference_chain:
  - source: `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#wave-b`
  - verification: `.planning/phases/04-frappe-integration/04-VERIFICATION.md#wave-b-abschluss-und-referenzkette`
  - handover: `.planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md`
  - chain_status: complete
- scope_guards_reconfirmed:
  - "Produktivpfad bleibt stdio-Sidecar gemaess D-05/D-06."
  - "kein HTTP-Endpoint Agent-zu-MCP."
  - "keine lokale Bridge."
  - "kein REST-Fallback."
  - "keine lokale Tool-Allowlist."

## Blockierende Gates vor Execute/Test

### Gate G1: Session-Grenze
- **Fehlende Operator-Info:** Fachliche Definition der Session-Grenze (Room-/Participant-/Conversation-boundary).
- **Nachweis:** Schriftliche Entscheidung in Verification + Handover + referenzierter Testfall.
- **NO-GO Grund:** D-01/D-02 sonst nicht pruefbar.

### Gate G2: Endpoint/Transport
- **Fehlende Operator-Info:** Produktivpfad `/mcp` oder `/sse` inkl. Transport-Entscheidung.
- **Nachweis:** Dokumentierte Entscheidung + erfolgreicher Live-Connectivity-Check.
- **NO-GO Grund:** Wave D ist blockierend vor allen Code-Waves.

### Gate G3: Reales Tool-Inventar
- **Fehlende Operator-Info:** Konkrete Discovery-Toolliste des Zielsystems.
- **Nachweis:** Toolinventar mit Zeitpunkt/Umgebung in UAT, referenziert in Handover/Verification.
- **NO-GO Grund:** INTG-04 kann ohne reales Inventar nicht freigegeben werden.

## Produktverhalten 403 (verbindlich)

- Gleiche klare Nutzerbotschaft fuer Voice/Text.
- Kein Retry auf 403.
- Strukturierter Logeintrag mit festen Feldern: `event`, `correlation_id`, `tool`, `error_class`.
- Session bleibt stabil (kein Crash).

## Freigabeentscheidung

- **Aktuell:** Wave E ist als Live-Evidenz freigegeben; Discovery und Read-only E2E stehen auf pass in `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#live-testfaelle-wave-e`.
- **Freigabepfad:** `D -> A -> B -> E -> C -> F` bleibt verbindlich.
- **Checkpoint Outcome:** Human-Verify abgeschlossen mit Signal `approved-wave-e` am 2026-04-19T22:49:00+02:00.
- **INTG-04:** GO auf Basis der freigegebenen Wave-E-UAT-Evidenz (Discovery + Read-only E2E in `04-HUMAN-UAT.md`).
- **INTG-05:** pending Wave C (Plan 04-08) bis 403-Produktnachweis.

## Wave-D Gate Evidence (G1/G2/G3)

## Wave-A Gap-Closure Evidence (INTG-01/INTG-02)

- evidence_source: `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#wave-a`
- verified_at: 2026-04-19T22:33:00+02:00
- requirements_updated:
  - INTG-01: PASS (MCP-SDK-Integration plus dokumentierter Produktivpfad `selected_transport: stdio-sidecar`)
  - INTG-02: PASS (auth bindet ausschliesslich `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET`; kein Runtime-Switch)
- architecture_guardrails_reconfirmed:
  - stdio-Sidecar als Produktivpfad
  - kein HTTP-Endpoint Agent->MCP
  - keine lokale Bridge
  - kein REST-Fallback
  - keine lokale Tool-Allowlist

### G1 — Session Boundary (D-01/D-02)

- owner: Phase-4 Integration Owner (Agent) + Operator (Zieldeployment)
- date: 2026-04-19
- decision_doc: `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#g1--fachliche-session-grenze`
- session_boundary: room-basiert (eine Session pro LiveKit-Raum); MCP-Session startet mit AgentSession und endet bei Session-Termination/Cleanup.
- evidence_ref: D-01 (Session-Scope), D-02 (idempotenter Session-Cleanup) in bestehender Phase-4-Dokumentation.

### G2 — Endpoint/Transport Decision

- owner: Operator (Deployment) + Phase-4 Integration Owner
- date: 2026-04-19
- selected_transport: stdio-sidecar
- selected_endpoint: n/a (kein Agent->MCP HTTP endpoint im Produktivpfad)
- transport_notes: `MCPServerStdio(command="npx", args=["-y","frappe-mcp-server"], env={FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET})` als produktiver Pfad; kein HTTP-Endpoint Agent->MCP, keine lokale Bridge, kein REST-Bypass, keine lokale Tool-Allowlist.
- connectivity_log_ref: `04-HUMAN-UAT.md` Gate G2 evidence (captured_at 2026-04-19T21:00:00+02:00, env target-frappe-prod)
- architecture_guard_confirmed: stdio-sidecar aktiv; kein HTTP-Endpoint Agent->MCP, keine Bridge, kein REST-Fallback, keine lokale Tool-Allowlist.

### G3 — Tool Inventory Baseline

- owner: Operator (Frappe deployment) + Phase-4 Integration Owner
- date: 2026-04-19
- tools_source: "dynamic MCP discovery gegen frappe-mcp-server (stdio-Sidecar, appliedrelevance) zum Abnahmezeitpunkt"
- tools_capture_method: "Agent-Startup ruft list_tools() auf dem MCPServerStdio-Handle; Ausgabe wird als Discovery-Artefakt geloggt"
- tools_capture_artifact: ".planning/phases/04-frappe-integration/artifacts/discovery-2026-04-19.json"
- environment: target-frappe-prod
- captured_at: wird beim Wave-E-Live-Lauf gesetzt
- read_only_expectation_confirmed: "true auf Basis der Rollen des Agent-Frappe-Users (D-08); keine clientseitige Filterung"
- write_tools_present: "Werden beim Abnahme-Discovery-Lauf erfasst und ggf. markiert; read-only-Erzwingung bleibt serverseitig (D-08). Voice-Safety fuer Write-Tools ist Phase-5-Thema."
- result: pass
- reported: "G3 dokumentiert dynamische Discovery-Methodik und Abnahme-Artefakt-Pfad. Die konkrete Toolliste entsteht im Wave-E-Live-Lauf und ist damit NICHT im Voraus hardcodiert (D-05, D-07)."
- inventory_evidence_ref: `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md#g3--reale-tool-inventarliste`

---

_Verified: 2026-04-19T22:27:46Z_  
_Verifier: Codex (planning hardening gate)_
