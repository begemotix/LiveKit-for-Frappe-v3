# Coolify: Umgebungsvariablen und Deployment-Hinweise

Diese Referenz richtet sich an **Kunden und Betreiber**, die das Projekt als **einen Docker-Compose-Stack** in [Coolify](https://coolify.io/) betreiben.

---

## Architektur: Universal Bridge Stack

Wir nutzen jetzt einen **Universal Docker-Compose-Stack**, der vollständig im **Bridge-Modus** läuft. Dies ist die sauberste Lösung für Multi-Tenant-Umgebungen und automatisches SSL-Routing.

1. **LiveKit Server**: Das WebRTC-Backend.
2. **Agent**: Der Python-basierte Voice-Worker (verbindet sich intern via Docker-DNS `ws://livekit:7880`).
3. **Frontend**: Das Next.js-Widget.

### Warum Bridge-Modus statt Host-Modus?
Früher war der Host-Modus nötig, um den Overhead von 10.000 Docker-Proxy-Prozessen für WebRTC zu vermeiden. Wir haben den Port-Bereich nun auf **100 Ports (50000-50100)** optimiert. Dadurch kann der Stack im Bridge-Modus laufen, was folgende Vorteile bietet:
- **Automatisches SSL**: Coolify/Traefik erkennt alle Dienste automatisch und stellt Let's Encrypt Zertifikate ohne manuelle Labels aus.
- **Isolierung**: Dienste kommunizieren intern über das Docker-Netzwerk (`livekit-net`), ohne Host-Ports zu belegen (außer den explizit gemappten).
- **Port-Flexibilität**: Mehrere Instanzen können einfach nebeneinander laufen.

---

## Multi-Tenancy (Mehrere Instanzen pro VPS)

Wenn Sie mehrere Instanzen auf demselben Server betreiben möchten, müssen Sie nur die Host-Ports in der `docker-compose.yml` anpassen:
- Signaling: `7880:7880` -> `7882:7880`
- WebRTC TCP: `7881:7881` -> `7883:7881`
- UDP-Range: `50000-50100:50000-50100/udp` -> `50101-50200:50000-50100/udp`
- Frontend: `3000:3000` -> `3001:3000`

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
3. **Traefik (Coolify)**: Coolify erkennt das Frontend automatisch und routet Traffic von Ihrer Domain auf Port **3000** im Container. Das Ausstellen von Let's Encrypt Zertifikaten funktioniert "out of the box".
4. **LiveKit Ports**: Stellen Sie sicher, dass die Ports 7880-7881 (TCP) und 3478, 5349, 50000-50100 (UDP) in der Firewall offen sind.

---

## Sicherheit & Best Practices

- **API Secrets**: Speichern Sie `LIVEKIT_API_SECRET` und `OPENAI_API_KEY` immer als **Secrets** (Hidden) in Coolify.
- **UDP Range**: In der Standardkonfiguration ist der Bereich auf 100 Ports begrenzt (50000-50100), was für die meisten Setups ausreicht und die Infrastruktur schont. Dies kann im `command`-Teil der `docker-compose.yml` angepasst werden.
