# Operator Handover - Phase 05 EU Voice Agent (Typ B)

## Coolify-ENV-Variablen

| Name | Zweck | Default | Beispielwert | Hinweis |
| --- | --- | --- | --- | --- |
| `AGENT_MODE` | Schaltet Agent-Betriebsmodus (Typ A/Typ B) | `type_b` | `type_b` | Pflicht fuer expliziten Modus-Switch, sonst Typ B |
| `MISTRAL_API_KEY` | API-Key fuer Mistral LLM/STT/TTS | leer | `mistral_xxx` | Pflicht in Typ B |
| `VOXTRAL_STT_MODEL` | STT-Modellname fuer Voxtral | leer | `voxtral-mini-transcribe` | Pflicht in Typ B |
| `VOXTRAL_TTS_MODEL` | TTS-Modellname fuer Voxtral | leer | `voxtral-mini-tts-2603` | Pflicht in Typ B |
| `AGENT_VOICE_REF_AUDIO` | Referenz-Audio-Dateipfad fuer Zero-Shot Voice Cloning | leer | `/app/voice_refs/voice_ref_de.mp3` | Hat Vorrang vor `AGENT_VOICE_ID` (Decision D-08) |
| `AGENT_VOICE_ID` | Preset-Voice-ID als Fallback wenn kein `AGENT_VOICE_REF_AUDIO` gesetzt ist | leer | `en_paul_neutral` | Wird ignoriert, sobald `AGENT_VOICE_REF_AUDIO` gesetzt ist |
| `AGENT_NUM_IDLE_PROCESSES` | Anzahl vorgewaermter Agent-Prozesse, die idle auf neue Jobs warten; reduziert Cold-Start-Latenz | `2` | `2` | Optional; ca. 500-700 MB RAM pro Idle-Process (Python + Silero VAD vorgewaermt). Empfehlung: `2` normal, `1` fuer RAM-knappe VPS, `0` deaktiviert Pre-Warming (nicht empfohlen). |
| `NEXT_PUBLIC_GDPR_NOTICE` | Browser-Hinweistext fuer DSGVO im Frontend | leer | leer | im aktuellen Architekturstand ungenutzt — siehe Decision D-B |

## Konfigurierbare Komponenten

- Agent-Betriebsmodus ueber `AGENT_MODE`.
- Mistral/Voxtral Modellwahl ueber `VOXTRAL_STT_MODEL`, `VOXTRAL_TTS_MODEL`, `MISTRAL_LLM_MODEL`.
- Stimme im Typ-B-Pfad ueber `AGENT_VOICE_REF_AUDIO` (bevorzugt) oder `AGENT_VOICE_ID`.
- Worker-Warm-Pool ueber `AGENT_NUM_IDLE_PROCESSES`.

## Nicht-konfigurierbare Komponenten

- Frappe-Anbindung bleibt MCP-stdio-basiert (`MCPServerStdio` + `MCPToolset`) gemaess bestehender Architekturentscheidungen aus Phase 04.
- Kein stiller Fallback von Typ B nach Typ A bei Provider-Fehlern (Hard-Fail-Policy in Phase 05).
- Prompt-Datei `readme/AGENT_PROMPT.md` bleibt Uebergangsloesung — wird in Phase 06 durch dynamisches Prompt-Management ersetzt (Decision D-A).

## Handover-Checkliste fuer den Onboarding-Termin

- [ ] `MISTRAL_API_KEY`, `VOXTRAL_STT_MODEL`, `VOXTRAL_TTS_MODEL` gesetzt und gegen Zielumgebung verifiziert.
- [ ] Voice-Pfad entschieden und dokumentiert: `AGENT_VOICE_REF_AUDIO` oder `AGENT_VOICE_ID`.
- [ ] Wenn `AGENT_VOICE_REF_AUDIO` genutzt wird: Datei im Container unter `/app/voice_refs/...` vorhanden und lesbar.
- [ ] `AGENT_NUM_IDLE_PROCESSES` passend zur RAM-Kapazitaet gesetzt (2/1/0 gemaess Empfehlung).
- [ ] Operator kennt Scope-Grenze: Prompt-Management ist Uebergang und wird in Phase 06 erweitert (Decision D-A).
