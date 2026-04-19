---
date: "2026-04-19 19:50"
promoted: false
---

Phase-4 Vorschlag: Local-First MCP fuer LiveKit als neue Wave aufnehmen.

Ausgangslage:
- Cursor kann mit bgx-frappe arbeiten, weil dort ein lokaler stdio-MCP-Adapter laeuft.
- LiveKit scheitert bei direkter URL-Nutzung mit Transport/Auth-Mismatch (HTML statt MCP-Transportantwort).

Ziel:
- Eine robuste Integrationsstrategie fuer den Agenten festlegen und umsetzen.
- Primar pruefen: MCPServerStdio mit lokal gestartetem frappe-mcp-server im Agent-Container.
- Sekundaer (Fallback): lokale Bridge/Gateway, falls stdio aus Laufzeitgruenden nicht praktikabel ist.

Erfolgskriterium:
- Agent laedt echte Frappe-Tools reproduzierbar ohne HTML/SSE-Fehler.
- UAT-Tests Discovery, Read-only E2E und 403-Pfad sind technisch unblockt.
