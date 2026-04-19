# Operator Handover - Phase 03 (agent-core)

## 1) Coolify-ENV-Variablen

| Name | Zweck | Default | Beispielwert |
| --- | --- | --- | --- |
| `LIVEKIT_URL` | LiveKit Server URL fuer Agent-Verbindung | leer | `wss://livekit.example.com` |
| `LIVEKIT_API_KEY` | API Key fuer Agent-Worker | leer | `APIKEY123` |
| `LIVEKIT_API_SECRET` | API Secret fuer Agent-Worker | leer | `supersecret` |
| `OPENAI_API_KEY` | OpenAI Zugriff fuer Realtime Modell | leer | `sk-...` |
| `AGENT_NAME` | Anzeigename des Agenten | `Assistant` | `Clara` |
| `COMPANY_NAME` | Firmen-/Markenname in Persona | `Frappe` | `Begemotix` |
| `ROLE_DESCRIPTION` | Persona-Grundprompt mit Platzhaltern | `You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.` | `You are {AGENT_NAME}...` |
| `INITIAL_GREETING` | Startbegruessung nach Join | `Hello, I am {AGENT_NAME}. How can I help you today?` | `Hallo, ich bin {AGENT_NAME} ...` |
| `MANDATORY_ANNOUNCEMENT` | Rechtliche Pflichtansage (DSGVO/Compliance) | vordefinierter Hinweistext | `Hinweis: Sie sprechen mit einem KI-Assistenten ...` |
| `AGENT_VOICE` | Voice-Profil im Modell | `alloy` | `alloy` |
| `VAD_THRESHOLD` | VAD Empfindlichkeit | `0.5` | `0.45` |
| `VAD_SILENCE_DURATION_MS` | Turn-Ende Schwellwert in ms | `500` | `650` |

## 2) Konfigurierbare Komponenten

- LLM Provider/Modellzugriff via `OPENAI_API_KEY` und Realtime-Plugin.
- Agent Persona/Branding via `AGENT_NAME`, `COMPANY_NAME`, `ROLE_DESCRIPTION`, `INITIAL_GREETING`.
- Compliance-Texte via `MANDATORY_ANNOUNCEMENT`.
- Sprach-/Turn-Parameter via `AGENT_VOICE`, `VAD_THRESHOLD`, `VAD_SILENCE_DURATION_MS`.
- LiveKit Zielsystem via `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.

## 3) Nicht-konfigurierbare Komponenten

- Runtime-Framework `livekit-agents` bleibt fest, da Architektur auf Worker/Session-Lifecycle dieses SDKs basiert.
- Logformat JSON via `python-json-logger` ist fix zur Korrelation und Betriebsanalyse.
- Korrelation-ID aus Room-Name ist fest implementiert fuer konsistentes Tracing.

## 4) Handover-Checkliste fuer Onboarding-Termin

- Kundenfragen klaeren:
  - Finaler Rechtstext fuer `MANDATORY_ANNOUNCEMENT`?
  - Gewuenschte Agent-Persona/Tonalitaet?
  - Erwartete Turn-Reaktionszeit und Unterbrechungsverhalten?
- Auszuhaendigende Dateien:
  - `apps/agent/.env.example`
  - `apps/agent/WHITE_LABELING.md`
  - `.planning/phases/03-agent-core/03-03-SUMMARY.md`
  - `.planning/phases/03-agent-core/03-CP-SUMMARY.md`
- Operativer Abschluss:
  - `pytest apps/agent/tests/test_agent.py` auf Zielumgebung grün pruefen.
  - ENV-Werte in Coolify gesetzt und redeploy bestaetigt.
