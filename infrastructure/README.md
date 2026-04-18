# LiveKit for Frappe

Sicherer, selbst-gehosteter Voice-Assistent für Frappe/ERPNext.

## LiveKit Deployment

Dieses Projekt nutzt Docker Compose für ein einfaches, produktionsbereites Deployment von LiveKit und Caddy (als Reverse Proxy).

### Voraussetzungen

- Installiertes Docker und Docker Compose.
- Eine Domain, die auf diesen Server zeigt.
- Ausgefüllte `.env` Datei (basierend auf `.env.example`).

### Starten der Infrastruktur

Um den LiveKit Server und den Caddy Proxy zu starten, führen Sie folgenden Befehl im Hauptverzeichnis aus:

```bash
docker compose up -d
```

### Mehrere LiveKit-Stacks auf demselben Host

Sollen **mehrere** Deployments parallel laufen (z. B. mehrere Kunden-Apps auf einem Server), dürfen sich die **Host-Ports** nicht überschneiden. Die `docker-compose.yml` erlaubt dafür überschreibbare Variablen (siehe `COOLIFY-KONFIGURATION.md` im Repository-Root).

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
