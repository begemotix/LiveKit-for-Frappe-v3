# Phase 4: Frappe Integration - Context

**Gathered:** 2026-04-19 (updated)
**Status:** Ready for planning

<domain>
## Phase Boundary

Der Voice-Agent verbindet sich per MCP mit der Frappe-Instanz, authentifiziert sich mit festen Agent-Credentials und nutzt dynamisch entdeckte Tools fuer read-only Datenzugriff. Fehler bei fehlenden Rechten oder Auth werden nutzerfreundlich behandelt, ohne den Agenten abstuerzen zu lassen.

</domain>

<decisions>
## Implementation Decisions

### MCP Session Lifecycle
- **D-01:** Fachliche Session-Grenze ist room-basiert (eine Session pro LiveKit-Raum).
- **D-02:** MCP-Verbindung wird pro Room-Session aufgebaut, innerhalb dieser Session wiederverwendet und beim Session-Ende sauber beendet.

### Credential Strategy
- **D-03:** Der Agent authentifiziert sich ausschliesslich mit festen Agent-Credentials aus ENV (`FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET`).
- **D-04:** Es gibt keinen Runtime-Switch auf Frontend- oder User-Credentials.

### MCP Runtime Path and Discovery
- **D-05:** Produktivpfad fuer Phase 4 ist ein stdio-Sidecar im Agent-Container: `MCPServerStdio(command="npx", args=["-y", "frappe-mcp-server"], env={FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET})`.
- **D-06:** Es gibt keinen HTTP-Endpoint zwischen Agent und MCP im Produktivpfad; der MCP-Serverprozess spricht intern per stdio mit dem Agenten und extern per REST mit der Kunden-Frappe-Instanz.
- **D-07:** Die Discovery-Liste wird beim Abnahmezeitpunkt vollstaendig erfasst und als Ist-Stand eingefroren, inklusive Write-Tools (z. B. `create_document`, `update_document`, `delete_document`, `call_method`, `reconcile_bank_transaction_with_vouchers`).
- **D-08:** Read-only-Erzwingung liegt bei den Frappe-Rollen des API-Users (kein lokaler Sicherheitsfilter).
- **D-09:** Strikte MCP-Reinheit bleibt bestehen: keine direkten Frappe-API-Aufrufe und keine hardcodierten Doctype-Annahmen.

### Permission and Error Handling
- **D-10:** Feste Nutzerbotschaft bei 403/Permission (Voice/Text identisch): `Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff.`
- **D-11:** Kein Retry auf 403.
- **D-12:** Fehlerpfade werden strukturiert geloggt mit festen Feldern (`event`, `correlation_id`, `tool`, `error_class`) ohne Session-Crash.

### Gate and UAT Sequence
- **D-13:** Verbindliche Reihenfolge: `G1 -> G2 -> G3 -> Wave A (endpoint-/ENV-gebundener Auth-Vertrag, belastbar dokumentiert) -> Wave B (Session-Grenze und Cleanup-Verhalten, belastbar dokumentiert) -> Live-MCP Discovery -> End-to-End Read-only Datenabfrage -> 403-Rechtefall als Produktverhalten -> Final Handover/Verification`.

### Claude's Discretion
- Konkrete technische Hook-Struktur fuer den room-basierten Session-Lifecycle.
- Exakte Form der Tool-Inventar-Dokumentation (solange vollstaendig und eingefroren).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and Requirement Baseline
- `.planning/ROADMAP.md` - Phase-4-Ziel, Scope und Success Criteria fuer Frappe-Integration.
- `.planning/REQUIREMENTS.md` - INTG-01 bis INTG-05 als verbindliche Anforderungen.
- `.planning/PROJECT.md` - Strikte MCP-Reinheit, Self-hosted/White-Label Leitplanken und Architekturentscheidungen D-A bis D-E.

### Prior Phase Decisions
- `.planning/phases/03-agent-core/03-CONTEXT.md` - Agent-Lifecycle, Logging/Korrelation und Deferred-Hinweis zur echten Frappe-MCP-Anbindung.
- `.planning/phases/01-infrastructure-setup/01-CONTEXT.md` - Betriebs-/Netzwerkkontext fuer Deployment-Pfad.
- `.planning/phases/02-frontend-widget/02-CONTEXT.md` - Frontend-Token-/Integrationskontext als Upstream-Rahmen.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/agent/agent.py` (`entrypoint`, `AgentSession`, `function_call_start` Hook) - natuerlicher Integrationspunkt fuer Session-Lifecycle, Tool-Call-Pipeline und Fehlerbehandlung.
- `apps/agent/src/frappe_mcp.py` - bestehender ENV-Credential-Vertrag als Referenz fuer Sidecar-ENV-Paritaet.

### Established Patterns
- Session-getriebener Agent-Start via `participant_joined` in `apps/agent/agent.py` - passt zur Entscheidung "MCP pro Session".
- Strukturiertes JSON-Logging und Korrelationsfelder in `apps/agent/agent.py` - Grundlage fuer INTG-05 Fehlerbehandlung.

### Integration Points
- `apps/agent/agent.py` - zentraler Ort fuer Session-Lifecycle und Tool-Error-Mapping.
- `apps/agent/tests/test_mcp_integration.py` - zentrale Testbasis fuer Credential-Vertrag, Discovery und 403-Verhalten.

</code_context>

<specifics>
## Specific Ideas

- Scope Phase 4 bleibt MCP-Core-Hardening mit stdio-Sidecar.
- G3 schraenkt das Toolset nicht ein, sondern friert den Discovery-Ist-Stand zur Abnahme ein.
- Voice-Safety fuer Write-Tools bleibt explizit ausserhalb von Phase 4.

</specifics>

<deferred>
## Deferred Ideas

- Voice-Safety-Bestaetigung fuer potenziell schreibende Tool-Calls wird separat diskutiert (eigener Punkt/Topic 6).
- Multi-Agent-pro-Deployment ist Backlog fuer Phase 5+ (aktuell 1 Persona pro Deployment).
- Prompt-Notes-/Persona-Themen bleiben Phase 5 (nicht Teil von Phase 4 Hardening).

</deferred>

---

*Phase: 04-frappe-integration*
*Context gathered: 2026-04-19*
