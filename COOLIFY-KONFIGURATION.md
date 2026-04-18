# Coolify: Umgebungsvariablen und Deployment-Hinweise

Diese Referenz richtet sich an **Kunden und Betreiber**, die das Projekt als **eine Docker-Compose-Anwendung** in [Coolify](https://coolify.io/) betreiben. **Sensible Werte** kommen aus der Coolify-Umgebungsmaske (nicht ins Git).

---

## Überblick

| Thema | Kurzfassung |
|--------|-------------|
| **Eine Coolify-App** | Ressource **Docker Compose** auf dieses Repo; mehrere Container = mehrere **Services** in **einer** Anwendung. |
| **Ports** | Fest in **`docker-compose.yml`** (übliche LiveKit-Ports). Nicht über Coolify-Variablen parametrisiert — bei Bedarf Datei lokal anpassen oder zweiten Server nutzen. |
| **Reverse Proxy** | Caddy optional; mit Coolify/Traefik oft Caddy weglassen (siehe `infrastructure/README.md`). |

**Stack in der Compose-Datei:** **LiveKit** + optional **Caddy**. Frontend und Python-Agent sind ggf. weitere Dienste — Env in den folgenden Abschnitten.

---

## A) LiveKit-Server (Service `livekit`)

Diese Variablen werden von `livekit.yaml` und dem LiveKit-Prozess erwartet (über `env_file: .env` bzw. die Coolify-Env für den Service).

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `DOMAIN` | **Ja** | Öffentlicher Hostname für **TURN** (`turn.domain` in `livekit.yaml`). Muss zur erreichbaren LiveKit-/WebRTC-Domain passen. | `live.example.com` |
| `LIVEKIT_API_KEY` | **Ja** | API-Key-Name (Schlüssel in `livekit.yaml` unter `keys:`). | `devkey` (nur Demo; produktiv: zufälliger, langer Wert) |
| `LIVEKIT_API_SECRET` | **Ja** | Geheimer Schlüssel zum Signieren von Tokens; **muss** zum Key oben passen. | *(nur in Coolify/Secret speichern)* |

```env
DOMAIN=live.example.com
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=ersetzen-durch-starkes-geheimnis
```

**Hinweis:** `LIVEKIT_URL` (z. B. `wss://live.example.com`) wird vom **Server** selbst nicht aus dieser Datei gelesen, aber von **Clients, Agent und Frontend** benötigt — siehe unten.

---

## B) Caddy (Service `caddy`, optional)

Nur relevant, wenn Sie Caddy **mit** deployen (typisch: ohne Coolify-Traefik vor dem Stack).

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `DOMAIN` | **Ja** | Hostname für TLS und vHost (muss mit `Caddyfile` übereinstimmen). | `live.example.com` |
| `LETSENCRYPT_EMAIL` | **Ja** | E-Mail für Let’s Encrypt (ACME). | `admin@example.com` |

```env
DOMAIN=live.example.com
LETSENCRYPT_EMAIL=admin@example.com
```

---

## C) Python-Agent (`apps/agent`)

Setzen Sie diese Variablen auf dem **Agent-Container** (oder in Coolify für den zukünftigen Agent-Service), sobald der Worker läuft.

### Verbindung & KI

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `LIVEKIT_URL` | **Ja** | WebSocket-URL des LiveKit-Servers (üblicherweise `wss://` in Produktion). | `wss://live.example.com` |
| `LIVEKIT_API_KEY` | **Ja** | Gleicher Key wie auf dem LiveKit-Server. | `devkey` |
| `LIVEKIT_API_SECRET` | **Ja** | Gleiches Secret wie auf dem LiveKit-Server. | *(Secret)* |
| `OPENAI_API_KEY` | **Ja** | API-Schlüssel für **OpenAI Realtime** (LiveKit-Plugin). | `sk-...` |

### White-Label & Ansagen

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `AGENT_NAME` | Nein | Name in Begrüßung und Platzhalter `{AGENT_NAME}`. | `Assistant` |
| `COMPANY_NAME` | Nein | Firmenname; Platzhalter `{COMPANY_NAME}`. | `Meine Firma` |
| `ROLE_DESCRIPTION` | Nein | Basis-Prompt; darf `{AGENT_NAME}` und `{COMPANY_NAME}` enthalten. | `You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.` |
| `INITIAL_GREETING` | Nein | Erste **unterbrechbare** Begrüßung nach der Pflichtansage. | `Hallo, ich bin {AGENT_NAME}. Wie kann ich helfen?` |
| `MANDATORY_ANNOUNCEMENT` | Nein | **Pflicht-Hinweis** (wird zuerst, nicht unterbrechbar gesprochen); rechtlich mit Datenschutz abstimmen. | *(eigener Text)* |
| `VAD_THRESHOLD` | Nein | Voice-Activity-Schwelle (Float). | `0.5` |
| `VAD_SILENCE_DURATION_MS` | Nein | Stille in ms bis Turn-Ende. | `500` |
| `AGENT_VOICE` | Nein | In `.env.example` / Doku vorgesehen; **aktuell** wird die Stimme im Code noch nicht aus dieser Variable an das Realtime-Modell durchgereicht. Reserviert für spätere Releases. | `alloy` |

Vollständige Vorlage siehe `apps/agent/.env.example` und `apps/agent/WHITE_LABELING.md`.

```env
LIVEKIT_URL=wss://live.example.com
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=...
OPENAI_API_KEY=sk-...

AGENT_NAME=Assistant
COMPANY_NAME=Meine Firma
ROLE_DESCRIPTION=You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.
INITIAL_GREETING=Hallo, ich bin {AGENT_NAME}. Wie kann ich helfen?
MANDATORY_ANNOUNCEMENT=Hinweis: Sie sprechen mit einem KI-Assistenten. ...
VAD_THRESHOLD=0.5
VAD_SILENCE_DURATION_MS=500
```

---

## D) Next.js-Frontend (`apps/frontend`)

Wenn das Widget als eigener Service (oder Build) läuft, unterscheiden Sie:

- **Server-seitig** (API-Routen, Token): normale Env-Variablen.
- **Browser** (`NEXT_PUBLIC_*`): müssen beim **Build** gesetzt sein, damit sie im Client-Bundle landen.

### Server (Runtime)

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `LIVEKIT_URL` | **Ja** | Server-URL für Token/Connection-Details-API (`wss://...`). | `wss://live.example.com` |
| `LIVEKIT_API_KEY` | **Ja** | Zum Ausstellen von Join-Tokens (nur Server, nie im Browser exponieren). | `devkey` |
| `LIVEKIT_API_SECRET` | **Ja** | Geheim zum Signieren. | *(Secret)* |
| `LIVEKIT_DEFAULT_ROOM` | Nein | Standard-Raumname für Token-Route. | `lobby` |
| `SANDBOX_ID` | Nein | Optional (Sandbox-/Template-Kontext). | — |
| `NEXT_PUBLIC_APP_CONFIG_ENDPOINT` | Nein | Optional: URL für externe App-Konfiguration. | — |

### Client (Build-Zeit: `NEXT_PUBLIC_*`)

| Variable | Erforderlich | Beschreibung | Beispiel |
|----------|--------------|--------------|----------|
| `NEXT_PUBLIC_LIVEKIT_URL` | Empfohlen | WebSocket-URL für das **LiveKit-Client-SDK** im Browser. | `wss://live.example.com` |
| `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` | Nein | Wo der Browser Join-Infos holt; Default intern `/api/connection-details`. | `https://widget.example.com/api/connection-details` |
| `NEXT_PUBLIC_WIDGET_PRIMARY_COLOR` | Nein | Primärfarbe (Light). | `#002cf2` |
| `NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR` | Nein | Hover Primär (Light). | `#0020b9` |
| `NEXT_PUBLIC_WIDGET_PRIMARY_COLOR_DARK` | Nein | Primärfarbe (Dark). | `#1fd5f9` |
| `NEXT_PUBLIC_WIDGET_PRIMARY_HOVER_COLOR_DARK` | Nein | Hover Primär (Dark). | `#19a7c7` |

Texte, Logos und Button-Beschriftungen können zusätzlich über `app-config.ts` bzw. optional `NEXT_PUBLIC_APP_CONFIG_ENDPOINT` gesteuert werden — siehe `apps/frontend/lib/env.ts`.

Siehe auch die Root-Vorlage `.env.example` (Frontend/LiveKit-Client).

```env
# Server
LIVEKIT_URL=wss://live.example.com
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=...

# Client (in Coolify beim Build setzen)
NEXT_PUBLIC_LIVEKIT_URL=wss://live.example.com
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://widget.example.com/api/connection-details
```

---

## Minimales vs. vollständiges Szenario

**Nur LiveKit-Stack (wie aktuelle Compose-Datei):** `DOMAIN`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (+ bei Caddy `LETSENCRYPT_EMAIL`).

**Voice mit Agent:** zusätzlich Agent-Block mit `LIVEKIT_URL`, `OPENAI_API_KEY` und den gewünschten Ansage-/White-Label-Variablen.

**Endnutzer-Widget:** zusätzlich Frontend-Block; `NEXT_PUBLIC_*` für Production-Build setzen.

---

## Sicherheit

- **`LIVEKIT_API_SECRET`** und **`OPENAI_API_KEY`** nur als **Secrets** in Coolify hinterlegen, nie ins Git.
- **`NEXT_PUBLIC_*`** sind im Browser sichtbar — dort **keine** Geheimnisse.
- Produktions-Keys nicht mit Demo-Werten wie `devkey` verwenden.

---

## Weitere Dokumentation

- `infrastructure/README.md` — Docker Compose lokal und Coolify-Hinweise (Traefik statt Caddy).
- `apps/agent/.env.example` — Agent-Variablenliste.
- `apps/agent/WHITE_LABELING.md` — Details zu Ansagen und Branding.
- `.env.example` — Frontend- und LiveKit-Client-Beispiele.
