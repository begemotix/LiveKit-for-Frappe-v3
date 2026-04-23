# Frappe-MCP-Wissensbasis

> Dieses Dokument hält den aktuellen Stand unserer Recherche zu
> `frappe-mcp-server` (dem Bindeglied zwischen Voice-Agent und
> Frappe/ERPNext) und dem zugrunde liegenden Model Context Protocol
> (MCP) fest. Ziel: Architektur-Entscheidungen belegbar treffen
> koennen, ohne jedes Mal neu recherchieren zu muessen.
>
> Stand: April 2026. Versionsbezug: `frappe-mcp-server` v0.6.0
> (npm-Paket), MCP-Spec Version 2025-06-18.

---

## 1. Was ist `frappe-mcp-server` ueberhaupt

Ein Node/TypeScript-Server, der das **Model Context Protocol** implementiert
und als "Uebersetzer" zwischen einem MCP-Client und der Frappe-REST-API
dient.

- **npm-Paket:** `frappe-mcp-server`
- **GitHub-Quellcode:** [`appliedrelevance/frappe_mcp_server`](https://github.com/appliedrelevance/frappe_mcp_server)
- **Lizenz:** ISC / MIT
- **Transporte:** stdio (Standard-MCP), HTTP, Streamable-HTTP
- **Aufruf in unserem Stack:** `npx -y frappe-mcp-server` (stdio-Subprozess
  pro Voice-Session)
- **ENV-Variablen:** `FRAPPE_URL`, `FRAPPE_API_KEY`, `FRAPPE_API_SECRET` —
  **keine** weiteren Stellschrauben

---

## 2. Welche Tools bietet `frappe-mcp-server` an (v0.6.0)

**Die Tool-Liste ist statisch im Code hinterlegt — identisch fuer jeden
API-Key, egal welcher Frappe-User dahinter steckt.**

### Dokument-Operationen (Lesen + Schreiben)
Quelle: `src/document-operations.ts`
- `create_document` — Dokument anlegen
- `get_document` — Dokument lesen
- `update_document` — Dokument aendern
- `delete_document` — Dokument loeschen
- `list_documents` — Dokumente auflisten
- `reconcile_bank_transaction_with_vouchers` — Bankabgleich (schreibend)

### Schema-Operationen (Lesen)
Quelle: `src/schema-operations.ts`
- `get_doctype_schema`
- `get_field_options`
- `get_frappe_usage_info`

### Helper-Tools (Lesen)
Quelle: `src/helper-tools.ts`
- `find_doctypes`, `get_module_list`, `get_doctypes_in_module`,
  `check_doctype_exists`, `check_document_exists`, `get_document_count`,
  `get_naming_info`, `get_required_fields`, `get_api_instructions`

### Report-Operationen (Lesen; `export_report` schreibt eine Datei)
Quelle: `src/report-operations.ts`
- `run_query_report`, `get_report_meta`, `list_reports`, `export_report`,
  `get_financial_statements`, `get_report_columns`, `run_doctype_report`

### Generisch
Quelle: `src/index.ts`
- `version`, `ping`
- `call_method` — fuehrt **beliebige whitelisted Frappe-Methoden** aus,
  kann also submit/cancel/andere Aktionen ausloesen, wenn Frappe sie
  erlaubt.

**Nicht enthalten** (wichtig): kein dediziertes `submit_document`,
`cancel_document`, `upload_file`. Submit/Cancel laufen ueber `call_method`
auf `frappe.client.submit` o.ae.

---

## 3. Wie entdeckt ein MCP-Client die Tool-Liste

- Der Client ruft die Standard-MCP-Methode **`tools/list`** auf (JSON-RPC).
- Der Server antwortet mit `{ tools: [{ name, description, inputSchema, ... }], nextCursor? }`.
- **Timing:** Die Liste kann jederzeit nach dem Init erneut abgefragt
  werden; der Server kann Aenderungen via `notifications/tools/list_changed`
  signalisieren (wenn er die Capability `tools.listChanged: true`
  deklariert).
- **`frappe-mcp-server` registriert Tools statisch** beim Startup ueber
  `McpServer.tool(...)` und liefert damit bei jedem `tools/list` dieselbe
  Liste. Keine User-abhaengige Filterung.

Quellen:
- [MCP Spec 2025-06-18 – Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- `frappe-mcp-server/src/index.ts` Zeilen 55–215

---

## 4. Wie werden Rechte durchgesetzt

**Ausschliesslich serverseitig in Frappe, nicht im MCP-Server.**

### Flow

1. MCP-Client ruft `tools/call` mit `name=<tool>`, `arguments={...}` auf.
2. `frappe-mcp-server` uebersetzt das in einen HTTP-Request an die
   **Frappe-REST-API** und haengt `FRAPPE_API_KEY` / `FRAPPE_API_SECRET`
   als Header an.
3. Frappe identifiziert anhand des Keys den **User**.
4. **Frappe selbst** prueft Rollen / Permissions dieses Users.
5. Wenn erlaubt: Frappe fuehrt die Aktion aus, Antwort geht zurueck.
6. Wenn nicht erlaubt: Frappe antwortet mit HTTP 401/403 und einer
   `exception`-Payload.

### Was `frappe-mcp-server` mit Ablehnungen macht

Bei 401/403 wirft der Server in `src/errors.ts` (Zeilen 34–41) einen
`FrappeApiError` mit der **fixen Message**:

> `"Authentication failed during <operation>. Check API key/secret."`

**Achtung:** Die Unterscheidung zwischen "API-Key falsch" und "Rolle
fehlt" geht dabei verloren — beide HTTP-Codes werden identisch behandelt.
Die Frappe-Originaldaten landen in `details.responseData` (inkl.
`exception`, `_server_messages`), stehen also dem Client zur Verfuegung —
aber nur, wenn der Client sie explizit auswertet.

### Konsequenz fuer unseren Code

Unser `apps/agent/src/mcp_errors.py` pruft den Fehlertext auf:
`"403"`, `"permission denied"`, `"not permitted"`, `"insufficient permissions"`.

Die vom `frappe-mcp-server` normalisierte Meldung **"Authentication
failed..."** enthaelt keinen dieser Marker. Das heisst: ein echtes
Permission-Denied wird von unserer `is_permission_error`-Heuristik
**nicht erkannt** und kommt u.U. nicht als freundliche Botschaft beim
User an. Das ist ein bekanntes Gap, das bei der naechsten Refactoring-
Welle mitgefixt werden sollte.

---

## 5. Gibt es einen Read-Only-Modus

**Nein.** Kein Feature-Flag, kein Env-Schalter.

Die einzige Moeglichkeit, Schreibaktionen zu unterbinden, ist die
**Rollenkonfiguration des Frappe-Users**, der zum verwendeten
`FRAPPE_API_KEY` gehoert. Wenn dieser User nur Lese-Rollen hat, lehnt
Frappe jeden Schreib-Call mit 403 ab — der MCP-Server selbst bietet
keine Begrenzung.

Nachgewiesen ueber Quellcode-Grep in v0.6.0:
- Keine Treffer fuer `READ_ONLY | readOnly | read_only | FEATURE | DISABLE`.
- `field.read_only` existiert, ist aber ein DocField-Attribut, kein
  Server-Modus.

---

## 6. Implikationen fuer unsere Architektur

### Was die urspruengliche Phase-04-Entscheidung besagt

Aus `.planning/STATE.md`:

> Phase 04: "Scope-Guardrails bleiben unveraendert: [...] **keine lokale
> Tool-Allowlist**."
>
> Phase 04: "Permission-Fehler werden zentral erkannt und ohne Retry
> auf eine feste nutzerfreundliche Antwort gemappt."

### Was aktuell im Code steht (Widerspruch)

`apps/agent/src/frappe_mcp.py::get_allowed_tools_for_mode("type_b")`
liefert eine fest einprogrammierte 10-Tool-Liste (reine Lese-Tools),
als `TEMPORARY_GUARD` bezeichnet. Das widerspricht der Phase-04-Regel
"keine lokale Tool-Allowlist".

### Was das in der Praxis heisst

- Der Mistral-Agent sieht im MCP-Server **alle ~25 Tools** (wenn wir
  die Allowlist entfernen), darunter `create_document`, `update_document`,
  `delete_document`, `call_method`.
- Der Agent "probiert" im Zweifelsfall auch Schreib-Operationen. Ob sie
  durchgehen, entscheidet **ausschliesslich** der Frappe-User via seine
  Rollen.
- Wenn der Frappe-User z.B. `System Manager` hat, kann der Voice-Agent
  potenziell alles, einschliesslich Loeschungen. Das ist zu **vermeiden**.
- Wenn der Frappe-User nur Lese-Rollen hat, blockt Frappe jede
  Schreibaktion mit 403. Das ist der saubere Weg.

### Offene Entscheidung (CEO)

Bevor wir die Allowlist entfernen:

1. **Welche Rollen hat der Frappe-User** hinter dem aktuellen
   `FRAPPE_API_KEY`?
2. Soll der Voice-Agent schreiben duerfen? Wenn ja, welche Aktionen
   genau?
3. Bleibt es bei einem dedizierten "voice-agent"-User mit engem
   Rollen-Satz? Das ist die empfohlene Praxis — ein eigener User mit
   genau den Rollen, die der Agent haben soll. Dann ist die
   Allowlist-Loeschung risikolos.

---

## 7. Was MCP allgemein zu Permissions sagt

- **MCP selbst hat kein Tool-level Permissions-Modell.** Die Spec
  definiert Authorization nur fuer den HTTP-Transport (OAuth 2.1
  Resource Server). Fuer stdio ist Auth "out of band" — Credentials
  werden ueber die Environment injiziert, die Trust-Boundary ist der
  Host-Prozess.
- **Permission-Denied ist spec-seitig ein Tool-Execution-Fehler**, nicht
  ein Protokoll-Fehler. Er soll als `{ isError: true, content: [...] }`
  im regulaeren Result zurueck kommen, **nicht** als JSON-RPC `error`.
  Grund: das LLM soll den Fehler "sehen" und ggf. umdisponieren.
- **Server duerfen** die Tool-Liste je nach Kontext unterschiedlich
  ausliefern (z.B. pro User filtern), **muessen aber nicht**.
  `frappe-mcp-server` macht es **nicht** — die Liste ist pro Installation
  statisch.

Quellen:
- [MCP Spec – Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [MCP Spec – Authorization](https://modelcontextprotocol.io/specification/draft/basic/authorization)

---

## 8. Bekannte Luecken

1. **Auth-Fehler-Normalisierung im MCP-Server verliert Aufloesung.**
   "Rolle fehlt" und "API-Key falsch" sehen fuer uns identisch aus.
2. **Unsere Permission-Marker in `mcp_errors.py` passen nicht zur
   normalisierten Meldung** des MCP-Servers. Dokumentiert in Kapitel 4.
3. **Die 10-Tool-Allowlist in `frappe_mcp.py` widerspricht** der
   Phase-04-Architekturentscheidung. Dokumentiert in Kapitel 6.
4. **Kein dediziertes Submit/Cancel-Tool** im MCP-Server. Diese
   Aktionen laufen ueber `call_method` — das ist fuer das LLM weniger
   offensichtlich und macht Prompting komplizierter, wenn wir spaeter
   echte Workflow-Schritte brauchen.

---

## 9. Quellen

### Zum npm-Paket / Code
- npm: https://www.npmjs.com/package/frappe-mcp-server
- GitHub-Repo: https://github.com/appliedrelevance/frappe_mcp_server
- README: https://github.com/appliedrelevance/frappe_mcp_server/blob/main/README.md
- Inspizierte Quelldateien (Tarball v0.6.0):
  - `src/index.ts`
  - `src/document-operations.ts`
  - `src/schema-operations.ts`
  - `src/helper-tools.ts`
  - `src/report-operations.ts`
  - `src/errors.ts`

### Zum Protokoll
- MCP Spec 2025-06-18 (aktuell), Kapitel Tools:
  https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- MCP Spec 2024-11-05 (vorherige), Kapitel Tools:
  https://modelcontextprotocol.io/specification/2024-11-05/server/tools
- MCP Spec – Authorization:
  https://modelcontextprotocol.io/specification/draft/basic/authorization
- Authorization Tutorial:
  https://modelcontextprotocol.io/docs/tutorials/security/authorization
- Referenz-SDK auf GitHub:
  https://github.com/modelcontextprotocol/modelcontextprotocol
- Diskussion/Discussions zum Protokoll:
  https://github.com/orgs/modelcontextprotocol/discussions/76

### Interne Verweise
- Phase-04-Entscheidungen: `.planning/STATE.md`
- Unsere MCP-Fehler-Behandlung: `apps/agent/src/mcp_errors.py`
- Unsere Allowlist (TEMPORARY_GUARD): `apps/agent/src/frappe_mcp.py`
- Kundendokumentation EU-Agent: `readme/MISTRAL-AGENT.md`
- Operator-Handover Frappe-Setup:
  `.planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md`
