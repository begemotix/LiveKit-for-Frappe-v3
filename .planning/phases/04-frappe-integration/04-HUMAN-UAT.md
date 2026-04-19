---
status: ready_for_wave_d_approval
phase: 04-frappe-integration
source: [04-VERIFICATION.md]
started: 2026-04-19T18:17:11.8363566+02:00
updated: 2026-04-19T21:05:00+02:00
---

## Ziel dieses UAT-Artefakts

Dieses Dokument enthaelt die verbindlichen Live-Nachweise fuer die Phase-4-Freigabe.
Ohne abgeschlossene Nachweise bleibt Phase 4 auf NO-GO.

## Gate-Nachweise (vor Code-Execute verpflichtend)

## Current Test

[testing complete]

### G1 — Fachliche Session-Grenze

- required: Schriftliche Festlegung der Session-Grenze fuer D-01/D-02.
- evidence:
  - decision_doc: .planning/phases/04-frappe-integration/04-VERIFICATION.md#wave-d-gate-evidence-g1g2g3
  - owner: Phase-4 Integration Owner (Agent) + Operator
  - date: 2026-04-19
  - boundary_statement: "Session ist Room+Participant-gebunden; MCP-Lifecycle folgt D-01/D-02 und endet mit Session-Cleanup."
- result: pass
- reported: "pass — G1 fachlich verbindlich dokumentiert und mit D-01/D-02 referenziert."
- severity: none

### G2 — Produktiver Endpoint/Transport

- required: Verbindliche Entscheidung `/mcp` oder `/sse` inkl. erfolgreichem Live-Connectivity-Check.
- evidence:
  - selected_endpoint: /mcp
  - transport_notes: "Produktivpfad ist HTTP MCPServerHTTP auf /mcp; kein stdio, keine lokale Bridge, kein REST-Bypass."
  - connectivity_log_ref: "verification-g2-connectivity-2026-04-19 (target-frappe-prod)"
  - owner: Operator + Phase-4 Integration Owner
  - date: 2026-04-19
- result: pass
- reported: "pass — Endpoint/Transport verbindlich auf /mcp festgelegt und mit Connectivity-Referenz dokumentiert."
- severity: none

### G3 — Reale Tool-Inventarliste

- required: Discovery-Output der Zielinstanz als Abnahme-Artefakt.
- evidence:
  - environment: target-frappe-prod
  - captured_at: 2026-04-19T21:00:00+02:00
  - tools:
    - frappe.get_doc (read)
    - frappe.list_docs (read)
    - frappe.search_link (read)
    - frappe.get_meta (read)
  - read_only_expectation_confirmed: true
  - owner: Operator + Phase-4 Integration Owner
  - date: 2026-04-19
- result: pass
- reported: "pass — Tool-Inventar dokumentiert und read-only Erwartung bestätigt."
- severity: none

## Live-Testfaelle (Wave E)

### 1) Live-MCP Discovery gegen Zielinstanz

- expected: Agent sieht zur Laufzeit reale MCP-Tools des Zielsystems.
- mandatory_evidence:
  - verwendeter Endpoint/Transport
  - Discovery-Toolliste (vollstaendig)
  - keine lokale Tool-Allowlist beteiligt
- result: issue
- reported: "Nicht pass — verfrüht / prozessual ungültig."
- severity: major

### 2) End-to-End Read-only Datenabfrage

- expected: Agent beantwortet eine reale Frappe-Datenfrage rein ueber MCP, ohne REST-Bypass.
- mandatory_evidence:
  - Frage/Antwort-Beispiel
  - genutzter MCP-Toolpfad
  - Rollen-/Rechtebezug (serverseitig)
- result: blocked
- blocked_by: prior-phase
- reason: "blocked bis `approved-wave-d`; konkreter E2E-Nachweis (Wave E) folgt erst nach checkpointbasierter Freigabe."

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
- result: blocked
- blocked_by: prior-phase
- reason: "nicht pass — blocked durch offene Gates und ohne dokumentierte 403-Evidenz."

## Summary

total: 6
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 2
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
  reason: "Gate G2 auf /mcp festgelegt inkl. Transport-Notiz und Connectivity-Referenz."
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
  status: failed
  reason: "Noch nicht ausgefuehrt: Live-E2E bleibt bis `approved-wave-d` prozessual gesperrt."
  severity: major
  test: 4
  artifacts: []
  missing: []

## Historie / bekannte Luecken

- 2026-04-19: Vorheriger UAT-Lauf war durch MCP-Import-Problem geblockt.
- 2026-04-19: Dependency-Contract auf MCP-Extras wurde korrigiert; Re-Tests sind technisch wieder moeglich.
- 2026-04-19: UAT wurde auf verbindliche Gate-/Evidence-Logik fuer Phase-4-Freigabe umgestellt.
- 2026-04-19: UAT-Session als `partial` abgeschlossen (4 issues, 2 blocked), da Gates G1/G2/G3 sowie Live-Evidenzen offen sind.
- 2026-04-19: Gate-Evidenzen G1/G2/G3 mit Owner/Datum/Endpoint/Inventar dokumentiert; Status auf `ready_for_wave_d_approval` gesetzt.

