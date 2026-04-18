# LiveKit for Frappe

Sicherer, selbst-gehosteter Voice-Assistent für Frappe/ERPNext.

## LiveKit Deployment

Dieses Projekt nutzt Docker Compose für ein einfaches, produktionsbereites Deployment von LiveKit und Caddy (als Reverse Proxy).

### Voraussetzungen

- Installiertes Docker und Docker Compose.
- Eine Domain, die auf diesen Server zeigt.
- Ausgefüllte `.env` Datei (basierend auf `.env.example`).

### Starten der Infrastruktur

```bash
docker compose up -d
```

Umgebungsvariablen für LiveKit/Caddy: siehe **`COOLIFY-KONFIGURATION.md`** (Root) und `.env.example`.

**Hinweis:** Die `docker-compose.yml` nutzt feste Standard-Ports. Eine zweite LiveKit-Instanz auf dem **gleichen** Host kollidiert damit — dann Ports in der Compose-Datei (und ggf. `livekit.yaml`) anpassen oder einen weiteren Server nutzen.

### Deployment mit Coolify (Alternative)

Wenn Sie das System über [Coolify](https://coolify.io/) deployen, können Sie den Caddy-Container überspringen, da Coolify bereits Traefik als globalen Proxy nutzt.

1. Erstellen Sie eine neue Ressource in Coolify basierend auf dem `docker-compose.yml`.
2. Entfernen Sie den `caddy` Service aus der Konfiguration.
3. Binden Sie den LiveKit Port `7880` in der Coolify UI an Ihre Domain.
4. Fügen Sie ggf. Traefik-Labels hinzu, falls Sie manuelle Konfigurationen benötigen:
   ```yaml
   labels:
     - 'traefik.http.routers.livekit.rule=Host(`livekit.example.com`)'
     - 'traefik.http.services.livekit.loadbalancer.server.port=7880'
   ```

### White-Labeling

Farbwerte und Branding-Informationen für das Frontend-Widget werden über die `.env` Datei gesteuert:

- `NEXT_PUBLIC_BRAND_COLOR`: Primärfarbe des Widgets (z.B. `#ff4500`).
- `NEXT_PUBLIC_APP_NAME`: Name des Assistenten.

## Lizenz

Apache-2.0
