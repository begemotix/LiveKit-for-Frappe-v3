# Operator Handover - Phase 04 Frappe Integration

## Phase-4 Freigabestatus

**Aktuell: Phase-4-Gap-Closure abgeschlossen (Wave F Dokumentation, 2026-04-19). Alle Waves D, A, B, E, C und F sind in dieser Reihenfolge dokumentarisch und evidenzbasiert geschlossen.**

1. Fachliche Session-Grenze (D-01/D-02) — Wave B / Gate G1
2. Produktiver Transport (**stdio-Sidecar**) mit Live-Nachweis — Wave D / Gate G2 (`selected_transport: stdio-sidecar`; **kein HTTP-Endpoint Agent->MCP**)
3. Reale Tool-Inventarliste aus dem Zieldeployment als Abnahme-Artefakt — Gate G3 / Wave E
4. Read-only E2E und Discovery — Wave E (`approved-wave-e`)
5. 403-Produktverhalten ohne Retry — Wave C
6. Betriebs- und Uebergabedokumentation — Wave F (dieses Paket)

Wave-Reihenfolge ist verbindlich: **D (blockierend) -> A -> B -> E -> C -> F**.
Exakte Ausfuehrungsreihenfolge (Resume-Check): `D -> A -> B -> E -> C -> F`.
Freigabesignale: `approved-wave-d` (Transport/Gates), `approved-wave-e` (Live-E2E INTG-04).

### Scope-Guards (Phase 4, keine Ausweitung)

- **stdio-Sidecar** als MCP-Produktivpfad; **kein HTTP-Endpoint Agent->MCP**.
- **Keine lokale Bridge**, **kein REST-Fallback**, **keine lokale Tool-Allowlist**.
- **Keine Phase-5-Persona-Features** (keine Prompt-Notes aus Frappe, keine Multi-Agent-Persona in dieser Phase).

## Coolify-ENV-Variablen

| Name | Zweck | Default | Beispielwert | Hinweis |
| --- | --- | --- | --- | --- |
| `FRAPPE_URL` | Frappe-Zielinstanz des Kunden; wird vom Agent-Container an den stdio-Sidecar-Prozess (frappe-mcp-server) als env durchgereicht | leer | `https://begemotix.pro` | Pflicht; identisch zu Cursor-MCP-Config (D-03, D-05) |
| `FRAPPE_API_KEY` | Agent-Credential Key fuer MCP-Auth | leer | `agent_key_xxx` | Nur dedizierter Agent-User, kein Runtime-Switch (Decision D-03, D-04) |
| `FRAPPE_API_SECRET` | Agent-Credential Secret fuer MCP-Auth | leer | `agent_secret_xxx` | Nur dedizierter Agent-User, kein Runtime-Switch (Decision D-03, D-04) |
| `ROLE_DESCRIPTION` | Prompt-Baseline aus Phase 3 | `You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.` | `You are {AGENT_NAME}...` | Uebergangsloesung — wird in Phase 5 durch Frappe-Notes ersetzt (Decision D-A) |
| `AGENT_NAME` | Prompt-Baseline Platzhalter aus Phase 3 | `Assistant` | `ERP Assistant` | Uebergangsloesung — wird in Phase 5 durch Frappe-Notes ersetzt (Decision D-A) |
| `COMPANY_NAME` | Prompt-Baseline Platzhalter aus Phase 3 | `Frappe` | `Acme GmbH` | Uebergangsloesung — wird in Phase 5 durch Frappe-Notes ersetzt (Decision D-A) |
| `NEXT_PUBLIC_GDPR_NOTICE` | Browser-Hinweistext fuer DSGVO im Frontend | leer | leer | im aktuellen Architekturstand ungenutzt — siehe Decision D-B |

## Konfigurierbare Komponenten

- MCP-Zielinstanz ueber `FRAPPE_URL` (Kundeninstanz pro Deployment).
- MCP-Authentifizierung ueber `FRAPPE_API_KEY` und `FRAPPE_API_SECRET` des dedizierten Agent-Users.
- Frappe-seitige Rollen/Allowlist des Agent-Users fuer read-only Zugriff (Decision D-06).
- Prompt-Baseline-Werte (`ROLE_DESCRIPTION`, `AGENT_NAME`, `COMPANY_NAME`) bleiben bis Phase 5 konfigurierbar, sind aber als Uebergang markiert (Decision D-A).
- Sidecar-Startparameter (`command/args/env`) sind konfigurierbar, aber **stdio-sidecar als Produktivpfad ist verbindlich entschieden und nachzuweisen**.

## Nicht-konfigurierbare Komponenten

- Keine direkten Frappe-REST-Calls im Agenten (strikte MCP-Reinheit, Decision D-07).
- Kein Credential-Switch auf Frontend-/Enduser-Token zur Laufzeit (Decision D-04).
- Permission-Fehler (z. B. 403) werden ohne Retry mit fixer, nutzerfreundlicher Meldung beantwortet (Decision D-08, D-09).
- Structured Logging fuer Permission-Pfade mit `correlation_id` und Tool-Kontext ist fest implementiert (Decision D-10).
- Prompt-Notes aus Frappe bleiben in Phase 4 out of scope (D-11 bis D-15 sind Phase 5).
- Keine lokalen Sicherheitsumgehungen (keine Tool-Allowlist als Security-Ersatz, keine lokale Bridge, kein REST-Bypass).

## Do-Not-Implement (Phase 4)

- Kein HTTP-Endpoint Agent->MCP im Produktivpfad.
- Keine lokale MCP-Bridge.
- Kein direkter REST-Fallback.
- Keine lokale Tool-Allowlist.
- Keine Prompt-Notes-Integration in Phase 4 (keine Phase-5-Persona-Features).
- Keine Multi-Agent-Persona-Logik.
- Kein Voice-Safety-Flow fuer Write-Tools in dieser Phase.

## Handover-Checkliste fuer den Onboarding-Termin

- [x] Gate G1: Session-Grenze schriftlich entschieden und in Verification/UAT referenziert.
- [x] Gate G2: Endpoint/Transport (`stdio-sidecar`) schriftlich entschieden und gegen Zielsystem geprueft.
- [x] Gate G3: Reale Tool-Inventarliste dokumentiert und als Abnahme-Artefakt in UAT verlinkt.
- [ ] Betreiber stellt dedizierten Frappe-Agent-User bereit (eigene API Credentials, minimale Rollen).
- [ ] `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` in Coolify gesetzt und auf korrekten Scope validiert.
- [ ] MCP-Discovery gegen Zielinstanz pruefen (Tools werden dynamisch geliefert, keine lokale Allowlist).
- [ ] Permission-Test durchfuehren: absichtlich verbotenen Tool-Call ausloesen und nutzerfreundliche Antwort ohne Retry verifizieren.
- [ ] Logcheck: 403-Produktfall enthaelt feste Felder `event`, `correlation_id`, `tool`, `error_class`.
- [ ] Session-Stabilitaet nach 403-Negativtest nachgewiesen (kein Session-Crash).
- [ ] Offene Scope-Grenze kommunizieren: Prompting aus Frappe-Notes ist out-of-scope in Phase 4 und fuer Phase 5 eingeplant (Decision D-A).
- [ ] Folgende Artefakte an Operator uebergeben: `.planning/phases/04-frappe-integration/04-HUMAN-UAT.md`, `.planning/phases/04-frappe-integration/04-VERIFICATION.md`, `.planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md`, `.planning/STATE.md`.
