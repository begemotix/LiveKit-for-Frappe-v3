# Coolify: Umgebungsvariablen und Deployment-Hinweise

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

- **Agent -> LiveKit**: Der Agent verbindet sich intern über `ws://host.docker.internal:7880`. 
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
| `LIVEKIT_URL` | **Ja** | Interne URL für den Agenten. | `ws://host.docker.internal:7880` |
| `NEXT_PUBLIC_LIVEKIT_URL` | **Ja** | Externe URL für den Browser. | `wss://live.example.com` |

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
