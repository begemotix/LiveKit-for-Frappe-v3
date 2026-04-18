# Phase 03: Agent Core - Research

**Researched:** 2026-04-18
**Domain:** Voice AI, OpenAI Realtime API, LiveKit Agents
**Confidence:** HIGH

## Summary

Diese Phase implementiert den zentralen Voice-Agenten (Typ A) basierend auf der **OpenAI Realtime API** und dem **LiveKit Agents SDK**. Der Fokus liegt auf minimaler Latenz (< 500ms), natürlichem Gesprächsverhalten durch serverseitige **Voice Activity Detection (VAD)** und robustem **Interruption Handling**. 

Die Implementierung basiert auf dem offiziellen `agent-starter-python` Template von LiveKit, wird aber um spezifische Anforderungen wie White-Labeling (via ENV), DSGVO-Pflichtansagen und einen "Prompt-Trick" für Filler-Audio erweitert. Ein Mock-Tool mit künstlichem Delay dient zur Vorbereitung der späteren Frappe-Integration.

**Primary recommendation:** Nutze das `livekit-plugins-openai` Plugin in der Version `~=1.4`, um die native Realtime-Anbindung zu nutzen, und konfiguriere die VAD-Parameter (`silence_duration_ms`) aggressiv für eine schnelle Reaktion.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01: Dynamische Konfiguration** — Persona via ENV (`AGENT_NAME`, `COMPANY_NAME`, etc.).
- **D-02: DSGVO-Compliance** — Pflichtansage via ENV (kein Hardcoding).
- **D-03: Filler-Audio Prompt-Trick** — Überbrückungssätze via System-Prompt Regel ("Sage kurz, dass du nachschaust...").
- **D-04: Architektur-Vorbereitung** — Leerer `on_function_call_start` Hook und Mock-Tool (3s Delay).
- **D-05: Sofortiger Stopp** — Audio-Ausgabe stoppt unmittelbar bei User-Unterbrechung.
- **D-06: Konfigurierbare Schwellwerte** — VAD via ENV (`VAD_THRESHOLD`, `VAD_SILENCE_DURATION_MS`).
- **D-07: Participant-Triggered Join** — Agent tritt erst bei `ParticipantJoined` bei.
- **D-08: ENV-Variablen-Katalog** — Erstellung in `.env.example`.
- **D-09: Strukturiertes JSON-Logging** — Nutzung von `python-json-logger`.
- **D-10: Korrelations-ID** — Ableitung aus LiveKit-Room-Name.

### Claude's Discretion
- Genaue Ausgestaltung des "Prompt-Tricks" für Filler-Audio.
- Spezifische VAD-Defaultwerte (Empfehlung: 300-500ms für Realtime).
- Logging-Struktur (JSON).

### Deferred Ideas (OUT OF SCOPE)
- **Frappe-MCP-Anbindung**: Keine Datenanbindung in Phase 3 (Phase 4).
- **Frappe-ENV-Variablen**: `FRAPPE_URL` etc. erst in Phase 4.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGNT-01 | Python Agent Worker mit `livekit-agents` | Nutzung von `AgentSession` und `WorkerOptions` aus dem SDK. |
| AGNT-02 | OpenAI Realtime API für STT/TTS | Integration via `openai.realtime.RealtimeModel`. |
| AGNT-03 | VAD für nahtlose Unterbrechungen | Konfiguration von `silero.VAD` oder OpenAI `Server VAD`. |
| AGNT-04 | Filler-Audio bei Tool-Calls | Umsetzung durch "Prompt-Trick" im System-Prompt. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `livekit-agents` | `~=1.4.0` | Framework für Voice-Agenten | Offizielles SDK, optimiert für WebRTC. |
| `livekit-plugins-openai` | `~=1.4.0` | OpenAI Realtime Plugin | Native Unterstützung für OpenAI's low-latency API. |
| `livekit-plugins-silero` | `~=0.6.0` | VAD (Voice Activity Detection) | Robuste, lokale VAD für Interruption-Detection. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-json-logger` | `~=2.0.0` | Strukturiertes Logging | Erforderlich für D-09 (JSON-Logs). |
| `python-dotenv` | `~=1.0.0` | ENV-Management | Laden der Persona-Konfiguration (D-01). |

**Installation:**
```bash
pip install livekit-agents[openai,silero] python-json-logger python-dotenv
```

## Architecture Patterns

### Recommended Project Structure
```
apps/agent/
├── agent.py               # Haupteinstiegspunkt (Worker & Entrypoint)
├── .env                   # Lokale Konfiguration (Persona, API Keys)
├── .env.example           # Vorlage für Partner (D-08)
├── requirements.txt       # Abhängigkeiten
└── tests/                 # Phase-Validierung
```

### Pattern 1: Persona-Injection (D-01)
Die Persona wird dynamisch in den System-Prompt injiziert, bevor die Session startet.
```python
instructions = os.getenv("ROLE_DESCRIPTION", "You are a helpful assistant.")
# Variablen-Substitution für White-Labeling
instructions = instructions.replace("{AGENT_NAME}", os.getenv("AGENT_NAME", "AI"))
```

### Pattern 2: Filler-Audio Prompt-Trick (D-03)
Anstatt echte Audio-Dateien abzuspielen, wird das LLM angewiesen, eine kurze Bestätigung zu geben.
```python
filler_prompt = "IMPORTANT: Before calling a tool, always say a brief filler sentence like 'One moment, I'll check that for you' or 'Let me look that up' so the user knows you are working."
combined_prompt = f"{instructions}\n\n{filler_prompt}"
```

### Anti-Patterns to Avoid
- **Hardcoded Prompts:** Verhindert White-Labeling (D-01).
- **Eigene Audio-Pipeline:** Das OpenAI Realtime Plugin verwaltet STT/TTS automatisch; manuelle Eingriffe erhöhen die Latenz.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| STT/TTS Sync | Manuelle Buffer-Logik | `RealtimeModel` | Das Plugin synchronisiert Audio und Transkripte nativ über WebRTC. |
| Turn Detection | Eigene Stille-Erkennung | `silero.VAD` | Silero ist hochoptimiert und filtert Hintergrundgeräusche besser als einfache RMS-Checks. |

## Common Pitfalls

### Pitfall 1: Hohe VAD-Latenz
**What goes wrong:** Der Agent antwortet zu langsam oder unterbricht den User zu spät.
**Why it happens:** `min_silence_duration_ms` ist zu hoch eingestellt (Default oft 1000ms).
**How to avoid:** Auf 300ms - 500ms reduzieren für ein "snappy" Gefühl.

### Pitfall 2: Double Greeting
**What goes wrong:** Der Agent grüßt zweimal beim Beitritt.
**Why it happens:** Sowohl `on_enter` Hook als auch `initial_greeting` im Realtime-Modell konfiguriert.
**How to avoid:** Nur einen Mechanismus nutzen (Empfehlung: `AgentSession.say` im `entrypoint`).

## Code Examples

### Agent Session Setup (AGNT-01, AGNT-02, AGNT-03)
```python
# Source: https://docs.livekit.io/agents/models/realtime/plugins/openai/
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, silero

session = AgentSession(
    llm=openai.realtime.RealtimeModel(
        instructions=os.getenv("ROLE_DESCRIPTION"),
        voice=os.getenv("AGENT_VOICE", "alloy")
    ),
    vad=silero.VAD.load(
        min_silence_duration_ms=int(os.getenv("VAD_SILENCE_DURATION_MS", "500"))
    ),
    allow_interruptions=True
)
```

### DSGVO-Pflichtansage (D-02, D-05)
```python
# Ununterbrechbare Ansage beim Start
announcement = os.getenv("MANDATORY_ANNOUNCEMENT", "This call may be recorded for quality assurance.")
await session.say(announcement, allow_interruptions=False)
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | ✓ | 3.11.x | — |
| OpenAI API Key | Realtime API | ✓ | — | — |
| LiveKit Server | WebRTC Signaling | ✓ | (Phase 1) | — |

**Missing dependencies with no fallback:**
- `OPENAI_API_KEY`: Ohne Key kann der Agent nicht starten.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Quick run command | `pytest apps/agent/tests/test_agent.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGNT-01 | Agent tritt Raum bei | Integration | `pytest -k test_join` | ❌ Wave 0 |
| AGNT-03 | Unterbrechung stoppt Audio | Smoke Test | `pytest -k test_interruption` | ❌ Wave 0 |
| AGNT-04 | Mock-Tool wird aufgerufen | Unit | `pytest -k test_mock_tool` | ❌ Wave 0 |

## Sources

### Primary (HIGH confidence)
- [LiveKit Docs: OpenAI Realtime](https://docs.livekit.io/agents/models/realtime/plugins/openai/)
- [LiveKit Docs: Turns & Interruptions](https://docs.livekit.io/agents/logic/turns/)
- [agent-starter-python Template](https://github.com/livekit-examples/agent-starter-python)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Basierend auf aktueller LiveKit Doku.
- Architecture: HIGH - Template-Struktur ist bewährt.
- Pitfalls: MEDIUM - Latenz-Tuning ist oft umgebungsabhängig.

**Research date:** 2026-04-18
**Valid until:** 2026-05-18
