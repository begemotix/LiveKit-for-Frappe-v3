# Coolify: Umgebungsvariablen und Deployment-Hinweise

Diese Referenz richtet sich an **Kunden und Betreiber**, die das Projekt als **einen Docker-Compose-Stack** in [Coolify](https://coolify.io/) betreiben.

---

## Architektur: Unified Stack

Wir nutzen jetzt einen **Unified Docker-Compose-Stack**, der alle Komponenten enthält:
1. **LiveKit Server**: Das WebRTC-Backend (Port 7880, 7881, etc.).
2. **Agent**: Der Python-basierte Voice-Worker (verbindet sich intern mit LiveKit).
3. **Frontend**: Das Next.js-Widget (Port 3000).

Wir nutzen weiterhin für alle Komponenten den **`network_mode: host`**. Das bedeutet:
1. **Performance**: WebRTC-Traffic (UDP) wird ohne Docker-Proxy-Overhead direkt vom Host verarbeitet.
2. **Einfachheit**: Es müssen keine 10.000 UDP-Ports gemappt werden.
3. **Kommunikation**: Alle Dienste können sich gegenseitig über `localhost` erreichen.

### Warum `network_mode: host`?
Docker startet für jeden einzeln gemappten UDP-Port einen eigenen Proxy-Prozess. Bei WebRTC (10.000 Ports) führt dies oft dazu, dass Container minutenlang im Status "Created" hängen oder gar nicht erst starten. Mit `network_mode: host` entfällt dieser Overhead.

---

## Multi-Tenancy (Mehrere Instanzen pro VPS)

Wenn Sie mehrere Instanzen auf demselben Server betreiben möchten, müssen Sie die Ports in der `docker-compose.yml` anpassen:
- LiveKit Signaling: 7880 -> 7882, etc.
- Frontend: 3000 -> 3001, etc.
- UDP-Range: 50000-50100 -> 50101-50200.

---

## Environment Variablen (Coolify-Maske)

Diese Variablen müssen in Coolify gesetzt werden:

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `DOMAIN` | **Ja** | Öffentlicher Hostname. | `live.example.com` |
| `LIVEKIT_API_KEY` | **Ja** | API-Key. | `devkey` |
| `LIVEKIT_API_SECRET` | **Ja** | API-Secret (Hidden). | `secret` |
| `OPENAI_API_KEY` | **Ja** | Für den Agenten (Hidden). | `sk-...` |
| `LIVEKIT_URL` | **Ja** | Interne URL für Agent/Frontend. | `ws://localhost:7880` |
| `NEXT_PUBLIC_LIVEKIT_URL` | **Ja** | Externe URL für den Browser. | `wss://live.example.com` |

---

## Deployment-Ablauf

1. **Ressource**: Docker Compose (verweist auf dieses Repo).
2. **Build**: Coolify baut das Frontend und den Agenten automatisch über die jeweiligen Dockerfiles in `apps/`.
3. **Traefik (Coolify)**: Routen Sie HTTPS von Ihrer Domain auf Port **3000** (Frontend) des Hosts.
4. **LiveKit Ports**: Stellen Sie sicher, dass die Ports 7880-7881 (TCP) und 3478, 5349, 50000-50100 (UDP) in der Firewall offen sind.

---

## Sicherheit & Best Practices

- **API Secrets**: Speichern Sie `LIVEKIT_API_SECRET` und `OPENAI_API_KEY` immer als **Secrets** (Hidden) in Coolify.
- **UDP Range**: In der Standardkonfiguration ist der Bereich auf 100 Ports begrenzt (50000-50100), was für die meisten Setups ausreicht und die Infrastruktur schont. Dies kann im `command`-Teil der `docker-compose.yml` angepasst werden.
