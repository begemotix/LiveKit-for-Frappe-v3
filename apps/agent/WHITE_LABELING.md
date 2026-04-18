# White Labeling Guide

Dieses Dokument beschreibt, wie Partner den Agenten ohne Codeanpassungen per Environment-Variablen branden und verifizieren.

## Konfigurationsvariablen

### `AGENT_NAME`
- Zweck: Anzeigename des Assistenten in Begruessung und Persona-Texten.
- Beispiel: `AGENT_NAME=Clara`

### `COMPANY_NAME`
- Zweck: Firmenname fuer Persona und Begruessung.
- Beispiel: `COMPANY_NAME=Begemotix`

### `ROLE_DESCRIPTION`
- Zweck: Basis-Prompt fuer Verhalten und Tonalitaet.
- Platzhalter: `{AGENT_NAME}`, `{COMPANY_NAME}`
- Beispiel:
  `ROLE_DESCRIPTION=You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}. Keep answers concise and friendly.`

### `INITIAL_GREETING`
- Zweck: Erste, unterbrechbare Begruessung nach Pflichtansage.
- Platzhalter: `{AGENT_NAME}`, `{COMPANY_NAME}`
- Beispiel:
  `INITIAL_GREETING=Hallo, ich bin {AGENT_NAME} von {COMPANY_NAME}. Wie kann ich helfen?`

### `MANDATORY_ANNOUNCEMENT`
- Zweck: DSGVO-/Compliance-Hinweis, der vor der Begruessung abgespielt wird.
- Standardfall: Hinweis auf KI-Nutzung und Datenverarbeitung.
- Beispiel:
  `MANDATORY_ANNOUNCEMENT=Hinweis: Sie sprechen mit einem KI-Assistenten. Audio-Daten werden zur Verarbeitung an OpenAI in den USA uebertragen.`

### `AGENT_VOICE`
- Zweck: Zielstimme fuer den Voice-Agenten (providerabhaengig).
- Beispiel: `AGENT_VOICE=alloy`

### `VAD_THRESHOLD`
- Zweck: Empfindlichkeit fuer Voice Activity Detection.
- Typisch: `0.3` bis `0.7`
- Beispiel: `VAD_THRESHOLD=0.5`

### `VAD_SILENCE_DURATION_MS`
- Zweck: Dauer der Stille (ms), nach der ein Turn als beendet gilt.
- Beispiel: `VAD_SILENCE_DURATION_MS=500`

## Legal Compliance

- Die Pflichtansage muss vor inhaltlicher Konversation abgespielt werden.
- `MANDATORY_ANNOUNCEMENT` sollte rechtlich mit eurem Datenschutztext abgestimmt sein.
- Fuer DACH-Betrieb wird ein expliziter Hinweis auf KI-Nutzung und Drittlandverarbeitung empfohlen.

## Runtime Verification Checklist (Phase-3 Success Criteria)

Nach Deployment in einer echten LiveKit-Session pruefen:

### 1) DSGVO-Ansage
- [ ] Beim Join wird zuerst die Pflichtansage aus `MANDATORY_ANNOUNCEMENT` gesprochen.
- [ ] Die Ansage laesst sich nicht durch Nutzerunterbrechung abbrechen.
- [ ] Erst danach startet `INITIAL_GREETING`.

### 2) Interruption
- [ ] Waehrend der Begruessung kann der Nutzer den Agenten unterbrechen.
- [ ] Bei Unterbrechung stoppt die laufende Agenten-Audioausgabe sofort.
- [ ] Der Agent reagiert auf den neuen Nutzerturn ohne merkliche Haenger.

### 3) Filler vor Tool-Call
- [ ] Bei ausgeloestem Tool-Call spricht der Agent zuerst einen kurzen Filler-Satz ("Einen Moment ...").
- [ ] Der Filler kommt vor dem eigentlichen Tool-Ergebnis.
- [ ] Der Filler passt zur Sprache des Nutzers (z. B. Deutsch/Englisch).
