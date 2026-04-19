# Operator Handover - Phase 04 Frappe Integration

## Coolify-ENV-Variablen

| Name | Zweck | Default | Beispielwert | Hinweis |
| --- | --- | --- | --- | --- |
| `FRAPPE_MCP_URL` | MCP-Endpunkt der Frappe-Instanz fuer Tool-Discovery und Calls | leer | `https://frappe.example.com/mcp` | Pflicht fuer MCP-Core (Decision D-03, D-05) |
| `FRAPPE_API_KEY` | Agent-Credential Key fuer MCP-Auth | leer | `agent_key_xxx` | Nur dedizierter Agent-User, kein Runtime-Switch (Decision D-03, D-04) |
| `FRAPPE_API_SECRET` | Agent-Credential Secret fuer MCP-Auth | leer | `agent_secret_xxx` | Nur dedizierter Agent-User, kein Runtime-Switch (Decision D-03, D-04) |
| `ROLE_DESCRIPTION` | Prompt-Baseline aus Phase 3 | `You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.` | `You are {AGENT_NAME}...` | Uebergangsloesung — wird in Phase 5 durch Frappe-Notes ersetzt (Decision D-A) |
| `AGENT_NAME` | Prompt-Baseline Platzhalter aus Phase 3 | `Assistant` | `ERP Assistant` | Uebergangsloesung — wird in Phase 5 durch Frappe-Notes ersetzt (Decision D-A) |
| `COMPANY_NAME` | Prompt-Baseline Platzhalter aus Phase 3 | `Frappe` | `Acme GmbH` | Uebergangsloesung — wird in Phase 5 durch Frappe-Notes ersetzt (Decision D-A) |
| `NEXT_PUBLIC_GDPR_NOTICE` | Browser-Hinweistext fuer DSGVO im Frontend | leer | leer | im aktuellen Architekturstand ungenutzt — siehe Decision D-B |

## Konfigurierbare Komponenten

- MCP-Zielinstanz ueber `FRAPPE_MCP_URL` (Kundeninstanz pro Deployment).
- MCP-Authentifizierung ueber `FRAPPE_API_KEY` und `FRAPPE_API_SECRET` des dedizierten Agent-Users.
- Frappe-seitige Rollen/Allowlist des Agent-Users fuer read-only Zugriff (Decision D-06).
- Prompt-Baseline-Werte (`ROLE_DESCRIPTION`, `AGENT_NAME`, `COMPANY_NAME`) bleiben bis Phase 5 konfigurierbar, sind aber als Uebergang markiert (Decision D-A).

## Nicht-konfigurierbare Komponenten

- Keine direkten Frappe-REST-Calls im Agenten (strikte MCP-Reinheit, Decision D-07).
- Kein Credential-Switch auf Frontend-/Enduser-Token zur Laufzeit (Decision D-04).
- Permission-Fehler (z. B. 403) werden ohne Retry mit fixer, nutzerfreundlicher Meldung beantwortet (Decision D-08, D-09).
- Structured Logging fuer Permission-Pfade mit `correlation_id` und Tool-Kontext ist fest implementiert (Decision D-10).

## Handover-Checkliste fuer den Onboarding-Termin

- [ ] Betreiber stellt dedizierten Frappe-Agent-User bereit (eigene API Credentials, minimale Rollen).
- [ ] `FRAPPE_MCP_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` in Coolify gesetzt und auf korrekten Scope validiert.
- [ ] MCP-Discovery gegen Zielinstanz pruefen (Tools werden dynamisch geliefert, keine lokale Allowlist).
- [ ] Permission-Test durchfuehren: absichtlich verbotenen Tool-Call ausloesen und nutzerfreundliche Antwort ohne Retry verifizieren.
- [ ] Logcheck: `mcp_permission_denied` enthaelt `correlation_id` und Toolname.
- [ ] Offene Scope-Grenze kommunizieren: Prompting aus Frappe-Notes ist out-of-scope in Phase 4 und fuer Phase 5 eingeplant (Decision D-A).
- [ ] Folgende Artefakte an Operator uebergeben: `.planning/phases/04-frappe-integration/04-03-SUMMARY.md`, `.planning/phases/04-frappe-integration/04-03-PLAN.md`, `.planning/STATE.md`.
