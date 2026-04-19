# Phase 4: Frappe Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves alternatives and final choices.

**Date:** 2026-04-19 (updated)
**Phase:** 04-frappe-integration
**Areas discussed:** Session-Grenze (G1), Endpoint/Transport-Pfad (G2), Tool-Inventar als Abnahme-Artefakt (G3), 403-Produktverhalten, Gate-/UAT-Reihenfolge

---

## Session-Grenze (G1)

| Option | Description | Selected |
|--------|-------------|----------|
| Room-basiert | Eine Session pro LiveKit-Raum | ✓ |
| Participant-basiert | Eine Session pro Teilnehmer | |
| Conversation-turn-basiert | Eine Session pro Turn | |
| Andere Variante | Frei definierter Ansatz | |

**User's choice:** Room-basiert (`1`).
**Notes:** D-01/D-02 werden an die Room-Session gekoppelt.

---

## Endpoint/Transport-Pfad (G2)

| Option | Description | Selected |
|--------|-------------|----------|
| `/mcp` | Streamable HTTP Endpoint | |
| `/sse` | SSE Endpoint | |
| Fallback `/mcp` -> `/sse` | dualer Endpoint-Pfad | |
| Andere Variante | stdio-Sidecar im Agent-Container | ✓ |

**User's choice:** Andere Variante (`4`): stdio-Sidecar.
**Notes:**  
- `MCPServerStdio(command="npx", args=["-y", "frappe-mcp-server"], env={FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET})`  
- Kein HTTP-Endpoint zwischen Agent und MCP.  
- MCP-Subprozess spricht per stdio mit LiveKit-Agent und per REST gegen Kunden-Frappe.

---

## Tool-Inventar als Abnahme-Artefakt (G3)

| Option | Description | Selected |
|--------|-------------|----------|
| Exakt 4 Pflichttools | `frappe.get_doc`, `list_docs`, `search_link`, `get_meta` | |
| Reale Discovery-Liste als Wahrheit | ungefilterter Ist-Stand beim Abnahmezeitpunkt | ✓ |
| Mindestmenge + Pflichtset | frei definierbare Mischform | |
| Andere Variante | Frei definierter Ansatz | |

**User's choice:** Reale Discovery-Liste als Wahrheit (`2`).
**Notes:**  
- Discovery-Liste wird bei Abnahme vollstaendig erfasst und eingefroren (inkl. Write-Tools).  
- Das schraenkt funktional nichts ein, es dokumentiert den Ist-Stand.  
- Read-only-Erzwingung liegt bei Frappe-Rollen des API-Users (D-06).  
- Voice-Safety fuer Write-Tools bleibt Deferred (Phase 5 / Topic 6).

---

## 403-Produktverhalten

| Option | Description | Selected |
|--------|-------------|----------|
| Bestehende feste Meldung beibehalten | `Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff.` | ✓ |
| Neue feste Meldung | Benutzerdefinierter Wortlaut | |
| Kurz + Admin-Hinweis | Assistenzvorschlag | |

**User's choice:** Bestehende feste Meldung beibehalten (`1`).
**Notes:** no-retry auf 403 bleibt verbindlich; strukturierte Logfelder bleiben Pflicht.

---

## Gate-/UAT-Reihenfolge

| Option | Description | Selected |
|--------|-------------|----------|
| Strikt sequentiell | G1 -> G2 -> G3 -> Live Discovery -> E2E read-only -> 403 -> Final | ✓ |
| Gates parallel, dann Live-Tests | Reihenfolge innerhalb G1-3 frei | |
| Andere Reihenfolge | Frei definierter Ansatz | |

**User's choice:** Strikt sequentiell (`1`).
**Notes:** Ohne Abschluss frueherer Gates gelten nachfolgende Live-Checks als verfrueht/prozessual ungueltig.

---

## Claude's Discretion

- Auspraegung der Dokumentationsstruktur fuer Gate-Evidenzen.
- Konkrete technische Hook-Details zur room-basierten Sessiongrenze.

## Deferred Ideas

- Voice-Safety-Bestaetigung fuer potenziell schreibende Tool-Calls als separater Diskussionspunkt (Phase 5 / Topic 6).
- Multi-Agent-pro-Deployment als Backlog fuer spaetere Phase (5+).
