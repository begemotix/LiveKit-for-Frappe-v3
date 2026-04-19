# OPERATOR-HANDOVER — Phase 01 Infrastructure Setup

## Zielbild (formalisiert)

Phase 1 ist produktiv als Coolify-Stack mit Traefik-Routing umgesetzt:

- LiveKit: `network_mode: host`
- Agent + Frontend: Bridge-Netzwerk
- Internes Wiring: `host.docker.internal` via `extra_hosts: host-gateway`
- Reverse Proxy im Default: Coolify-Traefik
- Caddy: optionales Profil `with-caddy` (auskommentierter Alternativpfad)

## 1) Coolify-ENV-Variablen

Alle für Phase 1 relevanten Variablen aus `.env.example` plus produktionsrelevante Proxy-/Netzwerkwerte.

| Variable | Zweck | Default | Beispielwert | Pflicht/Optional |
|---|---|---|---|---|
| `LIVEKIT_API_KEY` | API-Key für Token-Signierung und LiveKit-Auth | `devkey` | `lk_prod_key_01` | Pflicht |
| `LIVEKIT_API_SECRET` | Secret zu `LIVEKIT_API_KEY` (muss als Secret hinterlegt werden) | `secret` | `lk_prod_secret_01` | Pflicht |
| `DOMAIN` | Öffentlicher Hostname für LiveKit/TURN im LiveKit-Config-Body | `live.example.com` | `live.kunde.de` | Pflicht |
| `LIVEKIT_URL` | Interne Agent-Verbindung zu LiveKit; im Produktiv-Compose auf `ws://host.docker.internal:7880` gesetzt | `wss://live.example.com` | `ws://host.docker.internal:7880` | Pflicht |
| `NEXT_PUBLIC_LIVEKIT_URL` | Öffentliche Browser-URL für WebSocket-Signaling via Traefik | `wss://live.example.com` | `wss://live.kunde.de` | Pflicht |
| `LETSENCRYPT_EMAIL` | Kontaktadresse für ACME/Let's Encrypt (Coolify/Traefik-Resolver-Kontext) | Kein Repo-Default | `ops@kunde.de` | Optional (plattformabhängig) |
| `EXTERNAL_IP` | Explizite externe IP für Sonderfälle bei NAT/RTC-Debugging | Kein Repo-Default | `203.0.113.42` | Optional (nur Sonderfälle) |

### Traefik-Labels im Produktivpfad

Diese Labels sind Teil der deployten Service-Routing-Definition und müssen bei Domain-Änderungen konsistent sein:

| Label | Zweck | Default im Stack | Beispielwert | Pflicht/Optional |
|---|---|---|---|---|
| `traefik.enable=true` | Aktiviert Service-Erkennung | `true` | `true` | Pflicht |
| `traefik.http.routers.livekit.rule` | Host-basierte Router-Regel | `Host(\`live.begemotix.cloud\`)` | `Host(\`live.kunde.de\`)` | Pflicht |
| `traefik.http.routers.livekit.entrypoints` | Erzwingt TLS-EntryPoint | `websecure` | `websecure` | Pflicht |
| `traefik.http.routers.livekit.tls` | TLS für Router aktiv | `true` | `true` | Pflicht |
| `traefik.http.routers.livekit.tls.certresolver` | Let's-Encrypt Resolver in Traefik | `letsencrypt` | `letsencrypt` | Pflicht |
| `traefik.http.services.livekit.loadbalancer.server.url` | Traefik-Upstream auf Host-LiveKit | `http://host.docker.internal:7880` | `http://host.docker.internal:7880` | Pflicht |

## 2) Konfigurierbare Komponenten (Phase 1)

Ohne Codeänderung austauschbar:

- **Domain**: über `DOMAIN` plus Coolify-Routing/Traefik-Hostregel.
- **LiveKit-Credentials**: `LIVEKIT_API_KEY` und `LIVEKIT_API_SECRET`.
- **Reverse-Proxy-Wahl**:
  - Default: Coolify-Traefik.
  - Alternative: Caddy durch Compose-Profil `with-caddy` aktivieren.

## 3) Nicht-konfigurierbare Komponenten (Phase 1)

- **Port-Mapping `50000-50100/udp`**: als Teil des validierten WebRTC-Produktivpfads festgelegt; Änderungen erfordern Anpassungen und erneute technische Verifikation.
- **TURN-Konfiguration**: in LiveKit-`config-body` fest verdrahtet (`enabled`, `udp_port`, `tls_port`, `external_tls`); Änderungen gelten als Infrastruktur-Eingriff außerhalb des reinen Operator-Tunings.

## 4) Handover-Checkliste Onboarding

### Vorab-Fragen an den Kunden

- Welche produktive Domain/Subdomain wird für LiveKit verwendet?
- Wer ist verantwortlicher Kontakt für TLS/Let's Encrypt?
- Gibt es Firewall- oder Compliance-Vorgaben, die UDP-Portbereich oder TURN betreffen?

### Benötigte Zugänge für das IT-Team

- Zugriff auf Coolify-Projekt/Umgebung mit Recht zum Bearbeiten von ENV und Routing.
- DNS-Provider-Zugriff zum Setzen/Ändern von Records.
- Server-/Firewall-Zugriff (oder Ticketweg) zum Öffnen der benötigten Ports.

### DNS- und Netzwerkvoraussetzungen

- `A`/`AAAA`-Record für die LiveKit-Domain auf den Zielhost.
- TLS-Routing über Coolify-Traefik aktiv (`websecure`, Zertifikatsresolver).
- Inbound freigeben:
  - TCP: `7880`, `7881`, `5349`
  - UDP: `3478`, `50000-50100`

## Abnahmehinweis Phase 1

Phase 1 gilt als vollständig, wenn Domain, Credentials, Traefik-Routing und Portfreigaben gemäß dieser Datei gesetzt sind und Browser sowie Agent stabil verbinden.
