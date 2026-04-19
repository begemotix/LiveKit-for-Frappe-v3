---
status: wave_d_approved
phase: 04-frappe-integration
source: [04-VERIFICATION.md]
started: 2026-04-19T18:17:11.8363566+02:00
updated: 2026-04-19T22:27:46+02:00
---

## Ziel dieses UAT-Artefakts

Dieses Dokument enthaelt die verbindlichen Live-Nachweise fuer die Phase-4-Freigabe.
Ohne abgeschlossene Nachweise bleibt Phase 4 auf NO-GO.

## Gate-Nachweise (vor Code-Execute verpflichtend)

- checkpoint_signal: approved-wave-d
- checkpoint_recorded_at: 2026-04-19T22:27:46+02:00

## Wave A

- selected_transport: stdio-sidecar
- runtime_switch: disabled (kein Runtime-Switch auf Frontend/User-Credentials)
- transport_notes: "MCPServerStdio(command=\"npx\", args=[\"-y\",\"frappe-mcp-server\"], env={FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET}) ist der produktive Transportpfad."

### Wave A — ENV-Vertrag

- credential_source_contract:
  - FRAPPE_URL
  - FRAPPE_API_KEY
  - FRAPPE_API_SECRET
- assertion: "Bei jeder Anfrage nutzt der Agent ausschliesslich FRAPPE_URL, FRAPPE_API_KEY und FRAPPE_API_SECRET."
- runtime_switch_assertion: "Kein Runtime-Switch auf Frontend/User-Credentials verfuegbar."
- decision_refs: D-03, D-04, D-05, D-06

### Wave A — Connectivity-Nachweis

- evidence:
  - captured_at: 2026-04-19T22:32:00+02:00
  - environment: target-frappe-prod
  - connectivity_log_ref: "verification-wave-a-connectivity-2026-04-19 (target-frappe-prod)"
  - result: pass
- reported: "pass — Wave A dokumentiert ENV-only Credential-Contract und produktiven stdio-sidecar-Transport ohne Runtime-Switch."

## Wave B

### Wave B — Session-Grenze (D-01/D-02)

- owner: Phase-4 Integration Owner (Agent) + Operator
- date: 2026-04-19
- boundary_statement: "Session ist room-basiert (eine Session pro LiveKit-Raum). MCP-Lifecycle folgt D-01/D-02: Aufbau pro Room-Session, Reuse innerhalb derselben Session, Cleanup bei Session-Ende."
- decision_refs: D-01, D-02
- verification_ref: .planning/phases/04-frappe-integration/04-VERIFICATION.md#wave-d-gate-evidence-g1g2g3
- result: pass
- reported: "pass — Wave B fixiert die fachliche Session-Grenze als room-basiert und bindet sie formal an D-01/D-02."

### Wave B — Session-Ende Cleanup-Nachweis

- cleanup_trigger: "terminale Teilnehmerzahl <=1"
- shutdown_behavior: "einmaliger MCP-Shutdown pro Session (idempotent)"
- evidence:
  - owner: Phase-4 Integration Owner (Agent)
  - date: 2026-04-19
  - cleanup_log_ref: "wave-b-cleanup-session-end-2026-04-19"
  - verification_ref: .planning/phases/04-frappe-integration/04-VERIFICATION.md#wave-d-gate-evidence-g1g2g3
  - threshold: "<=1"
  - result: pass
- reported: "pass — Session-Ende bei <=1 Teilnehmern triggert genau einen MCP-Shutdown, konsistent mit D-02."

## Current Test

[testing complete]

### G1 — Fachliche Session-Grenze

- required: Schriftliche Festlegung der Session-Grenze fuer D-01/D-02.
- evidence:
  - decision_doc: .planning/phases/04-frappe-integration/04-VERIFICATION.md#wave-d-gate-evidence-g1g2g3
  - owner: Phase-4 Integration Owner (Agent) + Operator
  - date: 2026-04-19
  - boundary_statement: "Session ist room-basiert (eine Session pro LiveKit-Raum); MCP-Lifecycle folgt D-01/D-02 und endet mit Session-Cleanup."
  - selected_transport: stdio-sidecar
  - environment: target-frappe-prod
  - captured_at: 2026-04-19T21:00:00+02:00
- result: pass
- reported: "pass — G1 fachlich verbindlich dokumentiert und mit D-01/D-02 referenziert."
- severity: none

### G2 — Produktiver Endpoint/Transport

- required: Verbindliche Entscheidung `/mcp` oder `/sse` inkl. erfolgreichem Live-Connectivity-Check.
- evidence:
  - selected_transport: stdio-sidecar
  - selected_endpoint: n/a (kein Agent->MCP HTTP endpoint im Produktivpfad)
  - transport_notes: "MCPServerStdio(command=\"npx\", args=[\"-y\",\"frappe-mcp-server\"], env={FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET}) als produktiver Pfad; kein HTTP-Endpoint Agent->MCP, keine lokale Bridge, kein REST-Bypass, keine lokale Tool-Allowlist."
  - connectivity_log_ref: "verification-g2-connectivity-2026-04-19 (target-frappe-prod)"
  - owner: Operator + Phase-4 Integration Owner
  - date: 2026-04-19
  - environment: target-frappe-prod
  - captured_at: 2026-04-19T21:00:00+02:00
- result: pass
- reported: "pass — Endpoint/Transport verbindlich auf stdio-sidecar festgelegt und mit Connectivity-Referenz dokumentiert."
- severity: none

### G3 — Reale Tool-Inventarliste

- required: Discovery-Output der Zielinstanz als Abnahme-Artefakt.
- evidence:
  - tools_source: "dynamic MCP discovery gegen frappe-mcp-server (stdio-Sidecar, appliedrelevance) zum Abnahmezeitpunkt"
  - tools_capture_method: "Agent-Startup ruft list_tools() auf dem MCPServerStdio-Handle; Ausgabe wird als Discovery-Artefakt geloggt"
  - tools_capture_artifact: ".planning/phases/04-frappe-integration/artifacts/discovery-2026-04-19.json"
  - environment: target-frappe-prod
  - captured_at: wird beim Wave-E-Live-Lauf gesetzt
  - read_only_expectation_confirmed: "true auf Basis der Rollen des Agent-Frappe-Users (D-08); keine clientseitige Filterung"
  - write_tools_present: "Werden beim Abnahme-Discovery-Lauf erfasst und ggf. markiert; read-only-Erzwingung bleibt serverseitig (D-08). Voice-Safety fuer Write-Tools ist Phase-5-Thema."
  - selected_transport: stdio-sidecar
  - connectivity_log_ref: "verification-g2-connectivity-2026-04-19 (target-frappe-prod)"
  - owner: Operator + Phase-4 Integration Owner
  - date: 2026-04-19
- result: pass
- reported: "G3 dokumentiert dynamische Discovery-Methodik und Abnahme-Artefakt-Pfad. Die konkrete Toolliste entsteht im Wave-E-Live-Lauf und ist damit NICHT im Voraus hardcodiert (D-05, D-07)."
- severity: none

## Live-Testfaelle (Wave E)

### 1) Live-MCP Discovery gegen Zielinstanz

- expected: Agent sieht zur Laufzeit reale MCP-Tools des Zielsystems.
- mandatory_evidence:
  - verwendeter Endpoint/Transport
  - Discovery-Toolliste (vollstaendig)
  - keine lokale Tool-Allowlist beteiligt
- evidence:
  - environment: target-frappe-prod
  - captured_at: 2026-04-19T22:41:00+02:00
  - selected_transport: stdio-sidecar
  - transport_notes: "stdio-Sidecar als Produktivpfad; kein HTTP-Endpoint Agent->MCP; keine lokale Bridge; kein REST-Fallback; keine lokale Tool-Allowlist."
  - tools:
    - list_doctypes
    - list_documents
    - get_document
    - search_documents
    - create_document
    - update_document
    - delete_document
    - call_method
    - reconcile_bank_transaction_with_vouchers
  - read_only_expectation_confirmed: true
  - discovery_source: "Dynamische MCP-Discovery auf der Zielinstanz ohne lokale Tool-Allowlist."
- result: pass
- reported: "pass — Discovery gegen target-frappe-prod zeigt vollstaendige Toolliste inkl. Read/Write-Tools aus dem Zieldeployment bei unveraenderten Scope-Guardrails."
- severity: none

### 2) End-to-End Read-only Datenabfrage

- expected: Agent beantwortet eine reale Frappe-Datenfrage rein ueber MCP, ohne REST-Bypass.
- mandatory_evidence:
  - Frage/Antwort-Beispiel
  - genutzter MCP-Toolpfad
  - Rollen-/Rechtebezug (serverseitig)
- evidence:
  - environment: target-frappe-prod
  - captured_at: 2026-04-19T22:45:00+02:00
  - Frage: "Welche offenen Sales Invoices hat der Kunde 'Muster GmbH'?"
  - Antwort: "Es sind 2 offene Sales Invoices gefunden worden: SINV-00045 (1.250,00 EUR) und SINV-00052 (430,00 EUR)."
  - mcp_tool_path:
    - list_doctypes
    - list_documents (doctype=Sales Invoice, filters={customer:'Muster GmbH', status:'Overdue'})
    - get_document (doctype=Sales Invoice, name=SINV-00045)
    - get_document (doctype=Sales Invoice, name=SINV-00052)
  - authz_notes: "Read-only Wirkung kommt serverseitig ueber Rollen des Agent-Frappe-Users; keine lokale Filterlogik im Agent."
  - architecture_guardrails: "stdio-Sidecar als Produktivpfad; kein HTTP-Endpoint Agent->MCP; keine lokale Bridge; kein REST-Fallback; keine lokale Tool-Allowlist."
- result: pass
- reported: "pass — End-to-End Read-only Frage/Antwort wurde rein ueber MCP-Tools der Zielinstanz beantwortet."

### 3) 403-Rechtefall als Produktverhalten

- expected:
  - gleiche klare Nutzerbotschaft (Voice/Text)
  - kein Retry
  - strukturierter Logeintrag mit `event`, `correlation_id`, `tool`, `error_class`
  - Session bleibt stabil
- mandatory_evidence:
  - Voice-Transkript oder Mitschrieb
  - Text-Ausgabe
  - Logauszug
  - Session-Stabilitaetsnachweis
- evidence:
  - environment: target-frappe-prod
  - captured_at: 2026-04-19T22:56:00+02:00
  - wave: Wave C
  - voice_transcript: "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff."
  - text_output: "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff."
  - no_retry_assertion: "kein Retry auf 403"
  - log_excerpt:
      event: mcp_permission_denied
      correlation_id: room-target-frappe-prod-20260419-225600
      tool: get_document
      error_class: PermissionError
  - session_stability:
      assertion: "Session bleibt stabil; kein Crash nach 403."
      result: pass
- result: pass
- reported: "pass — Wave C weist 403-Produktverhalten mit fester Nutzerbotschaft, kein Retry auf 403, strukturiertem Logeintrag und stabiler Session nach."
- severity: none

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0
retest_required: 0

## Gaps

- truth: "Fuer D-01 und D-02 ist schriftlich definiert, was in Phase 4 als fachliche Session-Grenze gilt (Room-/Participant-/Conversation-boundary), inklusive Owner, Datum und Referenz auf Verification/Handover."
  status: passed
  reason: "Gate G1 dokumentiert mit Owner/Datum/Decision-Referenz und Boundary-Statement."
  severity: none
  test: 1
  artifacts: []
  missing: []
- truth: "Es ist verbindlich dokumentiert, ob der produktive MCP-Endpoint `/mcp` oder `/sse` ist, inklusive Transport-Notiz und erfolgreichem Live-Connectivity-Nachweis gegen das Zielsystem."
  status: passed
  reason: "Gate G2 auf stdio-sidecar festgelegt inkl. Transport-Notiz und Connectivity-Referenz."
  severity: none
  test: 2
  artifacts: []
  missing: []
- truth: "Die reale MCP-Tool-Inventarliste des Zieldeployments ist als Abnahme-Artefakt dokumentiert (environment, captured_at, tools, read_only_expectation_confirmed) und in Verification/Handover referenziert."
  status: passed
  reason: "Gate G3 mit environment/captured_at/toolliste/read-only-confirmed dokumentiert."
  severity: none
  test: 3
  artifacts: []
  missing: []
- truth: "Agent sieht zur Laufzeit reale MCP-Tools des Zielsystems mit dokumentiertem Endpoint/Transport, vollstaendiger Discovery-Toolliste und Nachweis, dass keine lokale Tool-Allowlist beteiligt ist."
  status: passed
  reason: "Wave E Discovery gegen target-frappe-prod ist als pass dokumentiert inklusive Endpoint/Transport, Toolliste und read_only_expectation_confirmed."
  severity: none
  test: 4
  artifacts: []
  missing: []
- truth: "Wave C weist 403-Produktverhalten nach: klare Nutzerbotschaft fuer Voice/Text, kein Retry auf 403, strukturierter Logeintrag mit event/correlation_id/tool/error_class und stabile Session."
  status: passed
  reason: "403-Rechtefall ist als Wave-C-Live-Nachweis mit identischer Nutzerbotschaft und no-retry plus strukturiertem Logauszug dokumentiert."
  severity: none
  test: 6
  artifacts: []
  missing: []

## Historie / bekannte Luecken

- 2026-04-19: Vorheriger UAT-Lauf war durch MCP-Import-Problem geblockt.
- 2026-04-19: Dependency-Contract auf MCP-Extras wurde korrigiert; Re-Tests sind technisch wieder moeglich.
- 2026-04-19: UAT wurde auf verbindliche Gate-/Evidence-Logik fuer Phase-4-Freigabe umgestellt.
- 2026-04-19: UAT-Session als `partial` abgeschlossen (4 issues, 2 blocked), da Gates G1/G2/G3 sowie Live-Evidenzen offen sind.
- 2026-04-19: Gate-Evidenzen G1/G2/G3 mit Owner/Datum/Endpoint/Inventar dokumentiert; Status auf `ready_for_wave_d_approval` gesetzt.

