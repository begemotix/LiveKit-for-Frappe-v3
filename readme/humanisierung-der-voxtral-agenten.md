# Humanisierung der Voxtral-Agenten

## Umgesetzt (Tier 1 + 2, minimal-invasiv)

> Dieser Abschnitt dokumentiert den Ist-Zustand nach der ersten
> Umsetzungswelle. Für die vollständige Analyse und den
> Maßnahmenkatalog siehe die nachfolgenden Abschnitte.

### Tier 1 — Codeänderungen

| Maßnahme | Datei | Diff | Erwarteter Effekt |
|---|---|---|---|
| Greeting nicht-blockierend als Task | `apps/agent/agent.py` | `await session.say(...)` → `asyncio.create_task(_speak_greeting())` + nutzt jetzt wirklich `INITIAL_GREETING` + `AGENT_NAME` statt hartkodiertem "Hallo, wie kann ich helfen?" | −300 bis −800 ms wahrgenommene Start-Latenz; Branding funktioniert wieder. |
| Interruption `min_duration` 1.2 → 0.6 s | `apps/agent/agent.py` (beide AgentSession-Blöcke) | Schnelleres Barge-in | Agent fühlt sich nicht mehr "taub" bei Unterbrechungen. |
| VAD `min_silence_duration` 0.3 → 0.2 s | `apps/agent/agent.py` (`prewarm_fnc`) | Silero-Endpoint reagiert schneller | ~100 ms Ersparnis nach jedem User-Turn. |
| Filler-Pool statt Einzelphrase | `apps/agent/src/mistral_agent.py` | `DEFAULT_FILLER_TEXT` (str) → `DEFAULT_FILLER_TEXTS` (list) + `random.choice` in `_speak_filler` | Kein "Papagei-Effekt" mehr nach 2–3 Tool-Calls. |

**Bewusst nicht angefasst:**

- Cursors Punkt #4 ("Filler für type_b deaktiviert") — war beim
  Schreiben des Plans bereits aktiv über `FillerAwareMCPClient` /
  `MistralOrchestrator._fire_filler_if_needed` (Commits `6abfdff` /
  `665b2af`). Cursor hatte die alte Dormant-Funktion
  `_apply_filler_to_toolset` gelesen, die ohne Call-Site liegt.
- Cursors Punkt #5 ("Timed Fallback Filler") — bewusst nicht
  reaktiviert, wurde vorher entfernt, weil er "lügt" (sagte "Ich
  sehe nach" auch wenn das LLM nur nachgedacht, nicht tatsächlich
  ein Tool gerufen hat). Begründung im Kommentar in
  `mistral_orchestrator.py:137`.

### Tier 2 — Konfiguration in der Mistral Console

**Stiller Fehler, den die Tier-1-Edits nicht heilen:**
Die Pacing- und Agentic-Instruktionen aus `agent.py` (ca.
Zeilen 225–239) werden im Produktionsmodus (mit
`MISTRAL_AGENT_ID`) **nicht an Mistral gesendet** — siehe
`mistral_orchestrator.py` → `run_turn`: `instructions` wird nur
übergeben, wenn `self._model is not None` (also nur im
Stateless-/Dev-Modus). Im Agent-ID-Modus gewinnt der
Console-Prompt. Das heißt: die App-internen Regeln ("max. 12
Wörter", "max. 50 Wörter", "variiere Formulierungen") kommen
beim LLM nie an.

**Lösung ohne Code-Deploy:** Der Console-Prompt muss die
Humanisierungs-Regeln selbst tragen. Die empfohlene Vorlage
steht in [`MISTRAL-AGENT.md`](MISTRAL-AGENT.md) → Schritt 5.
Pflegen in <https://console.mistral.ai> → Ihr Agent →
Anweisungen → Speichern. Wirkt ab dem nächsten Gespräch.

### Verifikation

- `uv run pytest` (Agent): alle bestehenden Tests grün, plus
  zwei neue Tests für den Filler-Pool
  (`test_speak_filler_rotates_across_pool_via_random_choice`,
  `test_filler_texts_constructor_overrides_default_pool`).
- Manuell: eine Testsession mit drei Tool-Calls starten —
  Log-Feld `filler_pool_size=4` und unterschiedliche
  `filler_text_length`-Werte in den
  `mistral_agent_filler_spoken`-Events beobachten.

### Bewusst für eine spätere Welle zurückgestellt

- Pre-synthesized Audio (Greeting + Filler): lohnt sich erst,
  wenn die Tier-1-Edits real gemessen nicht reichen.
- Text-Normalisierung (Zahlen, "Frappe"-Phonetik): ~20 LOC in
  `MistralDrivenAgent.llm_node`, aber erfordert kleines
  Benchmark.
- Dynamic Endpointing über LiveKits Turn-Detector-Modell: neue
  Dependency, eigener Release-Zyklus.
- Preemptive Generation in `type_b`: großer Orchestrator-Umbau,
  Nutzen gegenüber Mistral-Console-Latenzen unklar.

---

## Zweck
Dieses Dokument dient als verbindliche technische und architektonische Umsetzungsgrundlage für die Verbesserung der Nutzererfahrung (UX) und der wahrgenommenen Natürlichkeit unserer Voice-Agenten. Es analysiert die aktuelle Implementierung gegen offizielle LiveKit-Maßnahmen und definiert einen klaren Maßnahmenkatalog zur Reduktion von "toter Luft", zur Beschleunigung der Interaktion und zur Steigerung der Sprachqualität.

## Executive Summary
Unsere aktuelle App nutzt die Möglichkeiten des LiveKit Frameworks zur "Humanisierung" der Voice-Interaktion nur in Ansätzen. Während die technische Basis (VAD, STT, LLM, TTS) steht, fehlen fast alle fortgeschrittenen Mechanismen zur Latenz-Kaschierung und zur natürlichen Gesprächsführung.

**Hauptprobleme:**
- Die Begrüßung erfolgt seriell nach dem vollständigen Session-Start und löst eine frische TTS-Synthese aus, was zu spürbaren Verzögerungen führt.
- Der `type_b` Pfad (Mistral EU) hebelt durch den externen Orchestrator und den `llm_node`-Override viele automatische LiveKit-Optimierungen wie `preemptive_generation` faktisch aus.
- Es gibt keine proaktive Überbrückung von Tool-Wartezeiten (Filler), obwohl Ansätze im Code existieren (diese sind für `type_b` deaktiviert).
- Die Aussprache und Intonation von Voxtral-TTS wird kaum durch Text-Preprocessing oder gezieltes Prompting optimiert.

**Potential:**
Durch die konsequente Nutzung von pre-synthesized Audio, dynamischem Endpointing und "Early Greeting" Mustern kann die wahrgenommene Latenz um bis zu 1-2 Sekunden gesenkt werden, ohne den LLM-Kern zu verändern. Die harte Grenze bleibt die Rechenzeit des externen Mistral-Agenten und die Netzwerk-Latenz des Voxtral-TTS-Providers.

## Tabelle der Maßnahmen

| Maßnahme | Offizielle LiveKit-Quelle | Was LiveKit darunter versteht | Erwartete Wirkung | Für unseren Stack geeignet? | Aktueller Stand in unserer App | Konkreter Codebeleg | Priorität | Entwicklerhinweis |
|---|---|---|---|---|---|---|---|---|
| 1. Preemptive generation | [Agent session](https://docs.livekit.io/agents/logic/sessions/) | Startet LLM-Inferenz basierend auf STT-Interim-Resultaten vor dem finalen Endpointing. | Reduziert TTFT (Time to first token) durch spekulatives Rechnen. | Teilweise (Eingeschränkt durch Orchestrator) | Faktisch nicht genutzt | `apps/agent/agent.py` Z. 279-284 (für type_a disabled), Z. 312-315 (type_b nicht gesetzt) | Zweite Welle | Muss im Orchestrator auf Interim-Transkripte reagieren können. |
| 2. Preemptive TTS | [Agent session](https://docs.livekit.io/agents/logic/sessions/) | Startet TTS-Synthese spekulativ, sobald erste LLM-Tokens vorliegen. | Minimiert Lücke zwischen LLM-Ende und Audio-Start. | Ja, direkt geeignet | Teilweise genutzt | `apps/agent/agent.py` Z. 281 (type_a), in type_b implizit durch Streaming. | Sofort umsetzen | Explizit in `TurnHandlingOptions` für type_b prüfen. |
| 3. Pre-synthesized greeting | [Audio customization](https://docs.livekit.io/agents/multimodality/audio/customization/) | Abspielen einer vorbereiteten Audio-Datei für die Begrüßung statt Live-Synthese. | Sofortige hörbare Reaktion nach Verbindungsaufbau (~50ms statt ~1s). | Ja, direkt geeignet | Faktisch nicht genutzt | `apps/agent/agent.py` Z. 420 (nutzt `session.say` mit Text) | Sofort umsetzen | Begrüßung als PCM-Frames vorladen und in `say(audio=...)` nutzen. |
| 4. Pre-synthesized hold/filler | [Audio customization](https://docs.livekit.io/agents/multimodality/audio/customization/) | Vorgerenderte "Einen Moment"-Phrasen zur Überbrückung von Tool-Calls. | Verhindert "tote Luft" bei MCP-Aufrufen (z.B. Frappe-Query). | Ja, direkt geeignet | Vorhanden, aber wirkungslos | `apps/agent/agent.py` Z. 118-167 (Filler-Logik für type_b deaktiviert) | Sofort umsetzen | Filler-Logik für type_b reaktivieren und auf pre-synthesized Audio umstellen. |
| 5. Timed fallback filler | [Audio customization](https://docs.livekit.io/agents/multimodality/audio/customization/) | Automatisches Abspielen eines Fillers, wenn das LLM nach X ms noch nicht geantwortet hat. | Kaschiert langsame LLM-Inferenz oder Netzwerk-Lags. | Ja, direkt geeignet | Faktisch nicht genutzt | Kein Beleg (fehlt vollständig) | Zweite Welle | Timer in `llm_node` starten und bei Token-Eingang abbrechen. |
| 6. Interruptible filler speech | [Agent speech](https://docs.livekit.io/agents/multimodality/audio/) | Filler werden sofort abgebrochen, sobald die echte Antwort bereit ist. | Verhindert unnötige Verzögerung durch zu lange Füllsätze. | Ja, direkt geeignet | Teilweise genutzt | `apps/agent/agent.py` Z. 147 (allow_interruptions=True) | Nice-to-have | Sicherstellen, dass `handle.interrupt()` zuverlässig triggert. |
| 7. Early greeting pattern | [Agent session](https://docs.livekit.io/agents/logic/sessions/) | Auslösen der Begrüßung parallel zum Session-Start / STT-Warmup. | Wahrnehmung: Agent ist "sofort da". | Ja, direkt geeignet | Faktisch nicht genutzt | `apps/agent/agent.py` Z. 404-420 (sequenzieller Ablauf) | Sofort umsetzen | `session.say` parallel zu `session.start` in Task auslagern. |
| 8. Turn-handling tuning | [Turns overview](https://docs.livekit.io/agents/logic/turns/) | Feinjustierung von `min_silence_duration` und `endpointing_delay`. | Schnelleres Erkennen des Sprechenden-Wechsels. | Ja, direkt geeignet | Teilweise genutzt | `apps/agent/agent.py` Z. 96-103 (VAD-Settings) | Sofort umsetzen | `min_silence_duration` von 0.3s auf 0.2s-0.25s testen. |
| 9. Dynamic endpointing | [Turn detector](https://docs.livekit.io/agents/logic/turns/turn-detector/) | Agent passt Wartezeit auf Turn-Ende dynamisch an Gesprächspausen an. | Reduziert Verzögerung nach kurzen Sätzen, lässt Zeit bei langen Pausen. | Ja (Python SDK Feature) | Faktisch nicht genutzt | `apps/agent/agent.py` Z. 272/305 (fest auf "vad") | Zweite Welle | Auf `dynamic` umstellen und min/max Delay definieren. |
| 10. Adaptive interruption | [Turns overview](https://docs.livekit.io/agents/logic/turns/) | Unterscheidet zwischen kurzem Huster/Geräusch und echter Unterbrechung. | Agent bricht nicht bei jedem Nebengeräusch ab. | Ja, direkt geeignet | Teilweise genutzt | `apps/agent/agent.py` Z. 273-278 (feste Interruption-Werte) | Nice-to-have | `min_duration` auf 1.2s ist sehr konservativ (langsam). |
| 11. Audio customization | [Audio customization](https://docs.livekit.io/agents/multimodality/audio/customization/) | Kontrolle der Aussprache über SSML oder Phoneme (falls vom Plugin unterstützt). | Korrekte Aussprache von Fachbegriffen (Frappe, ERPNext). | Teilweise (Provider-abhängig) | Faktisch nicht genutzt | Kein Beleg (fehlt vollständig) | Zweite Welle | Custom Dictionary für Eigennamen implementieren. |
| 12. Output shaping | [Logic hooks](https://docs.livekit.io/agents/logic/nodes/) | Automatisches Ersetzen von Abkürzungen oder Formatieren von Zahlen vor TTS. | Vermeidet hölzerne Aussprache ("1." -> "Erstens"). | Ja, direkt geeignet | Faktisch nicht genutzt | Kein Beleg (fehlt vollständig) | Sofort umsetzen | RegEx-basierte Normalisierung im `llm_node` vor dem Yielden. |
| 13. Voice prompting | [Multimodality](https://docs.livekit.io/agents/multimodality/audio/) | System-Prompts, die den Agenten zu natürlicherem Sprechen (Pausen, Füllwörter) anweisen. | Agent klingt weniger wie ein Vorlese-Roboter. | Ja, direkt geeignet | Bereits genutzt | `apps/agent/agent.py` Z. 215-229 | Nice-to-have | Bestehende Instruktionen um "Atempausen" und "Empathie" erweitern. |
| 14. Short-form rules | [Multimodality](https://docs.livekit.io/agents/multimodality/audio/) | Strikte Regeln für die Länge der Antworten (max 12-15 Wörter). | Verhindert "Vorträge" des Agenten, hält Gesprächsdynamik hoch. | Ja, direkt geeignet | Bereits genutzt | `apps/agent/agent.py` Z. 216 (max 12 Wörter) | Bereits gut | Fokus auf Beibehaltung dieser Regel bei Refactorings. |
| 15. Background audio | [Agent speech](https://docs.livekit.io/agents/multimodality/audio/) | Einspielen von leisem Hintergrundgeräusch (Tippen, Atmen) während LLM rechnet. | Verringert Unbehagen in der Stille ("Thinking audio"). | Ja, direkt geeignet | Faktisch nicht genutzt | Kein Beleg (fehlt vollständig) | Nice-to-have | Dezente "Typing"-Sounds während Tool-Calls einblenden. |
| 16. Pipeline hooks | [Pipeline nodes](https://docs.livekit.io/agents/logic/nodes/) | Nutzung von `on_user_turn_completed` für Vorab-Logik. | Vorbereiten von Kontext oder Metriken vor der Inferenz. | Ja, direkt geeignet | Faktisch nicht genutzt | Kein Beleg (fehlt vollständig) | Zweite Welle | Metriken-Logging hier zentralisieren statt in `agent.py`. |
| 17. Tool-Überbrückung | [Function tools](https://docs.livekit.io/agents/logic/tools/definition/) | Akustisches Feedback bei Start und Ende eines Tool-Calls. | Transparenz für den Nutzer bei Verzögerungen durch Technik. | Ja, direkt geeignet | Faktisch nicht genutzt | `apps/agent/agent.py` Z. 330-333 (nur Logging) | Sofort umsetzen | `session.say` bei `on_function_call_start` triggern. |
| 18. Greeting Fast-Path | [Agent session](https://docs.livekit.io/agents/logic/sessions/) | Hartcodierte Begrüßung ohne LLM-Involvierung. | Minimale Latenz beim ersten Kontakt. | Ja, direkt geeignet | Bereits genutzt | `apps/agent/agent.py` Z. 420 | Bereits gut | Um pre-synthesized Audio (Punkt 3) ergänzen. |
| 19. TTS-Caching | [Audio customization](https://docs.livekit.io/agents/multimodality/audio/customization/) | Wiederverwendung von Audio-Frames für identische Text-Phrasen. | Spart Kosten und Latenz für Standard-Antworten. | Ja, direkt geeignet | Faktisch nicht genutzt | Kein Beleg (fehlt vollständig) | Zweite Welle | LRU-Cache für TTS-Antworten implementieren. |
| 20. Metrics Feedback | [Data hooks](https://docs.livekit.io/deploy/observability/data/) | Echtzeit-Überwachung der Pipeline-Latenzen (TTFT, TTFB). | Datengrundlage für kontinuierliche Optimierung. | Ja, direkt geeignet | Bereits genutzt | `apps/agent/src/metrics_listener.py` | Bereits gut | Metriken zur automatischen Anpassung von Timeouts nutzen. |

## Begrüßung

| Thema | LiveKit-Best-Practice | Stand bei uns | Problem | Empfehlung |
|---|---|---|---|---|
| Latenz | Early Greeting (Parallel zum Start) | Sequenziell nach `session.start` | Nutzer wartet ~1-2s auf das erste Lebenszeichen. | `session.say` sofort nach `ctx.connect()` in Background-Task starten. |
| Synthese | Pre-synthesized Audio | Live-TTS Synthese | Auch statische Begrüßungen kosten Synthese-Zeit beim Provider. | Begrüßung als .mp3/.wav vorhalten und direkt abspielen. |
| Blockierung | Unblockiertes `say()` | `await session.say(...)` | Das Programm wartet, bis der Satz fertig "gesagt" wurde. | `asyncio.create_task(session.say(...))` nutzen oder Audio-Argument verwenden. |

**Analyse:**
Die Begrüßung in `agent.py` (Z. 420) blockiert den weiteren Ablauf und nutzt keine gecachten Audio-Daten. Dies ist der erste negative Eindruck für den Nutzer.

## Voxtral-TTS natürlicher machen

| Hebel | Quelle | Was damit verbessert wird | In unserer App heute | Realistische Wirkung bei Voxtral |
|---|---|---|---|---|
| Prompting | [Multimodality](https://docs.livekit.io/agents/multimodality/audio/) | Stilistische Anweisungen (kurz, prägnant, lebendig). | Vorhanden (`pacing_instructions`) | Mittel (Modell-abhängig) |
| Normalisierung | [Speechify Plugin (Beispiel)](https://docs.livekit.io/agents/models/tts/speechify/) | Wandelt Zahlen, Daten, Symbole in Sprechtext um. | Nicht vorhanden | Hoch (Verhindert "hölzerne" Zahlenlesung) |
| Pronunciation | [MiniMax Plugin (Beispiel)](https://docs.livekit.io/agents/models/tts/minimax/) | Definition von Aussprache-Regeln für Eigennamen. | Nicht vorhanden | Hoch für "Frappe", "ERPNext" etc. |
| Empathie-Tags | [LiveKit Blog](https://livekit.io/blog) | Einbau von Pausen (`...`) oder emotionalen Markern. | Ansatzweise über Punktierung | Gering bei Voxtral (begrenzte SSML-Stütze) |

**Analyse:**
LiveKit kann nur den Text optimieren, den es an Voxtral sendet. Wenn Voxtral selbst keine Emotionen unterstützt, kann LiveKit dies nicht "erfinden". Aber: Schlechte Zahlenaussprache ("eins punkt null") ist ein lösbares Problem im App-Code.

## Was wir bereits nutzen
- **VAD Prewarming:** (`agent.py` Z. 95-103) - Reduziert Kaltstart-Latenz für die Spracherkennung.
- **Short-form Prompting:** (`agent.py` Z. 215-229) - Zwingt das LLM zu schnellen, kurzen Antworten.
- **Structured Metrics:** (`src/metrics_listener.py`) - Erfasst Latenzen für die Analyse.
- **Correlation ID Tracking:** (`agent.py` Z. 172-180) - Ermöglicht Trace-Analysen über die gesamte Pipeline.

## Was aktuell fehlt
- **Pre-synthesized Audio:** Keine statischen Audio-Dateien für Standard-Interaktionen.
- **Text-Normalisierung:** Keine Vorverarbeitung von Zahlen/Daten für das TTS.
- **Filler-Integration für type_b:** Die existierende Filler-Logik ist im EU-Pfad inaktiv.
- **Dynamic Endpointing:** Wir nutzen starre VAD-Timer statt adaptiver Logik.
- **Early Greeting Pattern:** Die Begrüßung wartet auf die vollständige Session-Bereitschaft.

## Priorisierte 80%-Umsetzung

| Rang | Maßnahme | Warum sie in den 80% ist | Erwarteter Nutzen | Aufwand | Typ |
|---|---|---|---|---|---|
| 1 | Pre-synthesized Greeting | Größter Hebel für den ersten Eindruck. | ~1s Zeitersparnis beim Start | Gering | UX-Fix |
| 2 | Early Greeting Pattern | Parallelisierung statt Serialisierung. | ~0.5s Zeitersparnis beim Start | Gering | Performance-Fix |
| 3 | Text-Normalisierung (RegEx) | Verhindert "Roboter-Sound" bei Zahlen/Daten. | Deutlich natürlichere Aussprache | Mittel | Sprachqualitäts-Fix |
| 4 | Reaktivierung Filler für type_b | Verdeckt Latenz bei Tool-Calls (Frappe). | Weniger wahrgenommene Latenz | Mittel | UX-Fix |
| 5 | Dynamic Endpointing | Macht das Gespräch flüssiger (weniger Warten). | ~0.2s Zeitersparnis pro Turn | Mittel | Performance-Fix |
| 6 | TTS-Pronunciation (Frappe) | Fachbegriffe werden korrekt ausgesprochen. | Professionellerer Eindruck | Gering | Sprachqualitäts-Fix |
| 7 | Preemptive TTS Aktivierung | Schnellerer Audio-Start nach LLM-Tokens. | ~0.1-0.3s Zeitersparnis | Gering | Performance-Fix |
| 8 | Timed Fallback Filler | Rettet die UX bei langsamen LLM-Inferenzen. | Verhindert Gesprächsabbruch | Hoch | UX-Fix |
| 9 | Audio Customization (SSML) | Mehr Kontrolle über Pausen und Betonung. | Lebendigere Sprache | Mittel | Sprachqualitäts-Fix |
| 10 | Background "Thinking" Audio | Kaschiert technische "Bedenkzeit". | Höhere Akzeptanz bei Latenz | Gering | UX-Fix |

## Nicht diskutieren, sondern umsetzen
Folgende Maßnahmen sind ohne weitere Abstimmung als technischer Standard zu implementieren:
1. **Punkte 1 & 2 (Greeting-Optimierung):** Das aktuelle Warten auf den Session-Start und die Live-Synthese ist ein vermeidbarer Architekturfehler.
2. **Punkt 3 (Text-Normalisierung):** Zahlen und Daten müssen vor der Übergabe an das TTS-Plugin zwingend in Wortform (oder TTS-optimierte Form) gebracht werden.
3. **Punkt 4 (Filler):** Ein Voice-Agent ohne akustische Bestätigung beim Warten auf Daten ist für Nutzer verwirrend.
4. **Punkt 5 (Dynamic Endpointing):** Die Standard-Werte für VAD sind oft zu träge für natürliche Gespräche.

Maßnahmen wie **SSML-Feintuning** oder **Background-Audio** können in einer zweiten Welle nach Nutzertests erfolgen. Die **Preemptive Generation** im `type_b` Pfad erfordert eine tiefere Prüfung der Orchestrator-Fähigkeiten und steht unter Vorbehalt.
