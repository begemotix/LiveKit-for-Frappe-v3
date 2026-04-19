# Coolify: Umgebungsvariablen und Deployment-Hinweise

Diese Referenz richtet sich an **Kunden und Betreiber**, die das Projekt als **eine Docker-Compose-Anwendung** in [Coolify](https://coolify.io/) betreiben. 

---

## Architektur: Host-Networking

Wir nutzen für LiveKit den **`network_mode: host`**. Das bedeutet:
1. **Performance**: WebRTC-Traffic (UDP) wird ohne Docker-Proxy-Overhead direkt vom Host verarbeitet.
2. **Einfachheit**: Es müssen keine 10.000 UDP-Ports in der Compose-Datei gemappt werden, was die Startzeit der Container massiv verkürzt.
3. **Ports**: Der LiveKit-Container nutzt direkt die Ports des Host-Systems (Standard: 7880, 7881, 3478, 5349, sowie der UDP-Bereich).

### Warum keine Port-Mappings in Coolify?
Docker startet für jeden einzeln gemappten UDP-Port einen eigenen Proxy-Prozess. Bei dem für WebRTC üblichen Bereich von 10.000 Ports führt dies oft dazu, dass Container minutenlang im Status "Created" hängen oder gar nicht erst starten. Mit `network_mode: host` entfällt dieser Schritt komplett.

---

## Multi-Tenancy (Mehrere Instanzen pro VPS)

Wenn Sie mehrere LiveKit-Instanzen auf demselben Server betreiben möchten, müssen Sie die Ports **innerhalb der `docker-compose.yml`** (im `--config-body` Bereich) anpassen, da sich diese sonst gegenseitig blockieren würden.

**Vorgehen pro Kunde/Mandant:**
1. Erstellen Sie eine eigene Coolify-Ressource (Docker Compose).
2. Vergeben Sie im `--config-body` eindeutige Ports für Signaling, RTC und TURN.
3. Passen Sie den UDP-Port-Range an (z.B. Instanz 1: 50000-50100, Instanz 2: 50101-50200).

---

## Environment Variablen (Coolify-Maske)

Diese Variablen müssen in der Coolify-Oberfläche für den Dienst gesetzt werden:

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `DOMAIN` | **Ja** | Öffentlicher Hostname (für TURN/SSL). | `live.example.com` |
| `LIVEKIT_API_KEY` | **Ja** | API-Key für den Zugriff. | `devkey` |
| `LIVEKIT_API_SECRET` | **Ja** | Geheimes Passwort (nur als Secret speichern!). | `secret` |

---

## Deployment-Ablauf

1. **Ressource**: Docker Compose (verweist auf dieses Repo).
2. **Source**: Die `docker-compose.yml` im Root nutzt automatisch `network_mode: host`.
3. **Traefik (Coolify)**: Routen Sie HTTPS von Ihrer Domain auf Port **7880** (Signaling) des Hosts.
4. **Agent & Frontend**: Diese benötigen die `LIVEKIT_URL` (z.B. `wss://live.example.com`).

---

## Sicherheit & Best Practices

- **API Secrets**: Speichern Sie `LIVEKIT_API_SECRET` und `OPENAI_API_KEY` immer als **Secrets** (Hidden) in Coolify.
- **UDP Range**: In der Standardkonfiguration ist der Bereich auf 100 Ports begrenzt (50000-50100), was für die meisten Setups ausreicht und die Infrastruktur schont. Dies kann im `command`-Teil der `docker-compose.yml` angepasst werden.
