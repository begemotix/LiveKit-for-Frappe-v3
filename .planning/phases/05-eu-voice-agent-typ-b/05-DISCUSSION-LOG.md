# Phase 5: EU-Voice-Agent (Typ B) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-20
**Phase:** 05-eu-voice-agent-typ-b
**Areas discussed:** Agent naming, Failure strategy, Voice/language product boundary, ENV contract, voice precedence, architecture hooks, verification gates

---

## Agent naming convention

| Option | Description | Selected |
|--------|-------------|----------|
| Modus-basiert (`voice-eu`) | `agent_name` kodiert nur den Betriebsmodus | ✓ |
| Funktionsbasiert (`support-agent`, etc.) | `agent_name` kodiert Fachrolle/Funktion | |

**User's choice:** Modus-basiert (`voice-eu`).
**Notes:** Funktionale Rolle wird über kundenseitigen Prompt definiert, nicht über `agent_name`.

---

## Failure strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Hard-Fail | Bei Mistral/Voxtral-Ausfall: sauberes Session-Ende, keine Provider-Umschaltung | ✓ |
| Fallback auf Typ A | Ausfallszenario durch stillen Wechsel auf OpenAI-Realtime | |

**User's choice:** Hard-Fail.
**Notes:** DSGVO-Haltung bleibt strikt; Routing-Resilienz (OpenRouter o.ä.) ist separates Zukunftsthema außerhalb Phase 5.

---

## Voice/language product policy

| Option | Description | Selected |
|--------|-------------|----------|
| Kundengesteuerte ENV-Auswahl | Kunde setzt Sprache/Voice aus Voxtral-Liste | ✓ |
| Produktdefinierte Default-Voice | Vendor setzt feste Voice-Defaults | |

**User's choice:** Kundengesteuerte ENV-Auswahl.
**Notes:** Keine begemotix-seitige Produktentscheidung zu konkreten Voices.

---

## Pflicht-ENV pro Modus

| Option | Description | Selected |
|--------|-------------|----------|
| Gemeinsamer unscharfer ENV-Satz | Ein Mischset ohne mode-spezifische Pflichtdefinition | |
| Pflicht-ENV-Set pro Mode | Typ A und Typ B erhalten klar getrennte Pflichtvariablen | ✓ |

**User's choice:** Pflicht-ENV pro Mode.
**Notes:** Anpassung bestätigt: STT/TTS-Variablen heißen `VOXTRAL_STT_MODEL` und `VOXTRAL_TTS_MODEL` (nicht `MISTRAL_*`).

---

## Voice precedence contract

| Option | Description | Selected |
|--------|-------------|----------|
| `AGENT_VOICE_ID` bevorzugen | feste Voice-ID hat Vorrang | |
| `AGENT_VOICE_REF_AUDIO` bevorzugen | Referenz-Audio überschreibt Voice-ID bei Doppelbelegung | ✓ |

**User's choice:** `AGENT_VOICE_REF_AUDIO` hat Vorrang.
**Notes:** Gilt nur wenn beide Variablen gesetzt sind.

---

## Architektur-Hooks (ohne Feature-Ausbau)

| Option | Description | Selected |
|--------|-------------|----------|
| Hooks + Features sofort | Multi-Agent/Session-Switch direkt umsetzen | |
| Nur strukturelle Hooks | Factory/Interfaces vorbereiten, Features später aktivieren | ✓ |

**User's choice:** Nur strukturelle Hooks in Phase 5.
**Notes:** Spätere Aktivierung in Folgephasen vorgesehen.

---

## Verifikations-Gate

| Option | Description | Selected |
|--------|-------------|----------|
| Produkt-Hörtest als Gate | manuelle Voice-Abnahme als separates Gate | |
| Technischer Smoke-Test | STT/TTS-Funktionsnachweis, inkl. Sprachprüfung | ✓ |

**User's choice:** Technischer Smoke-Test.
**Notes:** Zusätzliche Präzisierung: mindestens zwei Sprachen (DE + EN) müssen im Smoke-Test abgedeckt sein.

---

## Claude's Discretion

- Interne Benennung ergänzender ENV-Variablen außerhalb der vom User fixierten Schlüssel.
- Konkrete Modulgrenzen für Factory/Prompt-Provider-Hooks.

## Deferred Ideas

- Aktives Session-Switching und Multi-Agent-Dispatch-Funktionalität.
- Prompt-Management als MCP-neutrale Laufzeitquelle.
- LLM-Routing-Resilienz über externe Router.
- Piper-Integration als self-hosted TTS-Alternative.
