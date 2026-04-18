---
status: blocked
phase: 03-agent-core
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md
started: 2026-04-18T18:02:24.3824851+02:00
updated: 2026-04-18T18:05:09.0338646+02:00
---

## Current Test

[testing blocked — Runtime-Deployment auf Coolify ausstehend]

## Tests

### 1. DSGVO-Ansage beim Join
expected: Beim Betreten des Raums spricht der Agent zuerst die Pflichtansage aus `MANDATORY_ANNOUNCEMENT`, nicht unterbrechbar, danach Begrüßung.
result: pending

### 2. Interruption in normaler Konversation
expected: Während der normalen Begrüßung/Antwort kann der Nutzer unterbrechen und die laufende Agenten-Ausgabe stoppt unmittelbar.
result: pending

### 3. Filler vor Tool-Call
expected: Bei einem Tool-Call sagt der Agent zuerst einen kurzen Filler-Satz in Nutzersprache und liefert erst danach das Tool-Ergebnis.
result: pending

### 4. Mock-Tool Antwortverhalten
expected: Der Mock-Tool-Aufruf liefert eine erfolgreiche Antwort mit Nutzlast zum Query (`status: success`, `data` enthält die Suchanfrage) nach kurzer Wartezeit.
result: pending

## Summary

total: 4
passed: 0
issues: 0
pending: 0
skipped: 0
blocked: 4

## Gaps

- blocked_by: deployment
  reason: "Runtime-Deployment auf Coolify ausstehend"
