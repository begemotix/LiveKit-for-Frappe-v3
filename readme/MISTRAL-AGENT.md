# Der Mistral-Agent (EU-Variante)

> Diese Anleitung richtet sich an **Kunden und Betreiber**, die
> den EU-Voice-Agenten mit Mistral und Voxtral einsetzen. Für
> die Standard-Variante mit OpenAI siehe
> [`SCHULUNG_GUIDE.md`](SCHULUNG_GUIDE.md) und
> [`COOLIFY-KONFIGURATION.md`](COOLIFY-KONFIGURATION.md).

---

## Worum geht es?

Unser Sprachassistent gibt es in zwei Ausführungen:

- **US-Variante (OpenAI)**: schnell und ausgereift, aber die
  Gesprächsdaten laufen über US-Infrastruktur.
- **EU-Variante (Mistral)**: in Europa gehostet. DSGVO-konformer,
  und die Antworten kommen flüssiger, weil der Agent intern
  anders arbeitet (dazu gleich mehr).

Diese Anleitung beschreibt die **EU-Variante**.

---

## Warum läuft der EU-Agent anders?

Stellen Sie sich einen Empfangsmitarbeiter vor, der am Telefon
sitzt und gleichzeitig Daten aus Ihrem ERP heraussucht. Es gibt
zwei Wege, wie er das organisieren kann:

**Weg 1 (alt):** Der Empfangsmitarbeiter sucht bei jeder Frage
selbst im ERP, hört dabei auf zu sprechen, sucht, und spricht
dann weiter. Das führt zu Pausen und "Ähm, einen Moment"-Fillern.

**Weg 2 (neu):** Ein schneller Assistent im Hintergrund übernimmt
die ERP-Suche. Der Empfangsmitarbeiter bekommt nur noch die
fertige Antwort geliefert und spricht sie flüssig aus. Keine
Pausen, kein Stottern.

Die EU-Variante nutzt **Weg 2**. Der schnelle Hintergrund-Assistent
ist Mistral (ein europäisches KI-Modell). Er steuert den Zugriff
auf Ihr ERP-System direkt und gibt dem Sprecher-Agenten nur den
fertigen Text zum Vorlesen.

**Für Sie als Kunden heißt das:**
- Kürzere Antwortzeiten, weniger Stottern.
- Die Persönlichkeit Ihres Agenten pflegen Sie nicht mehr in einer
  Datei auf dem Server, sondern bequem in der **Mistral Console**
  im Browser.

---

## Wo wird was eingestellt?

Die EU-Variante wird an **zwei Orten** konfiguriert. Das klingt
umständlich, ist aber praktisch: jede Änderung liegt dort, wo
sie hingehört.

| Was wollen Sie ändern? | Wo? | Wirkung |
|---|---|---|
| Persönlichkeit, Tonfall, Anweisungen | Mistral Console | Sofort, beim nächsten Gespräch |
| Modell-Wahl (z.B. Small/Medium) | Mistral Console | Sofort, beim nächsten Gespräch |
| Stimme des Agenten | Coolify (ENV) | Nach Deploy |
| Zugangsdaten (API-Keys, Frappe) | Coolify (ENV) | Nach Deploy |
| Sprache (Deutsch / Englisch) | Coolify (ENV) | Nach Deploy |

---

## Teil 1: Einstellungen in Coolify

Diese Variablen tragen Sie in der Coolify-Maske Ihrer Instanz ein.
Sie sind **zusätzlich** zu den allgemeinen Variablen aus
[`COOLIFY-KONFIGURATION.md`](COOLIFY-KONFIGURATION.md) — dort
stehen z.B. `DOMAIN`, `LIVEKIT_API_KEY` usw.

### Pflicht-Variablen (Produktion)

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `AGENT_MODE` | Muss auf `type_b` stehen, damit die EU-Variante aktiv ist. Leer lassen geht auch — `type_b` ist der Standard. | `type_b` |
| `MISTRAL_API_KEY` | Ihr API-Schlüssel von Mistral. **Als "Secret" / Hidden speichern.** | `W2xk…` |
| `MISTRAL_AGENT_ID` | Die ID des Agenten, den Sie in der Mistral Console angelegt haben (siehe Teil 2). Beginnt mit `ag_`. | `ag_01jxxxx…` |
| `VOXTRAL_STT_MODEL` | Das Voxtral-Modell fürs Verstehen gesprochener Sprache. | `voxtral-mini-latest` |
| `VOXTRAL_TTS_MODEL` | Das Voxtral-Modell für die Sprachausgabe. | `voxtral-mini-tts` |

### Stimme des Agenten (eine der beiden Varianten)

Sie wählen **entweder** eine Standardstimme **oder** eine eigene
Stimmprobe (für Voice-Cloning):

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `AGENT_VOICE_ID` | ID einer Standardstimme aus dem Voxtral-Katalog. | `de_anja_neutral` |
| `AGENT_VOICE_REF_AUDIO` | Pfad zu einer Audiodatei im Container (ca. 25–30 Sek. saubere Sprachprobe). Wenn gesetzt, gewinnt sie gegen `AGENT_VOICE_ID`. | `/app/voice_refs/de_anja.mp3` |

### Optionale Variablen

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `AGENT_LANGUAGE` | Sprache der Spracherkennung. Nur `de` oder `en`. | `de` |
| `FRAPPE_URL` / `FRAPPE_API_KEY` / `FRAPPE_API_SECRET` | Zugang zu Ihrer Frappe-Instanz. Identisch zur bisherigen Konfiguration. | `https://ihre-frappe.example` |

### Nur für Entwickler-Tests (nicht in Produktion setzen)

| Variable | Beschreibung |
|---|---|
| `MISTRAL_STATELESS_MODE` | Wenn auf `true` gesetzt, umgeht der Agent die Mistral Console und arbeitet direkt mit einem Modellnamen. **In Produktion leer lassen.** |
| `MISTRAL_LLM_MODEL` | Nur relevant, wenn `MISTRAL_STATELESS_MODE=true`. Dann z.B. `mistral-small-latest`. |

---

## Teil 2: Einstellungen in der Mistral Console

Die Mistral Console erreichen Sie unter
[https://console.mistral.ai](https://console.mistral.ai). Melden
Sie sich mit Ihrem Mistral-Konto an.

### Schritt 1 — Neuen Agenten erstellen

1. Linkes Menü: **Agenten** (oder "Agents").
2. Oben rechts: **Neuer Agent**.
3. Name vergeben, z.B. `Voice Assistant Produktion`.

### Schritt 2 — Modell wählen

- **Mistral Small** ist die empfohlene Wahl für gesprochene
  Assistenten: schnell und günstig.
- **Mistral Medium** ist besser, wenn der Agent schwierigere
  Nachfragen beantworten soll — dafür etwas langsamer.

Temperatur zwischen **0.4 und 0.6** ist ein guter Startwert.
Das sorgt für gleichmäßige, vorhersehbare Antworten.

### Schritt 3 — Integrierte Tools: alle ausschalten

In der Rubrik **Integrierte Tools** sehen Sie Schaltflächen wie
*Code*, *Bild*, *Suche*, *Premium-Suche*. **Bitte alle
deaktivieren** (oder gar nicht erst einschalten).

Unser Agent nutzt nur die Tools, die er über Ihren MCP-Server
(z.B. Frappe) bekommt — alles andere würde ihn nur verwirren.

### Schritt 4 — Funktionen: leer lassen

In der Rubrik **Funktionen** könnten Sie eigene JSON-Schemata
hinterlegen. **Tun Sie das nicht.** Die Funktionen für Ihren
MCP-Server trägt unser System automatisch bei jedem Gesprächsstart
ein. Manuelle Einträge würden zu Dubletten führen.

### Schritt 5 — Anweisungen (System-Prompt)

Das ist das Herzstück. Hier beschreiben Sie, **wer** der Agent
ist, **wie** er klingen soll und **welche Regeln** er einhält.

Beispiel als Startvorlage:

```
Du bist der Sprachassistent für die Begemotix GmbH. Du hilfst
Anrufern und Web-Besuchern, Informationen aus dem Firmen-ERP
abzurufen.

Regeln für deine Sprache:
- Antworte in maximal 50 Wörtern.
- Ein Satz hat höchstens 12 Wörter.
- Keine Aufzählungen, keine Schachtelsätze, keine Emoji.

Regeln für Tool-Aufrufe:
- Bevor du ein Tool aufrufst, sage kurz: "Einen Moment, ich
  schaue nach."
- Nutze Tools nur, wenn die Frage wirklich ERP-Daten braucht.
- Fasse das Tool-Ergebnis in einem einzigen Satz zusammen.

Persönlichkeit:
Freundlich, ruhig, kompetent. Kein Service-Chat-Sprech,
keine überflüssigen Höflichkeitsfloskeln.

Wenn ein Tool "403" oder "permission denied" zurückgibt,
antworte genau: "Darauf habe ich mit meinem Agent-Zugang
leider keinen Zugriff."
```

Sie können diesen Text frei anpassen — wie bei
[`AGENT_PROMPT.md`](AGENT_PROMPT.md) in der US-Variante. Die
Prinzipien aus [`SCHULUNG_GUIDE.md`](SCHULUNG_GUIDE.md) gelten
genauso.

### Schritt 6 — Antwortformat

**Text** (Standard). Nicht JSON, nicht Structured Output.

### Schritt 7 — Connectors: nicht anrühren

Links im Menü gibt es einen Bereich **Connectors**. Sie müssen
dort **nichts** einrichten. Unser MCP-Server (Frappe) läuft auf
Ihrer eigenen Infrastruktur und wird vom Agenten direkt
angesprochen — ohne Umweg über die Mistral Console. Wenn Sie
dort einen Connector anlegen, passiert nichts Schlimmes, aber
er wird auch nicht benutzt.

### Schritt 8 — Speichern und Agent-ID kopieren

1. **Speichern** klicken.
2. In der URL oder im Agent-Detail steht jetzt eine ID im Format
   `ag_01xxxxxxxxxx`.
3. Diese ID kopieren.
4. In Coolify als `MISTRAL_AGENT_ID` eintragen und speichern.
5. Die App in Coolify neu deployen.

Ab der nächsten Session spricht der Agent mit der neuen
Konfiguration.

---

## Wie ändere ich später etwas?

### "Der Agent soll höflicher klingen."
→ Mistral Console → Ihr Agent → **Anweisungen** bearbeiten →
**Speichern**. Wirkt beim nächsten Gespräch. Kein Deploy nötig.

### "Der Agent soll schneller / gescheiter antworten."
→ Mistral Console → Modell von *Small* auf *Medium* ändern (oder
umgekehrt) → **Speichern**. Wirkt beim nächsten Gespräch.

### "Der Agent soll eine andere Stimme haben."
→ Coolify → `AGENT_VOICE_ID` ändern (oder eine neue Referenz-
Audiodatei hochladen und `AGENT_VOICE_REF_AUDIO` anpassen) →
Deploy.

### "Wir haben einen neuen Mistral-API-Key."
→ Coolify → `MISTRAL_API_KEY` ersetzen → Deploy.

### "Wir möchten zurück auf die US-Variante."
→ Coolify → `AGENT_MODE=type_a` setzen, `OPENAI_API_KEY`
vorhanden halten → Deploy. Die EU-Variablen können drin bleiben,
sie werden ignoriert.

---

## Häufige Stolpersteine

**"Der Agent antwortet nicht mehr, nach einem Update."**
Prüfen Sie in den Coolify-Logs, ob eine Fehlermeldung erscheint
wie *"type_b production mode requires MISTRAL_AGENT_ID"*. Dann
ist das Feld leer oder der Wert hat einen Tippfehler.

**"Ich habe Funktionen in der Mistral Console eingetragen und
jetzt ruft der Agent dieselbe Funktion doppelt auf."**
Bitte die Funktionen in der Console wieder löschen. Unser System
trägt sie automatisch bei jedem Gespräch ein.

**"Die Stimme klingt komisch / abgehackt."**
Prüfen Sie, ob `AGENT_VOICE_REF_AUDIO` auf eine saubere
Audiodatei zeigt (Mono, 24 kHz, ca. 25 Sek., keine Hintergrund-
geräusche). Alternativ auf eine Standard-`AGENT_VOICE_ID`
wechseln.

**"Ich habe gleichzeitig `MISTRAL_AGENT_ID` und
`MISTRAL_STATELESS_MODE=true` gesetzt."**
In den Logs erscheint eine Warnung
(`mistral_agent_id_ignored_in_stateless_mode`). Der Stateless-
Modus ignoriert die Agent-ID bewusst. Für Produktion
`MISTRAL_STATELESS_MODE` entfernen.

---

## Kurzfassung

1. **Coolify** pflegen: Zugangsdaten, Stimme, Sprache.
2. **Mistral Console** pflegen: Persönlichkeit, Modell, Regeln.
3. **Nichts** in der Mistral Console bei "Funktionen" oder
   "Connectors" eintragen.
4. Agent-ID aus der Console in Coolify als `MISTRAL_AGENT_ID`
   hinterlegen.
5. Änderungen am System-Prompt wirken ohne Deploy; Änderungen
   an Coolify-Variablen brauchen einen Deploy.
