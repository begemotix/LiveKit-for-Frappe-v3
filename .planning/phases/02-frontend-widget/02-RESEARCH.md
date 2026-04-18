# Phase 2: Frontend Widget - Research

**Researched:** 2026-04-18
**Domain:** Next.js Frontend Development / WebRTC / LiveKit SDK
**Confidence:** HIGH

## Summary

Phase 2 konzentriert sich auf die Implementierung eines Next.js-basierten Widgets, das als Floating Action Button (FAB) in Webseiten eingebettet werden kann. Es ermöglicht Gast-Nutzern eine nahtlose Sprach- und Text-Interaktion mit dem LiveKit-Server. Die Architektur folgt einem sicheren Token-Handshake-Modell, bei dem das Frontend über eine serverseitige API-Route Zugriffstoken anfordert, ohne sensible API-Secrets preiszugeben.

**Primary recommendation:** Nutze das offizielle `@livekit/components-react` SDK für die Room-Logik und die `AgentAudioVisualizerWave`-Komponente für eine moderne Voice-UI. Implementiere das White-Labeling strikt über CSS-Variablen, die aus `NEXT_PUBLIC_` Umgebungsvariablen gespeist werden.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Start-Zustand: Eingeklappt als FAB-Icon unten rechts.
- **D-02:** Panel-Verhalten: Öffnet sich bei Klick als Chat/Voice-Interface.
- **D-03:** Hybrid-Mode: Unterstützung von Text-Historie (Transkription) parallel zu Voice-Interaktion (Waveforms).
- **D-04:** Status-Indikatoren: Visuelle Rückmeldung über Verbindungsstatus und Agenten-Aktivität.
- **D-05:** Dynamic Styling: CSS-Variablen (Primärfarbe, Hintergründe) werden direkt aus `.env` (z.B. `WIDGET_PRIMARY_COLOR`) gespeist.
- **D-06:** Server-side Token: Absolutes Verbot von Client-side Token-Generierung. Implementierung einer Next.js API-Route.
- **D-07:** Gast-Zugang: Generierung eines Tokens für einen anonymen Gast-User.
- **D-08:** Initialer Connect: Expliziter "Start/Connect"-Knopf im geöffneten Widget (für Browser-Audio-Context & Mic-Permissions).
- **D-09:** Voice-First: Nach Verbindungsaufbau startet direkt der VAD (Voice Activity Detection) Modus.

### Claude's Discretion

- Auswahl der spezifischen LiveKit-Komponenten für Visualisierung.
- Struktur der API-Route und Token-TTL.
- UI-Framework-Wahl innerhalb von Next.js (z.B. Tailwind CSS für Layout).

### Deferred Ideas (OUT OF SCOPE)

- None.
  </user_constraints>

<phase_requirements>

## Phase Requirements

| ID      | Description                                                                    | Research Support                                                                         |
| ------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| WIDG-01 | Next.js-basiertes Voice/Text-Widget als Floating Button bereitstellen          | FAB-Layout mit React-Portals oder CSS Fixed Positioning; Nutzung von Next.js App Router. |
| WIDG-02 | Button ermöglicht Verbindungsaufbau (WebRTC) zum lokalen LiveKit Server        | Integration des `LiveKitRoom` Providers und `useToken` Hooks zum `livekit-client`.       |
| WIDG-03 | Widget generiert einen unauthentifizierten Gast-Token, um dem Raum beizutreten | Serverseitige Token-Generierung mit `livekit-server-sdk` und `AccessToken` Klasse.       |

</phase_requirements>

## Standard Stack

### Core

| Library                     | Version | Purpose                    | Why Standard                                             |
| --------------------------- | ------- | -------------------------- | -------------------------------------------------------- |
| `livekit-client`            | 2.18.3  | Core WebRTC Logik          | Offizielles SDK für Browser-Verbindungen.                |
| `@livekit/components-react` | 2.9.20  | UI-Komponenten & Hooks     | Beschleunigt Entwicklung durch vorgefertigte Room-Logik. |
| `livekit-server-sdk`        | 2.15.1  | Token-Generierung (Server) | Sicherer Weg zur Erstellung von JWT-Tokens.              |
| `Next.js`                   | 14/15+  | Application Framework      | Standard für moderne React-Apps mit API-Routes.          |

### Supporting

| Library                      | Version | Purpose             | When to Use                               |
| ---------------------------- | ------- | ------------------- | ----------------------------------------- |
| `@livekit/components-styles` | 1.2.0   | Standard CSS-Styles | Basis-Theming für LiveKit Komponenten.    |
| `lucide-react`               | Latest  | Iconography         | FAB-Icon und UI-Symbole.                  |
| `clsx` / `tailwind-merge`    | Latest  | CSS Utility         | Dynamisches Styling basierend auf States. |

### Alternatives Considered

| Instead of      | Could Use     | Tradeoff                                                            |
| --------------- | ------------- | ------------------------------------------------------------------- |
| `livekit-react` | Custom WebRTC | Extrem hoher Aufwand für State-Management (Muting, Visualisierung). |
| Global CSS      | CSS Variables | CSS-Variablen ermöglichen echtes Runtime-Theming ohne Rebuild.      |

**Installation:**

```bash
npm install livekit-client livekit-server-sdk @livekit/components-react @livekit/components-styles lucide-react
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── app/
│   ├── api/
│   │   └── token/
│   │       └── route.ts     # Token Generation Endpoint
│   ├── layout.tsx
│   └── page.tsx             # Widget Test/Demo Page
├── components/
│   ├── widget/
│   │   ├── FloatingButton.tsx
│   │   ├── ChatPanel.tsx
│   │   ├── VoiceVisualizer.tsx
│   │   └── index.tsx        # Widget Entry Point
│   └── LiveKitProvider.tsx  # Wrapper for Room Context
└── styles/
    └── widget.css           # Custom CSS for the Widget
```

### Pattern 1: Secure Token Handshake

Das Frontend speichert keine Secrets. Es sendet eine POST-Anfrage an `/api/token`, der Server validiert die Anfrage (z.B. Host-Check) und gibt ein signiertes JWT zurück.

### Anti-Patterns to Avoid

- **Client-side API Secrets:** `LIVEKIT_API_SECRET` niemals im Frontend verwenden.
- **Auto-Play Audio:** Browser blockieren Audio ohne Interaktion. Die Verbindung muss durch einen Klick ("D-08") gestartet werden.

## Don't Hand-Roll

| Problem             | Don't Build            | Use Instead                | Why                                                      |
| ------------------- | ---------------------- | -------------------------- | -------------------------------------------------------- |
| Voice Visualization | Custom Canvas Shader   | `AgentAudioVisualizerWave` | Hochperformante, shader-basierte Waveforms.              |
| Room State Mgmt     | Redux/Context Provider | `LiveKitRoom`              | Behandelt Reconnects, Muting und Track-Sync automatisch. |
| JWT Signing         | Custom Crypto          | `AccessToken` SDK          | Verhindert Formatfehler und Sicherheitslücken.           |

## Common Pitfalls

### Pitfall 1: Audio Context Locked

**What goes wrong:** Der Agent spricht, aber der Nutzer hört nichts.
**Why it happens:** Der Browser erlaubt keinen Audio-Output ohne "User Gesture".
**How to avoid:** Ein expliziter "Start"-Button im Widget setzt den Audio-Context frei.

### Pitfall 2: Environment Variable Naming

**What goes wrong:** Farben oder URLs sind im Frontend `undefined`.
**Why it happens:** Next.js exponiert Variablen nur, wenn sie mit `NEXT_PUBLIC_` beginnen.
**How to avoid:** Nutze `NEXT_PUBLIC_WIDGET_PRIMARY_COLOR` etc.

## Code Examples

### Server-side Token Generation (`/api/token/route.ts`)

```typescript
// Source: https://docs.livekit.io/server-sdk-js/classes/AccessToken.html
import { NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';

export async function POST(req: Request) {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const roomName = process.env.LIVEKIT_DEFAULT_ROOM || 'lobby';

  const at = new AccessToken(apiKey, apiSecret, {
    identity: `guest-${Math.random().toString(36).substring(7)}`,
  });

  at.addGrant({
    roomJoin: true,
    room: roomName,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  });

  return NextResponse.json({ token: await at.toJwt() });
}
```

### Dynamic Styling Wrapper

```tsx
const WidgetWrapper = ({ children }) => {
  const style = {
    '--primary-color': process.env.NEXT_PUBLIC_WIDGET_PRIMARY_COLOR || '#3b82f6',
    '--bg-color': process.env.NEXT_PUBLIC_WIDGET_BG_COLOR || '#ffffff',
  } as React.CSSProperties;

  return (
    <div style={style} className="widget-root">
      {children}
    </div>
  );
};
```

## Environment Availability

| Dependency         | Required By       | Available | Version        | Fallback           |
| ------------------ | ----------------- | --------- | -------------- | ------------------ |
| Node.js            | Next.js Server    | ✓         | v20+           | —                  |
| LiveKit Server     | WebRTC Connection | ✓         | v1.x (Phase 1) | —                  |
| Browser Mic Access | Voice Interaction | ✓         | N/A            | Text-only fallback |

## Validation Architecture

### Test Framework

| Property          | Value                          |
| ----------------- | ------------------------------ |
| Framework         | Vitest + React Testing Library |
| Config file       | `vitest.config.ts`             |
| Quick run command | `npm test`                     |

### Phase Requirements → Test Map

| Req ID  | Behavior                      | Test Type   | Automated Command                | File Exists? |
| ------- | ----------------------------- | ----------- | -------------------------------- | ------------ |
| WIDG-01 | FAB ist sichtbar und klickbar | Component   | `vitest FloatingButton.test.tsx` | ❌ Wave 0    |
| WIDG-02 | Verbindung wird aufgebaut     | Integration | `vitest Connection.test.tsx`     | ❌ Wave 0    |
| WIDG-03 | API gibt gültiges JWT zurück  | API         | `vitest api/token.test.ts`       | ❌ Wave 0    |

## Sources

### Primary (HIGH confidence)

- `livekit-client` Documentation
- `livekit-server-sdk` Documentation
- `@livekit/components-react` Reference

### Secondary (MEDIUM confidence)

- Next.js Environment Variables Guide
- WebRTC Audio Context MDN Docs

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - Offizielle LiveKit SDKs verwendet.
- Architecture: HIGH - Bewährtes Token-Modell für Gast-Zugang.
- Pitfalls: MEDIUM - Browser-Audio-Constraints sind variabel, aber bekannt.

**Research date:** 2026-04-18
**Valid until:** 2026-05-18
