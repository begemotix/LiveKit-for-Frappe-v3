# Leitfaden: So schulen Sie Ihren KI-Agenten

Willkommen bei Ihrem LiveKit Voice Assistant. Dieses Dokument erklärt Ihnen, wie Sie das Verhalten, die Persönlichkeit und das Wissen Ihres sprechenden Agenten anpassen können.

Dieser Leitfaden gilt unabhängig vom angebundenen Backend -
ob Frappe, ein anderes ERP oder ein beliebiger MCP-Server.
Die Instruktionen des Agenten beschreiben sein Verhalten und
seine Persönlichkeit; die Daten, auf die er zugreifen kann,
kommen aus dem konfigurierten MCP-Server.

## Das Prinzip: "Training" per Markdown
Im Gegensatz zu klassischer Software wird dieser Agent nicht programmiert, sondern instruiert. Das Herzstück ist die Datei `AGENT_PROMPT.md`. Alles, was Sie dort hineinschreiben, definiert, wie der Agent auf Anrufe oder Web-Besucher reagiert.

### Wann werden die Informationen übertragen?
*   **Zeitpunkt**: Jedes Mal, wenn ein neues Gespräch beginnt (Web-Widget geöffnet oder Telefonanruf entgegengenommen).
*   **Weg**: Der Server liest die `AGENT_PROMPT.md` ein und sendet den Inhalt verschlüsselt via WebSocket direkt an das KI-Modell (OpenAI Realtime API).
*   **Sicherheit**: Die Informationen werden nur für die Dauer des aktuellen Gesprächs genutzt und danach "vergessen". Es findet kein dauerhaftes Training des öffentlichen KI-Modells mit Ihren Daten statt.

## Best Practices für die Gestaltung
1.  **Identität**: Geben Sie dem Agenten einen Namen und eine klare Rolle (z.B. "Du bist eine freundliche Empfangsdame...").
2.  **Zielgruppe**: Beschreiben Sie, mit wem der Agent spricht (z.B. "Deine Kunden sind meist ältere Menschen oder Handwerker").
3.  **Tonalität**: Definieren Sie den Sprachstil (z.B. "Sprich ruhig, deutlich und verwende keine Anglizismen").
4.  **Wissen**: Fügen Sie wichtige Fakten über Ihr Unternehmen ein (Öffnungszeiten, Leistungen, Ansprechpartner).

## Änderungen übernehmen
Sobald Sie die Datei `AGENT_PROMPT.md` auf dem Server speichern, nutzt der Agent beim **nächsten Gespräch** automatisch die neuen Instruktionen. Ein Neustart der gesamten App ist in der Regel nicht erforderlich.
