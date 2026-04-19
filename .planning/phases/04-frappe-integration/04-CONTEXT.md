# Phase 4: Frappe Integration - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Der Voice-Agent verbindet sich per MCP mit der Frappe-Instanz, authentifiziert sich mit festen Agent-Credentials und nutzt dynamisch entdeckte Tools fuer read-only Datenzugriff. Fehler bei fehlenden Rechten oder Auth werden nutzerfreundlich behandelt, ohne den Agenten abstuerzen zu lassen.

</domain>

<decisions>
## Implementation Decisions

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
- `apps/agent/agent.py` (`entrypoint`, `AgentSession`, `function_call_start` Hook) - natuerlicher Integrationspunkt fuer MCP-Session-Init, Tool-Call-Pipeline und Fehlerbehandlung.
- `apps/agent/agent.py` (`load_agent_instructions`) - vorhandener Prompt-Ladepfad, der in Phase 4 auf Frappe-Notes als Primaerquelle umgestellt werden muss.

### Established Patterns
- Session-getriebener Agent-Start via `participant_joined` in `apps/agent/agent.py` - passt zur Entscheidung "MCP pro Session".
- Strukturiertes JSON-Logging und Korrelationsfelder in `apps/agent/agent.py` - Grundlage fuer INTG-05 Fehlerbehandlung.

### Integration Points
- `apps/agent/agent.py` - zentraler Ort fuer MCP-Client-Lifecycle, Discovery und Prompt-Zusammenbau.
- `apps/agent/tests/test_agent.py` - bestehende Testbasis; muss fuer MCP/Auth/403/Prompt-Fallback-Pfade erweitert werden.

</code_context>

<specifics>
## Specific Ideas

- Prompt-Fachquelle ist explizit "Frappe Notes via MCP", nicht Dateisystem-Markdown.
- Public + Assigned Notes bilden gemeinsam die Persona.
- Operator-Hinweis fuer Notes-Groesse (z. B. max. 2-3 Notes pro Agent) wird im Handover dokumentiert.
- Im Plan muessen der konkrete MCP-Tool-Pfad fuer "assigned to user" Notes und der exakte ENV-Notfallinhalt geklaert werden.

</specifics>

<deferred>
## Deferred Ideas

- Voice-Safety-Bestaetigung fuer potenziell schreibende Tool-Calls wird separat diskutiert (eigener Punkt/Topic 6).
- Multi-Agent-pro-Deployment ist Backlog fuer Phase 5+ (aktuell 1 Persona pro Deployment).

</deferred>

---

*Phase: 04-frappe-integration*
*Context gathered: 2026-04-19*
