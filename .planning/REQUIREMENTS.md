# Requirements: LiveKit for Frappe

**Defined:** 2026-04-18
**Core Value:** Sichere, selbst-gehostete Sprach- und Text-Interaktion mit Frappe-Instanzen, bei der alle Berechtigungen strikt dem Frappe-User folgen und keine externen Cloud-Plattformen (außer LLM/TTS-APIs) für das Hosting des Produkts benötigt werden.

## v1 Requirements

### Infrastructure
- [ ] **INFR-01**: Docker Compose Setup für LiveKit Server bereitstellen
- [ ] **INFR-02**: Reverse Proxy (Caddy) für automatische SSL-Zertifikate (Let's Encrypt) integrieren
- [ ] **INFR-03**: Environment-Variablen für White-Labeling und API-Keys definieren
- [ ] **INFR-04**: TURN/STUN-Konfiguration für reibungslose WebRTC-Verbindungen hinter NAT sicherstellen

### Frontend (Widget)
- [ ] **WIDG-01**: Next.js-basiertes Voice/Text-Widget als Floating Button bereitstellen
- [ ] **WIDG-02**: Button ermöglicht Verbindungsaufbau (WebRTC) zum lokalen LiveKit Server
- [ ] **WIDG-03**: Widget generiert einen unauthentifizierten Gast-Token, um dem Raum beizutreten

### Agent Core (Type A)
- [ ] **AGNT-01**: Python Agent Worker mit `livekit-agents` implementieren
- [ ] **AGNT-02**: OpenAI Realtime API für STT/TTS (Speech-to-Speech) mit geringer Latenz integrieren
- [ ] **AGNT-03**: Voice Activity Detection (VAD) für nahtlose Unterbrechungen durch den User konfigurieren
- [ ] **AGNT-04**: Filler-Audio bei langen Ladezeiten/Tool-Calls implementieren (Vermeidung von "Dead Air")

### Integration (Frappe MCP)
- [ ] **INTG-01**: `mcp` Python SDK in den Agent Worker integrieren
- [ ] **INTG-02**: Agent baut Verbindung zum externen Frappe MCP-Server auf und authentifiziert sich mit eigenen, fest hinterlegten Agenten-Credentials (z.B. API-Key aus der .env)
- [ ] **INTG-03**: Agent nutzt die übergebenen Credentials, um im eigenen Namen als authentifizierter "Agenten-User" in Frappe zu agieren
- [ ] **INTG-04**: Agent nutzt Frappe MCP-Tools ausschließlich lesend (Read-only)
- [ ] **INTG-05**: Graceful Error Handling für fehlgeschlagene Frappe-Rechte (403/Opaque Errors) implementieren

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

| Feature | Reason |
|---------|--------|
| LiveKit Cloud Hosting | Produkt ist zwingend self-hosted für maximale Datenhoheit. |
| Eigene Berechtigungslogik | Redundant und fehleranfällig; Agent erbt 100% die Frappe-Rechte. |
| Frappe-interne App | Starke Koppelung an Frappe-Codebase vermeiden; Produkt bleibt eigenständig. |
| Proprietäre Frontend-Frameworks | Erschwert White-Labeling; Nutzung von Standard React/Next.js. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 1 | Pending |
| INFR-02 | Phase 1 | Pending |
| INFR-03 | Phase 1 | Pending |
| INFR-04 | Phase 1 | Pending |
| WIDG-01 | Phase 2 | Pending |
| WIDG-02 | Phase 2 | Pending |
| WIDG-03 | Phase 2 | Pending |
| AGNT-01 | Phase 3 | Pending |
| AGNT-02 | Phase 3 | Pending |
| AGNT-03 | Phase 3 | Pending |
| AGNT-04 | Phase 3 | Pending |
| INTG-01 | Phase 4 | Pending |
| INTG-02 | Phase 4 | Pending |
| INTG-03 | Phase 4 | Pending |
| INTG-04 | Phase 4 | Pending |
| INTG-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-18*
*Last updated: 2026-04-18 after initial definition*