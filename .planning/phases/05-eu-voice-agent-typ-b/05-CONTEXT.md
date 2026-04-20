# Phase 5: EU-Voice-Agent (Typ B) - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 liefert einen zweiten Agent-Mode (Typ B) mit Mistral LLM + Voxtral STT/TTS im selben Docker-Image wie Typ A.
Der aktive Mode wird deployment-weit per ENV gewählt. Multi-Agent-Routing, Session-Switch und dynamisches Prompt-Management
werden in dieser Phase nur strukturell vorbereitet, aber nicht umgesetzt.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projekt- und Scope-Quellen
- `.planning/ROADMAP.md` — bindender Phase-5-Scope (Typ-B Mode, gleicher Container, ENV-Switch, EU-Default)
- `.planning/PROJECT.md` — Produkt- und Entscheidungsrahmen (MCP-Neutralität, Deployment-Haltung)
- `.planning/STATE.md` — aktueller Projektstatus und aktive Phase

### Bestehende Implementierungspunkte
- `apps/agent/agent.py` — aktueller Typ-A/OpenAI-Realtime Einstieg, Session-Bootstrap, MCP-Toolset-Verkabelung
- `apps/agent/src/frappe_mcp.py` — bestehender MCP-Server-Fabrikpfad, der in beiden Modi konsistent bleiben muss

### Externe Architektur-/SDK-Referenzen (für Planung/Implementierung)
- `https://docs.livekit.io/agents/server/agent-dispatch.md` — agent_name + explicit dispatch Muster
- `https://docs.livekit.io/agents/logic/sessions.md` — AgentSession-Orchestrierung und Modellkonfiguration
- `https://docs.livekit.io/agents/models/llm/mistralai.md` — Mistral LLM Plugin
- `https://docs.livekit.io/agents/models/stt/mistralai.md` — Voxtral STT über Mistral Plugin
- `https://docs.livekit.io/agents/models/tts/mistralai.md` — Voxtral TTS über Mistral Plugin

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/agent/agent.py`: bestehender `AgentSession`-Bootstrap inkl. Room-Connect, Greeting-Flow und Logging kann für Typ B weitergenutzt werden.
- `apps/agent/src/frappe_mcp.py`: MCP-Factory ist bereits gekapselt und kann mode-unabhängig wiederverwendet werden.
- `apps/agent/tests/test_agent.py`: Teststruktur mit Mocks für Session-/Model-Initialisierung ist vorhanden und erweiterbar für Mode-Switch-Tests.

### Established Patterns
- Session wird zentral im Entrypoint erzeugt und per ENV parametriert.
- Fehlerpfade werden über mapper-/helper-Funktionen in nutzerfreundliche Antworten überführt.
- MCP-Tooling wird als `MCPToolset` an `AgentSession` gebunden.

### Integration Points
- Mode-Auswahl greift am Punkt der Modellinitialisierung in `agent.py`.
- Prompt-/Rollen-Text wird bereits über Datei+ENV geladen und kann später per Prompt-Provider abstrahiert werden.
- Test- und Verifikationspfad ist auf pytest-basierten Agent-Tests aufsetzbar.

</code_context>

<specifics>
## Specific Ideas

- Multi-Agent-Readiness ohne Feature-Ausbau: in Phase 5 nur strukturelle Hooks (`voice-eu` Namensraum,
  mode-basierte Factory, Prompt-Provider-Schnittstelle), keine Aktivierung von Session-Switch.
- Runtime-Konfiguration als Produktprinzip: Kunden steuern Sprachen/Voices selbst über ENV.
- Hard-Fail-Haltung ist Produkt-Policy, kein optionaler Toggle in Phase 5.

</specifics>

<deferred>
## Deferred Ideas

- Session-vs-Instance-Switch als aktive Laufzeitfunktion (spätere Phase, vorbereitende Hooks jetzt).
- MCP-neutrales dynamisches Prompt-Management (Phase 6).
- Self-hosted Piper-TTS als alternative Pipeline (Phase 7/Backlog).
- LLM-Routing-Resilienz über externe Router (z.B. OpenRouter) als separates Zukunftsthema.

</deferred>

---

*Phase: 05-eu-voice-agent-typ-b*
*Context gathered: 2026-04-20*
