# Phase 5: EU-Voice-Agent (Typ B) - Research

**Researched:** 2026-04-21  
**Domain:** LiveKit Agents Multi-Mode Voice Pipeline (OpenAI Realtime vs Mistral/Voxtral)  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Mode Identity & Dispatch
- **D-01:** `agent_name` ist modusbasiert, nicht funktionsbasiert. Für Phase 5 gilt der Namensraum `voice-eu`.
- **D-02:** Agent-Funktion (z.B. Support/Info/Termin) wird ausschließlich über kundenseitig konfigurierten Prompt gesteuert, nicht über `agent_name`.

### Failure Strategy
- **D-03:** Bei Ausfall von Mistral/Voxtral gilt Hard-Fail: Agent meldet sich sauber ab und beendet die Session.
- **D-04:** Kein stiller Provider-Wechsel auf Typ A im Fehlerfall. DSGVO-Position bleibt technisch strikt.
- **D-05:** LLM-Routing-Resilienz (z.B. OpenRouter) ist explizit außerhalb von Phase 5 und wird nur als spätere Option dokumentiert.

### Runtime Configuration Contract
- **D-06:** Pflicht-ENV-Sets werden pro Mode dokumentiert:
  - Typ A: benötigt `OPENAI_API_KEY`
  - Typ B: benötigt Mistral/Voxtral-Variablen inkl. `MISTRAL_API_KEY`, `VOXTRAL_STT_MODEL`, `VOXTRAL_TTS_MODEL`
- **D-07:** Voice/Language sind kundenseitige Runtime-Konfiguration. Das Produkt setzt keine begemotix-spezifischen Default-Voices.
- **D-08:** Für Voice-Cloning gilt Priorität: `AGENT_VOICE_REF_AUDIO` überschreibt `AGENT_VOICE_ID`, wenn beide gesetzt sind.

### Phase-5 Verification Scope
- **D-09:** Ein Voxtral-Hörtest als Produkt-Gate entfällt. Stattdessen gilt technischer Smoke-Test im Implementierungsflow.
- **D-10:** Smoke-Test deckt mindestens zwei Sprachen ab (DE + EN), um die Sprach-ENV-Konfiguration nachzuweisen.

### Claude's Discretion
- Benennung der verbleibenden ENV-Felder (z.B. `AGENT_MODE`, `MISTRAL_LLM_MODEL`, optionale Fallback-/Timeout-Flags),
  solange D-01 bis D-10 unverändert umgesetzt werden.
- Interne Modulstruktur (Factory-Namen, Datei-Schnitt) zur Vorbereitung von Phase 6/7.

### Deferred Ideas (OUT OF SCOPE)
- Session-vs-Instance-Switch als aktive Laufzeitfunktion (spätere Phase, vorbereitende Hooks jetzt).
- MCP-neutrales dynamisches Prompt-Management (Phase 6).
- Self-hosted Piper-TTS als alternative Pipeline (Phase 7/Backlog).
- LLM-Routing-Resilienz über externe Router (z.B. OpenRouter) als separates Zukunftsthema.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGNT-05 | Typ B Agent (Mistral + EU-TTS) für DSGVO-Konformität implementieren | Mode-Factory-Pattern, Mistral/Voxtral Plugin-Stack, ENV-Vertrag pro Modus, Hard-Fail-Handling, MCPToolset-Entkopplung von Modell-Pipeline |
</phase_requirements>

## Project Constraints (from .cursor/rules/)

- `operator-handover-pflicht.mdc`: D-Entscheidungen aus `PROJECT.md`/`STATE.md` sind bindend und dürfen nicht unterlaufen.
- `anti-drift-reality-check.mdc`: Vor Commits sind definierte Reality-Checks im Terminal Pflicht; bei verbotenen Git-Dateitreffern Commit abbrechen.

## Summary

Phase 5 sollte als **Provider-separierte, aber Session-kompatible Pipeline-Erweiterung** geplant werden: derselbe Worker, dasselbe Docker-Image, dieselbe MCP-Integration, aber zwei klar getrennte Modell-Stacks (Typ A OpenAI Realtime vs Typ B Mistral LLM + Voxtral STT/TTS). Der Umschaltpunkt gehört in eine zentrale Mode-Factory (ENV-gesteuert), nicht in verstreute `if`-Blöcke.

Der bestehende Code in `apps/agent/agent.py` ist bereits session-zentriert und MCP-separiert (`build_frappe_mcp_server()` + `MCPToolset`). Das ist ein guter Anker: MCP bleibt mode-agnostisch, nur Modellinstanzen (llm/stt/tts/turn handling) wechseln je nach Mode. Damit wird AGNT-05 umgesetzt, ohne INTG-01..05-Reife aus Phase 4 zu regressieren.

Für Typ B sind aktuelle Doku-/Ökosystemsignale konsistent: LiveKit führt Mistral als Plugin-Provider für LLM/STT/TTS, Mistral dokumentiert Voxtral-Modelle für Transcription und TTS inkl. Sprache/Voice-Parameter. Einige Detailparameter (z. B. konkrete Voice-IDs je Modellgeneration) sind schnelllebig; diese sollten in Planung als verifizierbare Konfigurationspunkte statt Hardcoding behandelt werden.

**Primary recommendation:** Plane eine `AGENT_MODE`-gesteuerte Pipeline-Factory mit strikt getrennten ENV-Sets pro Mode, gemeinsamem MCPToolset und Hard-Fail-Policy für Typ B.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `livekit-agents` | 1.5.5 | AgentSession, Worker, Tooling, Voice-Orchestrierung | Kern-SDK des bestehenden Projekts; unterstützt Plugin-basierte Providerwahl |
| `livekit-plugins-mistralai` | 1.5.5 | Mistral LLM + Voxtral STT/TTS im LiveKit-Ökosystem | Offizieller Integrationspfad statt eigener HTTP-Adapter |
| `mistralai` | 2.4.0 | Direkte API-/Modellnähe (Fallback, Troubleshooting, ggf. Utilities) | Offizielles SDK; nützlich für Debug/Smoke-Utilities außerhalb LiveKit |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `livekit-agents[mcp,...]` Extras | `~=1.5` | MCP-Toolset + Provider-Plugins aus einer Vertragsversion | Für konsistente Dependency-Auflösung im Agent-Image |
| `pytest`, `pytest-asyncio` | project-managed | Moduswechsel-/Konfigurations-/Fehlerpfadtests | Für Wave- und Gate-Absicherung vor Deploy |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LiveKit Mistral-Plugin | Eigene Mistral HTTP-Adapter im Agent | Mehr Kontrolle, aber höheres Drift-/Wartungsrisiko |
| Single-Path Agent Code | Zwei separate Container/Entrypoints | Klare Trennung, aber widerspricht Success Criteria (ein Image) |

**Installation:**
```bash
uv add "livekit-agents[mcp,openai,mistralai,silero,turn-detector]~=1.5"
```

**Version verification:**  
- `livekit-agents`: 1.5.5 (PyPI upload: 2026-04-20T19:09:51Z)  
- `livekit-plugins-mistralai`: 1.5.5 (PyPI upload: 2026-04-20T19:10:58Z)  
- `mistralai`: 2.4.0 (PyPI upload: 2026-04-16T12:03:34Z)

## Architecture Patterns

### Recommended Project Structure
```
apps/agent/
├── src/
│   ├── mode_config.py        # ENV parsing + validation pro Mode
│   ├── model_factory.py      # build_pipeline(mode) -> llm/stt/tts/turn config
│   ├── session_factory.py    # AgentSession creation (mode-agnostisch)
│   └── frappe_mcp.py         # bestehend, unverändert als MCP-Vertrag
├── agent.py                  # entrypoint + dispatch + lifecycle
└── tests/
    ├── test_mode_switch.py
    └── test_mode_env_validation.py
```

### Pattern 1: Mode-to-Pipeline Factory
**What:** Eine zentrale Factory erstellt je `AGENT_MODE` den passenden Modell-Stack.  
**When to use:** Immer bei mehreren Voice-Providern im selben Worker/Image.  
**Example:**
```python
# Source: https://docs.livekit.io/agents/models/stt/mistralai.md
from livekit.plugins import mistralai

session = AgentSession(
    stt=mistralai.STT(model="voxtral-mini-latest"),
    tts=mistralai.TTS(model="voxtral-mini-tts-2603"),
    # llm=..., tools=[...]
)
```

### Pattern 2: MCP as Stable Contract, Provider as Swappable Concern
**What:** `MCPToolset` bleibt identisch, unabhängig vom aktiven Voice/LLM-Provider.  
**When to use:** Wenn Tool-Verhalten zwischen Modis identisch bleiben muss (Success Criterion #2).  
**Example:**
```python
# Source: https://docs.livekit.io/reference/python/livekit/agents/llm/mcp.html
from livekit.agents.llm.mcp import MCPToolset

toolset = MCPToolset(id="frappe_mcp", mcp_server=frappe_server)
session = AgentSession(tools=[toolset], llm=model)
```

### Anti-Patterns to Avoid
- **Provider-Logik in Entry-Flow verstreuen:** erschwert Tests und erhöht Regressionen bei Typ-A.
- **Silent fallback Typ B -> Typ A:** verletzt D-03/D-04 und Datenschutzposition.
- **Mode-spezifische MCP-Filter ohne Anforderung:** gefährdet Konsistenz des Toolsets zwischen Modi.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mistral/Voxtral Integration | Eigene REST-Wrapper pro Endpoint | `livekit-plugins-mistralai` | Offizieller Adapter enthält bereits Session-/Pipeline-Integration |
| MCP Tool Discovery | Eigenes Tool-Registry-System | `MCPToolset` | Dynamische Tool-Introspection und Session-Integration sind vorhanden |
| Multi-Mode Routing | Mehrere Entrypoint-Skripte/Container | Eine ENV-gesteuerte Factory | Erfüllt Single-Image-Kriterium und reduziert Drift |

**Key insight:** In dieser Phase ist Orchestrierungsdisziplin wichtiger als neue Feature-Tiefe: Standard-Plugins + saubere Factory liefern schneller eine robuste AGNT-05-Basis als eigene Provider-Abstraktionen.

## Common Pitfalls

### Pitfall 1: ENV-Verträge nicht strikt trennen
**What goes wrong:** Typ-B läuft mit unvollständiger Konfiguration und fällt erst zur Laufzeit in obskure Fehler.  
**Why it happens:** Gemeinsame ENV-Validierung ohne Mode-spezifische Pflichtfelder.  
**How to avoid:** Frühzeitige `validate_mode_env(mode)` mit präziser Fehlermeldung je fehlendem Key.  
**Warning signs:** Session startet, bricht aber bei erstem Audio/Tool-Aufruf.

### Pitfall 2: Realtime-Erwartung falsch auf Batch-STT gemappt
**What goes wrong:** Hohe Latenz oder unnatürliche Turn-Timing-Effekte im Voice-Flow.  
**Why it happens:** Modellwahl (`voxtral-mini-*`) nicht an Realtime-Usecase angepasst.  
**How to avoid:** Realtime-geeignete STT/TTS-Modellpfade als Default für Typ B dokumentieren und per ENV überschreibbar halten.  
**Warning signs:** Spürbare Verzögerung bis erste Transkription/Audioantwort.

### Pitfall 3: Mode-Switch testet nur Happy Path
**What goes wrong:** Typ-A bleibt stabil, aber Typ-B-Fehlerpfade verletzen D-03/D-04 oder brechen MCP-Lifecycle.  
**Why it happens:** Keine expliziten Tests für fehlende Keys, API-Fehler, Session-Cleanup.  
**How to avoid:** Dedizierte Tests je Mode + Hard-Fail-Szenarien + Cleanup-Assertions.  
**Warning signs:** Uneinheitliches Verhalten bei Provider-Störungen.

## Code Examples

Verified patterns from official sources:

### Mistral STT/TTS in AgentSession
```python
# Source: https://docs.livekit.io/agents/models/stt/mistralai.md
from livekit.plugins import mistralai
from livekit.agents import AgentSession

session = AgentSession(
    stt=mistralai.STT(model="voxtral-mini-latest"),
    tts=mistralai.TTS(model="voxtral-mini-tts-2603"),
)
```

### Explicit agent dispatch with agent_name
```python
# Source: https://docs.livekit.io/agents/server/agent-dispatch.md
from livekit import api

dispatch = await api.LiveKitAPI().agent_dispatch.create_dispatch(
    api.CreateAgentDispatchRequest(
        agent_name="voice-eu",
        room="room-123",
    )
)
```

### Voxtral speech generation semantics (voice_id/ref_audio)
```python
# Source: https://docs.mistral.ai/capabilities/audio/text_to_speech/speech
response = client.audio.speech.complete(
    model="voxtral-mini-tts-2603",
    input="Hallo aus dem EU-Modus",
    voice_id="your-voice-id",
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single provider path (OpenAI Realtime only) | Multi-provider voice stack via LiveKit plugin ecosystem | LiveKit Agents 1.5.x plugin maturity | Ermöglicht DSGVO-orientierten Mode ohne Architekturbruch |
| `mcp_servers`-zentrierte ältere Muster | `MCPToolset` als primärer MCP-Integrationspfad | 2025-2026 API/Doku-Konvergenz | Bessere Tool-Update-/Filterbarkeit und klare Session-Integration |

**Deprecated/outdated:**
- Implizite Annahme „ein Agent = ein Provider“: Für diese Roadmap nicht mehr ausreichend.

## Open Questions

1. **Welche konkrete Voxtral-Realtime-Variante soll als Typ-B-STT-Default gelten?**
   - What we know: Mistral dokumentiert mehrere Voxtral-Modelllinien (`latest`, versionierte Varianten, realtime/batch Kontexte).
   - What's unclear: Finaler Modellname für eure Latenz-/Kosten-/Qualitätsziele.
   - Recommendation: In Plan Wave 0 eine verifizierende Modell-Selection-Matrix (DE/EN Smoke, TTFA, Fehlerquote) aufnehmen.

2. **Wie strikt soll Dispatch pro `agent_name` bereits in Phase 5 erzwungen werden?**
   - What we know: `agent_name`-basiertes explizites Dispatch ist dokumentiert; D-01 setzt `voice-eu` als Namespace.
   - What's unclear: Ob bestehende automatische Dispatch-Flows parallel weiterlaufen müssen.
   - Recommendation: Plan als „kompatibel zuerst“: Mode-Switch über ENV sicherstellen; explizites Dispatch als optionales Gate in eigener Task.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Agent runtime | ✓ | 3.13.7 | — |
| uv | Projektstandard (AGENTS.md) | ✓ | 0.11.7 | `pip` (nur Notfall) |
| Node.js | `npx frappe-mcp-server` Sidecar | ✓ | v22.22.0 | — |
| npm | MCP Sidecar install/run | ✓ | 11.5.1 | — |
| Docker CLI | Single-image Build/Run-Validierung | ✗ | — | Lokale Non-Docker-Verifikation bis Operator-Stage |

**Missing dependencies with no fallback:**
- Keine für reine Implementierungs-/Unit-Test-Phase; Docker wird erst für Container-Gate zwingend.

**Missing dependencies with fallback:**
- Docker CLI lokal fehlt; funktionale Agent-Validierung kann zunächst ohne Container erfolgen.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` + `pytest-asyncio` |
| Config file | `apps/agent/pyproject.toml` (`tool.pytest.ini_options`) |
| Quick run command | `cd apps/agent && uv run pytest tests/test_agent.py -q` |
| Full suite command | `cd apps/agent && uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGNT-05 | ENV toggles provider A/B in same worker image path | unit | `cd apps/agent && uv run pytest tests/test_mode_switch.py -q` | ❌ Wave 0 |
| AGNT-05 | MCP tool wiring unchanged in both modes | integration-lite | `cd apps/agent && uv run pytest tests/test_mode_switch.py::test_mcp_toolset_same_for_both_modes -q` | ❌ Wave 0 |
| AGNT-05 | Typ-B STT/TTS config accepts DE+EN smoke settings | unit | `cd apps/agent && uv run pytest tests/test_mode_env_validation.py -q` | ❌ Wave 0 |
| AGNT-05 | Typ-B provider failure triggers hard-fail (no fallback) | unit | `cd apps/agent && uv run pytest tests/test_mode_failure_policy.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/agent && uv run pytest tests/test_agent.py -q`
- **Per wave merge:** `cd apps/agent && uv run pytest`
- **Phase gate:** Full suite + DE/EN technical smoke for Typ B

### Wave 0 Gaps
- [ ] `apps/agent/tests/test_mode_switch.py` — AGNT-05 Mode-Dispatch/MCP-Contract
- [ ] `apps/agent/tests/test_mode_env_validation.py` — Pflicht-ENVs je Mode
- [ ] `apps/agent/tests/test_mode_failure_policy.py` — D-03/D-04 Hard-Fail Verhalten

## Sources

### Primary (HIGH confidence)
- https://docs.livekit.io/agents/models/stt/mistralai.md - STT plugin usage, package extras, model parameters
- https://docs.livekit.io/agents/models/tts/mistralai.md - TTS plugin usage, default model/voice behavior
- https://docs.livekit.io/agents/server/agent-dispatch.md - `agent_name` dispatch semantics
- https://docs.livekit.io/reference/python/livekit/agents/llm/mcp.html - `MCPToolset` API semantics
- https://docs.mistral.ai/capabilities/audio/speech_to_text - Voxtral STT capability overview
- https://docs.mistral.ai/capabilities/audio/text_to_speech/speech - `voice_id` / `ref_audio` usage
- https://pypi.org/pypi/livekit-agents/json - version + publish metadata
- https://pypi.org/pypi/livekit-plugins-mistralai/json - version + publish metadata
- https://pypi.org/pypi/mistralai/json - version + publish metadata

### Secondary (MEDIUM confidence)
- https://docs.mistral.ai/models/voxtral-tts-26-03 - modellnahe TTS-Metadaten/Releasekontext

### Tertiary (LOW confidence)
- Web-Suchergebnisse mit gerenderten Doc-Snippets (nur als Navigationshilfe genutzt; Kernclaims gegen offizielle Doku gegengeprüft)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Versionen und Integrationspfade gegen PyPI + offizielle Docs geprüft
- Architecture: MEDIUM - Lokaler Code ist klar, aber einige LiveKit-Seiten sind stark dynamisch gerendert
- Pitfalls: MEDIUM - aus aktueller Doku + bestehender Codebasis, teils erfahrungsbasiert

**Research date:** 2026-04-21  
**Valid until:** 2026-04-28 (schnell bewegte SDK-/Modelllandschaft)
