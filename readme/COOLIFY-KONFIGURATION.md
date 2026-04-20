# Coolify: Umgebungsvariablen und Deployment-Hinweise

> **Hinweis zum Referenz-Setup:** Diese Anleitung dokumentiert
> die Konfiguration mit dem Frappe-MCP-Server als Referenzimplementierung.
> Für andere MCP-Server (ERP, CRM, interne Tools) passen Sie
> die MCP-Sidecar-ENV-Variablen analog an - das Grundmuster
> (drei ENV-Werte, stdio-Transport) bleibt identisch.

Diese Referenz richtet sich an **Kunden und Betreiber**, die das Projekt als **einen Docker-Compose-Stack** in [Coolify](https://coolify.io/) betreiben.

---

## Architektur: Hybrid Wired Stack

Wir nutzen ein spezialisiertes **Hybrid-Netzwerk**, um WebRTC-Performance mit einfacher SSL-Verwaltung zu kombinieren:

1. **LiveKit Server**: Läuft im **`network_mode: host`**. Dies ist zwingend erforderlich für stabile WebRTC-Audio/Video-Verbindungen (kein Docker-Proxy Overhead).
2. **Agent & Frontend**: Laufen im Standard **Bridge-Modus**. 
   - Dies ermöglicht dem Frontend die automatische SSL-Zertifikatsverwaltung durch Traefik.
   - Der Agent kann sicher auf externe Dienste (wie den Frappe-MCP) zugreifen, ohne das Host-Netzwerk zu belasten.

### Warum dieser Hybrid-Ansatz?
- **WebRTC-Performance**: LiveKit benötigt direkten Zugriff auf die Hardware-Ports des Hosts, um Latenzen zu minimieren.
- **SSL-Einfachheit**: Das Frontend und das LiveKit-Signaling werden über Traefik mit Let's Encrypt abgesichert.
- **Interne Verdrahtung**: Der Agent erreicht den LiveKit-Server über das Docker-Gateway (`host.docker.internal`), was den Traffic innerhalb des VPS hält und die Latenz minimiert.

---

## Komponenten-Verdrahtung (Wiring)

- **Agent -> LiveKit**: Der Agent verbindet sich intern über `ws://host.docker.internal:7880`. Dies wird automatisch durch die `extra_hosts` Konfiguration in der `docker-compose.yml` auf die IP des Docker-Gateways (meist `172.17.0.1`) aufgelöst.
- **Browser -> LiveKit**: Der Client im Browser verbindet sich verschlüsselt über `wss://live.begemotix.cloud`. Traefik routet dies intern an den Host-Port 7880 weiter.
- **Agent -> Frappe-MCP**: Der Agent greift als Client auf Ihren externen Frappe-Server zu (HTTPS). Dies erfordert keine speziellen Inbound-Ports am VPS, da es sich um eine ausgehende Verbindung handelt.

---

## Multi-Tenancy (Mehrere Instanzen pro VPS)

Wenn Sie mehrere Instanzen auf demselben Server betreiben möchten, müssen Sie nur die Host-Ports in der `docker-compose.yml` anpassen:
- Signaling: Host-Port 7880
- WebRTC TCP: Host-Port 7881
- UDP-Range: Host-Ports 50000-50100
- Frontend: Port 3000 (automatisch durch Coolify)

---

## Environment Variablen (Coolify-Maske)

Diese Variablen müssen in Coolify gesetzt werden:

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `DOMAIN` | **Ja** | Öffentlicher Hostname. | `live.example.com` |
| `LIVEKIT_API_KEY` | **Ja** | API-Key. | `devkey` |
| `LIVEKIT_API_SECRET` | **Ja** | API-Secret (Hidden). | `secret` |
| `OPENAI_API_KEY` | **Ja** | Für den Agenten (Hidden). | `sk-...` |
| `LIVEKIT_URL` | **Ja** | Interne URL für den Agenten (wird in compose überschrieben). | `ws://host.docker.internal:7880` |
| `NEXT_PUBLIC_LIVEKIT_URL` | **Ja** | Öffentliche URL für den Browser (via Traefik). | `wss://live.begemotix.cloud` |
| `AGENT_NAME` | Nein | Anzeigename des Agenten. | `Assistant` |
| `COMPANY_NAME` | Nein | Name des Unternehmens. | `Begemotix` |
| `ROLE_DESCRIPTION` | Nein | System-Prompt für das LLM. | `You are {AGENT_NAME}, a helpful assistant...` |
| `INITIAL_GREETING` | Nein | Erster Satz des Agenten. | `Hallo, ich bin {AGENT_NAME}...` |
| `MANDATORY_ANNOUNCEMENT` | Nein | Nicht unterbrechbarer DSGVO-Hinweis. | `Hinweis: Sie sprechen mit einem KI...` |
| `AGENT_VOICE` | Nein | OpenAI Voice ID. | `alloy` |
| `VAD_THRESHOLD` | Nein | Empfindlichkeit der Spracherkennung (0.0-1.0). | `0.5` |
| `VAD_SILENCE_DURATION_MS` | Nein | Pause in ms, bevor Agent antwortet. | `500` |
| `SERVICE_FQDN_LIVEKIT` | Nein | FQDN für LiveKit. | `live.begemotix.cloud` |
| `SERVICE_URL_LIVEKIT` | Nein | Full URL für LiveKit. | `https://live.begemotix.cloud` |
| `SERVICE_URL_FRONTEND` | Nein | Full URL für Frontend. | `https://voice.begemotix.cloud` |
| `SERVICE_FQDN_FRONTEND` | Nein | FQDN für Frontend. | `voice.begemotix.cloud` |
| `NEXT_PUBLIC_APP_CONFIG_ENDPOINT` | Nein | Optionaler Endpoint für App-Konfiguration. | |
| `NEXT_PUBLIC_GDPR_NOTICE` | Nein | Text für den DSGVO-Hinweis im Web-Widget. | `Ich willige in die Verarbeitung...` |

---

## Deployment-Ablauf

1. **Ressource**: Docker Compose (verweist auf dieses Repo).
2. **Build**: Coolify baut das Frontend und den Agenten automatisch über die jeweiligen Dockerfiles in `apps/`.
3. **Traefik (Coolify)**: Coolify erkennt das Frontend automatisch und routet Traffic von Ihrer Domain auf Port **3000** im Container. Das Ausstellen von Let's Encrypt Zertifikaten funktioniert "out of the box".
4. **LiveKit Ports**: Stellen Sie sicher, dass die Ports 7880-7881 (TCP) und 3478, 5349, 50000-50100 (UDP) in der Firewall offen sind.

---

## Sicherheit & Best Practices

- **API Secrets**: Speichern Sie `LIVEKIT_API_SECRET` und `OPENAI_API_KEY` immer als **Secrets** (Hidden) in Coolify.
- **UDP Range**: In der Standardkonfiguration ist der Bereich auf 100 Ports begrenzt (50000-50100), was für die meisten Setups ausreicht und die Infrastruktur schont. Dies kann im `command`-Teil der `docker-compose.yml` angepasst werden.
