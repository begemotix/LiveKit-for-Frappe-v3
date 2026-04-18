# Phase 1: Infrastructure Setup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 1-Infrastructure Setup
**Areas discussed:** LiveKit Basis-Setup, Reverse Proxy, TURN-Server, Environment Variables

---

## LiveKit Basis-Setup

| Option   | Description                                                             | Selected |
| -------- | ----------------------------------------------------------------------- | -------- |
| Standard | Standard (Single Node) — Einfachstes Setup, völlig ausreichend für V1   | ✓        |
| Redis    | Mit Redis — Bereitet Multi-Node-Skalierung vor, erhöht aber Komplexität |          |
| Andere   | Andere                                                                  |          |

**User's choice:** standard
**Notes:**

---

## Reverse Proxy

| Option  | Description                                                       | Selected |
| ------- | ----------------------------------------------------------------- | -------- |
| Caddy   | Caddy — Automatische SSL-Zertifikate, einfache Caddyfile          |          |
| Traefik | Traefik — Sehr mächtig, erfordert aber mehr Konfigurationsaufwand |          |
| Andere  | Andere                                                            | ✓        |

**User's choice:** LiveKit empfiehlt für Media-Traffic direkte Host-Anbindung. Erstelle die docker-compose.yml so, dass LiveKit die UDP-Ports direkt nach außen öffnet. Für das HTTPS-Signaling nutzen wir Caddy als Standard-Proxy im Stack, dokumentieren aber in der .env, wie Coolify-Nutzer ihren globalen Traefik-Proxy stattdessen direkt anbinden können.
**Notes:**

---

## TURN-Server

| Option   | Description                                                       | Selected |
| -------- | ----------------------------------------------------------------- | -------- |
| Internal | Integrierter LiveKit TURN — Kein extra Container, einfache Config | ✓        |
| Coturn   | Externer Coturn — Extra Service, aber mehr Kontrolle              |          |
| Andere   | Andere                                                            |          |

**User's choice:** internal
**Notes:**

---

## Environment Variables

| Option  | Description                                      | Selected |
| ------- | ------------------------------------------------ | -------- |
| Central | Zentrale .env — Eine Datei für alles             |          |
| Split   | Aufgeteilt — Z.B. .env.livekit, .env.agent, etc. |          |
| Andere  | Andere                                           | ✓        |

**User's choice:** Zentrale Struktur, aber da wir coolify nutzen, muss sie über die coolify-variablen-maske anpassbar sein (und nicht hardcoded in einer datei im repo).
**Notes:**

---

## Arbeitsweise & Regeln

**User's choice:** Die Planung ist abgeschlossen. Bevor wir in die Umsetzung von Phase 1 gehen, schreibe bitte folgende verbindliche Arbeitsweise in das Projektwissen (z.B. in die PROJECT.md oder die Cursor-Rules):Primäre Datenquelle: Cursor ist angewiesen, für alle technischen Recherchen und Implementierungsschritte bezüglich LiveKit (Server-Setup, Agent-Worker, Frontend-Hooks) vorrangig das angebundene LiveKit-Dokumentations-MCP zu nutzen.Dies stellt sicher, dass wir stets die aktuellsten Best Practices für WebRTC, Token-Handling und die Realtime-API verwenden. Manuelle Suchen oder allgemeine LLM-Kenntnisse dienen nur als Sekundärquelle, falls das MCP keine spezifische Antwort liefert.
**Notes:** Rule is added to PROJECT.md.
