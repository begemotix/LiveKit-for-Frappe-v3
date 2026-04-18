# Domain Pitfalls

**Domain:** Voice-Assistent für Frappe (Self-Hosted Voice Agent)
**Researched:** 2026-04-18

## Critical Pitfalls

Mistakes that cause rewrites, broken deployments, or critical UX failures.

### Pitfall 1: Dead Air During Frappe Tool Calls (LLM Latency)
**What goes wrong:** Der Agent ruft über MCP Daten aus dem ERPNext/Frappe ab (z.B. "Wie ist der Status von Bestellung X?"). Die Frappe-API benötigt 2-4 Sekunden, der Agent bleibt in dieser Zeit komplett stumm. Der Nutzer denkt, die Verbindung sei abgebrochen und spricht erneut in das Mikrofon, was die Tool-Call-Chain zerstört.
**Why it happens:** OpenAI Realtime (Typ A) pausiert die Audioausgabe naturgemäß, während ein Funktionsaufruf (Function Calling) auf sein Ergebnis wartet.
**Consequences:** Katastrophale User Experience; Nutzer brechen Interaktionen ab.
**Prevention:** Implementierung von asynchronen "Filler Words" oder "Audio-Status-Updates" im Agenten *bevor* der MCP-Call an Frappe abgesetzt wird (z.B. "Einen Moment, ich schlage das im System nach...").

### Pitfall 2: Globale API-Schlüssel vs. User-Permissions (Auth Bypass)
**What goes wrong:** Der Agent wird backend-seitig mit einem zentralen "Administrator" Frappe API-Key konfiguriert, und Berechtigungen werden lediglich weich (z.B. im Prompt) eingeschränkt.
**Why it happens:** Es ist architektonisch einfacher, einen Master-Key zwischen MCP und Frappe zu nutzen, als User-Tokens oder OAuth-Sessions dynamisch vom Browser an den Agent-Worker durchzureichen.
**Consequences:** Schwere Sicherheitslücke. Prompt Injection oder Halluzinationen können dazu führen, dass der Agent im Namen des Administrators Frappe-Datensätze löscht, liest oder mutiert. Dies verstößt gegen die Core Value "strikt dem Frappe-User folgen".
**Prevention:** Der Agent MUSS zwingend mit dem Session-Token oder dem spezifischen API-Schlüssel des aktuell im Frontend eingeloggten Frappe-Users initialisiert werden (Impersonation/Passthrough). Das MCP-Backend darf ausschließlich in diesem übergebenen User-Kontext kommunizieren.

### Pitfall 3: WebRTC / TURN in Self-Hosted Docker Setups
**What goes wrong:** Das Voice-Widget funktioniert im lokalen Entwicklungsnetzwerk perfekt, schlägt aber von extern (Mobiles Netz, strikte Firmennetzwerke) fehl (endloses "Connecting...").
**Why it happens:** LiveKit benötigt funktionierende TURN/STUN Server für NAT-Traversal. Bei Docker-Deployments wird oft die interne Docker-IP statt der externen public IP an Clients gesendet (`use_external_ip` Konfigurationsfehler), oder UDP/TCP Fallbacks sind nicht korrekt konfiguriert (Port 443 → 5349 Mapping fehlt am Loadbalancer).
**Consequences:** Das Produkt ist bei Kundennetzwerken unbrauchbar.
**Prevention:** Nutzung des gebündelten LiveKit TURN-Servers anstatt externer coturn-Instanzen. Zwingende korrekte Konfiguration von `node_ip` in der `livekit.yaml` und frühzeitiger Test der WebRTC Fallbacks auf ICE/TCP und TURN/TLS via Port 443.

## Moderate Pitfalls

### Pitfall 4: Frappe Link-Field Permission Errors (Opaque 403s)
**What goes wrong:** Der Agent schlägt beim Lesen eines Dokuments (z.B. "Sales Invoice") fehl, obwohl der User das generelle Recht auf "Sales Invoice" hat.
**Why it happens:** Frappe erfordert Lesezugriff auf alle referenzierten Link-Fields in einem Dokument (z.B. "Territory" oder "Customer Group"). Wenn der User darauf keinen Zugriff hat, wirft Frappe einen `403 Forbidden` Fehler.
**Prevention:** Der MCP-Server muss 403 Fehler sauber abfangen und dem LLM im Klartext mitteilen, dass "Zugriff auf verknüpfte Daten fehlt", anstatt nur Stacktraces zu werfen. So kann der Agent dem Nutzer eine sinnvolle Antwort generieren ("Sie haben nicht die nötigen Rechte für bestimmte verknüpfte Felder in diesem Datensatz").

### Pitfall 5: VAD-Probleme & Truncation Handling (Voice Activity Detection)
**What goes wrong:** Der Agent unterbricht sich selbst durch eigenes Echo, verliert die ersten Worte eines Satzes, oder redet einfach über den Nutzer hinweg, wenn dieser dazwischenredet.
**Prevention:** Sorgfältige Konfiguration der server-side VAD-Parameter (z.B. Reduktion von `min_endpointing_delay` und `false_interruption_timeout` für schnellere Reaktionen). Zudem muss das "Truncation Handling" (Abbruch des aktuellen Audios, wenn der User reinspricht) im LiveKit-Worker sauber implementiert sein, damit die Context-Window Historie des Modells weiß, wo genau der Agent unterbrochen wurde.

## Minor Pitfalls

### Pitfall 6: Widget Disconnect bei Next.js Route-Changes
**What goes wrong:** Der Nutzer redet mit dem Agenten-Widget, klickt auf einen internen Link im Frappe-Frontend / Next.js-Frontend, und das Voice-Widget bricht hart die Verbindung ab.
**Prevention:** Das Audio/LiveKit-Room-Context-Objekt muss zwingend übergeordnet (z.B. im Root-Layout oder via React Context außerhalb der variablen Route-Ebene) gerendert werden, um den State über Client-Side Navigations hinweg beizubehalten.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| LiveKit Docker Setup | WebRTC verbindet sich extern nicht | Test-Script für TURN-Relay via Mobilfunknetzwerk als Abnahmekriterium definieren. |
| Agent Worker (Typ A) | Dead Air bei Frappe-Queries | LLM muss asynchron Filler-Phrasen generieren, bevor der blockierende MCP-Call gestartet wird. |
| Frappe MCP Integration | Auth Bypass / Privilege Escalation | Architektur-Review: Der Token-Flow (Frappe Frontend → LiveKit Token Payload → Agent Worker → MCP) muss vor Implementierung sauber dokumentiert werden. |

## Sources

- [HIGH] Frappe Forum & Docs: Authentication mechanisms, Link Field permission architecture
- [HIGH] LiveKit GitHub Issues: TURN/STUN Docker configs, NAT leakage issues (2025/2026)
- [HIGH] LiveKit Field Guides: Latency optimization, Homepage agent configuration
- [MEDIUM] OpenAI Developer Forums: Realtime API VAD issues, Truncation handling bugs
