# LiveKit for Frappe - Infrastruktur

Dieses Verzeichnis enthält die Konfiguration für den LiveKit-Server-Stack.

## Deployment

Der Stack wird via Docker Compose gestartet. Wir nutzen **Host-Networking** für maximale Performance und einfachste Konfiguration.

### Voraussetzungen
- Docker & Docker Compose installiert.
- Domain ist auf die IP des Servers geroutet.
- Ports 7880, 7881, 3478, 5349 (TCP/UDP) sowie 50000-50100 (UDP) sind in der Firewall offen.

### Starten
```bash
docker compose up -d
```

Standardmäßig wird nur der **LiveKit-Server** gestartet.

### Optional: Caddy (TLS-Proxy)
Falls Sie kein Coolify/Traefik nutzen, können Sie Cadddy mitstarten:
```bash
docker compose --profile with-caddy up -d
```

## Konfiguration
- **`livekit.yaml`**: Zentrale Server-Konfiguration (Ports, IP, Keys).
- **`.env`**: Enthält Secrets wie API-Keys und Domain-Namen. Nutzen Sie `.env.example` als Vorlage.

Details zum Deployment via **Coolify** finden Sie in der `COOLIFY-KONFIGURATION.md` im Hauptverzeichnis.
