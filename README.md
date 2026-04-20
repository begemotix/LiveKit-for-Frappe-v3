# LiveKit for Frappe

**DSGVO-konformer, selbst-gehosteter Voice-Assistent fuer Frappe/ERPNext.**

Ein White-Label Open-Source Voice-Agent, den Frappe-Betreiber
vollstaendig auf eigener Infrastruktur betreiben - ohne dass
Gesprächsdaten US-Clouds oder Dritt-Anbieter erreichen. Nutzer
interagieren per Browser-Widget, Chatbot-Fenster oder Telefon
mit dem ERP; Berechtigungen richten sich strikt nach dem
Frappe-User, mit dem der Agent authentifiziert ist.

## Warum DSGVO-konform?

Der Agent laeuft auf Ihrer Infrastruktur. LiveKit-Server,
Voice-Agent und Frontend werden gemeinsam bei Ihnen deployed.
Zur Frappe-Instanz des Kunden verbindet sich der Agent per
MCP (Model Context Protocol) mit drei ENV-Variablen -
identisch zum Cursor-Setup. Aktuell nutzt der Voice-Pfad
OpenAI Realtime (Typ A); eine vollstaendig EU-gehostete
Variante mit Mistral und Voxtral (Typ B) ist in Vorbereitung.

## Fuer wen

- Frappe- oder ERPNext-Betreiber, die Voice-AI ohne
  Datenabfluss an US-Cloud-Anbieter einsetzen wollen
- Integratoren und Agenturen mit White-Label-Bedarf
- Unternehmen im deutschen und europaeischen Markt, fuer die
  DSGVO nicht optional ist

## Weiterfuehrende Dokumentation

**Fuer Betreiber und Kunden:**
- [`readme/COOLIFY-KONFIGURATION.md`](readme/COOLIFY-KONFIGURATION.md)
  - Deployment, ENV-Variablen, Hybrid-Networking
- [`readme/SCHULUNG_GUIDE.md`](readme/SCHULUNG_GUIDE.md)
  - So passen Sie Ihren Agenten an (Persoenlichkeit, Wissen,
  Tonalitaet)
- [`readme/AGENT_PROMPT.md`](readme/AGENT_PROMPT.md)
  - Beispiel-Agentenpersoenlichkeit

**Fuer Uebergabe an Operatoren:**
- [`.planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md`](.planning/phases/04-frappe-integration/OPERATOR-HANDOVER.md)
  - Onboarding-Checkliste, Scope-Guards, Frappe-MCP-Setup

**Fuer Entwickler:**
- `.planning/` - Phasenweise Architektur- und
  Entscheidungsdokumentation, Decisions, Verifikation

## Quickstart

1. Repository klonen
2. `.env.example` nach `.env` kopieren und ausfuellen
   (siehe `readme/COOLIFY-KONFIGURATION.md`)
3. `docker compose up -d`
4. Frontend ist unter der konfigurierten Domain erreichbar

## Stack

- **Media:** LiveKit Server, self-hosted, WebRTC
- **Agent:** Python, LiveKit Agents 1.5.x, MCP-Client (stdio)
- **MCP-Sidecar:** `frappe-mcp-server` (npm-Paket,
  stdio-Transport)
- **Frontend:** Next.js, basiert auf agent-starter-embed
- **Deployment:** Docker Compose, Coolify-optimiert

## Lizenz

Apache-2.0.
