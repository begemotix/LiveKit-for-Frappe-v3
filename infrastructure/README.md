# LiveKit for Frappe

Sicherer, selbst-gehosteter Voice-Assistent für Frappe/ERPNext.

## LiveKit Deployment

Docker Compose startet **LiveKit**. **Caddy** ist optional (Profil `with-caddy`) — mit **Coolify/Traefik** typischerweise **ohne** Caddy.

### Voraussetzungen

- Docker und Docker Compose.
- Domain (optional, je nach Proxy).
- `.env` nach `.env.example`; Host-Ports siehe **`COOLIFY-KONFIGURATION.md`**.

### Starten

Aus **`docker-compose.template.yml`** die aktuelle Compose erzeugen (Pflicht bei abweichenden Host-Ports — z. B. mehrere Instanzen auf einem Server):

```bash
bash scripts/render-compose.sh
docker compose up -d
```

Nur **LiveKit** (Standard): wie oben. **Mit Caddy** (eigener TLS-Proxy, z. B. ohne Traefik):

```bash
bash scripts/render-compose.sh
docker compose --profile with-caddy up -d
```

Details, Mandanten-Ports, Coolify: **`COOLIFY-KONFIGURATION.md`** im Repository-Root.

### Deployment mit Coolify

- Traefik von Coolify nutzen → **kein** Caddy-Profil; vor Deploy **`bash scripts/render-compose.sh`** mit mandantenspezifischen `LIVEKIT_HOST_*`-Variablen.
- LiveKit-Signaling-Port in Traefik auf den **gewählten Host-Port** (nicht zwingend 7880) mappen.

### White-Labeling

Widget-Farben u. a. über `.env` / Frontend-`NEXT_PUBLIC_*` (siehe Root-`.env.example`).

## Lizenz

Apache-2.0
