# Requirements: LiveKit for Frappe

**Defined:** 2026-04-18
**Core Value:** Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.

## v1 Requirements

### Infrastructure

- [x] **INFR-01**: Docker Compose Setup für LiveKit Server bereitstellen
- [x] **INFR-02**: Reverse Proxy (Caddy) für automatische SSL-Zertifikate (Let's Encrypt) integrieren
- [x] **INFR-03**: Environment-Variablen für White-Labeling (Farbwerte im UI), Verbindungs-URLs und API-Keys generisch definieren
- [x] **INFR-04**: TURN/STUN-Konfiguration für reibungslose WebRTC-Verbindungen hinter NAT sicherstellen

### Frontend (Widget)

- [x] **WIDG-01**: Next.js-basiertes Voice/Text-Widget als Floating Button bereitstellen
- [x] **WIDG-02**: Button ermöglicht Verbindungsaufbau (WebRTC) zum lokalen LiveKit Server
- [x] **WIDG-03**: Widget generiert einen unauthentifizierten Gast-Token, um dem Raum beizutreten

### Agent Core (Type A)

- [x] **AGNT-01**: Python Agent Worker mit `livekit-agents` implementieren
- [x] **AGNT-02**: OpenAI Realtime API für STT/TTS (Speech-to-Speech) mit geringer Latenz integrieren
- [x] **AGNT-03**: Voice Activity Detection (VAD) für nahtlose Unterbrechungen durch den User konfigurieren
- [x] **AGNT-04**: Filler-Audio bei langen Ladezeiten/Tool-Calls implementieren (Vermeidung von "Dead Air")

### Integration (Frappe MCP)

- [x] **INTG-01**: `mcp` Python SDK in den Agent Worker integrieren
- [x] **INTG-02**: Agent baut Verbindung zum externen Frappe MCP-Server auf und authentifiziert sich mit eigenen, fest hinterlegten Agenten-Credentials (z.B. API-Key aus der .env)
- [x] **INTG-03**: Agent nutzt die übergebenen Credentials, um im eigenen Namen als authentifizierter "Agenten-User" in Frappe zu agieren
- [x] **INTG-04**: Agent entdeckt Tools dynamisch über den MCP-Server (Introspection) und nutzt diese ausschließlich lesend (Read-only). Keine direkten Frappe-API-Aufrufe oder hardcoded Doctypes.
- [x] **INTG-05**: Graceful Error Handling für fehlgeschlagene Frappe-Rechte (403/Opaque Errors) implementieren

## v2 Requirements

### Advanced Telephony

- **TELE-01**: SIP-Trunk Integration für eingehende Telefonanrufe
- **TELE-02**: Asynchrone Anrufer-Verifizierung via SMS-Link

### Agent Core (Type B & C)

- **AGNT-05**: Typ B Agent (Mistral + EU-TTS) für DSGVO-Konformität implementieren
- **AGNT-06**: Typ C Agent (Mistral Text) für zeitgesteuerte Back-Office-Automatisierungen

### Integration (Write Operations)

- **INTG-06**: Write-Confirmation-Gate vor dem Ausführen von schreibenden Frappe-Aktionen
- **INTG-07**: Correlation-ID-Logging für Frappe-Aktionen zur Nachverfolgbarkeit

## Out of Scope

| Feature                         | Reason                                                                      |
| ------------------------------- | --------------------------------------------------------------------------- |
| LiveKit Cloud Hosting           | Produkt ist zwingend self-hosted für maximale Datenhoheit.                  |
| Eigene Berechtigungslogik       | Redundant und fehleranfällig; Agent erbt 100% die Frappe-Rechte.            |
| Frappe-interne App              | Starke Koppelung an Frappe-Codebase vermeiden; Produkt bleibt eigenständig. |
| Proprietäre Frontend-Frameworks | Erschwert White-Labeling; Nutzung von Standard React/Next.js.               |

## Traceability

| Requirement | Phase   | Status   |
| ----------- | ------- | -------- |
| INFR-01     | Phase 1 | Complete |
| INFR-02     | Phase 1 | Complete |
| INFR-03     | Phase 1 | Complete |
| INFR-04     | Phase 1 | Complete |
| WIDG-01     | Phase 2 | Complete |
| WIDG-02     | Phase 2 | Complete |
| WIDG-03     | Phase 2 | Complete |
| AGNT-01     | Phase 3 | Complete |
| AGNT-02     | Phase 3 | Complete |
| AGNT-03     | Phase 3 | Complete |
| AGNT-04     | Phase 3 | Complete |
| INTG-01     | Phase 4 | Complete |
| INTG-02     | Phase 4 | Complete |
| INTG-03     | Phase 4 | Complete |
| INTG-04     | Phase 4 | Complete |
| INTG-05     | Phase 4 | Complete |

**Coverage:**

- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---

_Requirements defined: 2026-04-18_
_Last updated: 2026-04-18 after initial definition_
