# Phase 4: Frappe Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves alternatives and final choices.

**Date:** 2026-04-19
**Phase:** 04-frappe-integration
**Areas discussed:** MCP Session Lifecycle, Credential Strategy, Tool Discovery and MCP Purity, Permission and Error Handling, Prompt Source from Frappe Notes

---

## MCP Session Lifecycle

| Option | Description | Selected |
|--------|-------------|----------|
| Pro Agent-Session | Setup beim Session-Start, Reuse in Session, sauberer Close | ✓ |
| Pro Tool-Call | Hohe Isolation, aber deutlich mehr Latenz/Overhead | |
| Global pro Worker | Schnell, aber Risiko von Cross-Session-Effekten | |
| Andere Variante | Frei definierter Ansatz | |

**User's choice:** Pro Agent-Session.
**Notes:** Session-Isolation bei gleichzeitig gutem Laufzeitverhalten.

---

## Credential Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Feste Agent-Credentials nur aus ENV | Keine User-Credentials aus Frontend, kein Runtime-Switch | ✓ |
| ENV + Secret-Manager-Fallback | Optionaler externer Secret-Pfad | |
| Runtime-Selection pro Mandant | Dynamische Umschaltung zur Laufzeit | |
| Andere Variante | Frei definierter Ansatz | |

**User's choice:** Feste Agent-Credentials nur aus ENV.
**Notes:** Strikte Trennung zwischen Agent-Identitaet und Frontend-/User-Kontext.

---

## Tool Discovery and MCP Purity

| Option | Description | Selected |
|--------|-------------|----------|
| Discovery + app-seitige read-only Allowlist | Lokale Filterung durch App | |
| Discovery + nur Prompt-Regeln | Keine technische Filterung | |
| Statische Toolliste | Keine Discovery | |
| Andere Variante | Dynamische Discovery ohne App-Allowlist; read-only durch Frappe-MCP + Rollen | ✓ |

**User's choice:** Dynamische Discovery ohne app-seitige Allowlist.
**Notes:** Read-only ist Eigenschaft des Frappe-MCP-Servers und der Agent-User-Rollen beim Kunden. Strikte MCP-Reinheit gemaess PROJECT.md.

---

## Permission and Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Graceful Meldung + Logging, kein Retry bei 403 | Nutzerfreundlich und stabil | ✓ |
| Graceful Meldung + 1 Retry bei allen Fehlern | Einfacher Retry-Ansatz | |
| Technische Meldung 1:1 an Nutzer | Rohfehler sichtbar | |
| Andere Variante | Frei definierter Ansatz | |

**User's choice:** Graceful User-Meldung + strukturiertes Logging, kein Retry bei 403.
**Notes:** Permission-Fehler sollen transparent, aber nicht technisch und nicht absturzverursachend sein.

---

## Prompt Source from Frappe Notes

| Option | Description | Selected |
|--------|-------------|----------|
| Session-Start aus Frappe + ENV-Fallback | Standardvorschlag | |
| Worker-Start + Global Cache | Statisch bis Neustart | |
| Pro Turn neu laden | Maximal aktuell, hohe Latenz | |
| Andere Variante | Frappe Notes via MCP: Public + Assigned; Lazy Load ohne Cache; ENV-Fallback | ✓ |

**User's choice:** Eigene Variante (Frappe Notes via MCP).
**Notes:**  
- Prompt setzt sich aus Public Notes und den dem Agent-User zugewiesenen Notes zusammen.  
- Pro Deployment exakt eine Agent-User-Identitaet (eine Persona).  
- Multi-Agent-pro-Deployment ist Backlog (Phase 5+).  
- Phase 4 startet ohne Cache; Session-Cache nur bei real nachgewiesenem Bedarf (Gap-Closure).  
- Im Plan zu klaeren: MCP-Tool-Pfad fuer "assigned to user" Notes, exakter Inhalt der ENV-Notfall-Persona.

---

## Claude's Discretion

- Konkrete technische Hook-Struktur fuer Session-Lifecycle.
- Konkrete Formulierungen fuer Permission-Fehlertexte in Voice/Text.
- Konkretes Merge-Format der Prompt-Bausteine.

## Deferred Ideas

- Voice-Safety-Bestaetigung fuer potenziell schreibende Tool-Calls als separater Diskussionspunkt (Topic 6).
- Multi-Agent-pro-Deployment als Backlog fuer spaetere Phase (5+).
