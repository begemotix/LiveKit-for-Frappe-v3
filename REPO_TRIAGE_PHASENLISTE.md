# REPO TRIAGE PHASENLISTE

Nur Analyse. Keine Repo-Änderungen außer dieser Datei.

## Aufgabe 1 — Positiv-Liste pro Phase

## Phase 01 (`.planning/phases/01-infrastructure-setup/`)

### Explizit erstellte Dateien
- `.env.example` (01-01-PLAN `files_modified`, Task 1 `<files>`, sowie 01-01-SUMMARY `added`)
- `livekit.yaml` (01-01-PLAN `files_modified`, Task 2 `<files>`, sowie 01-01-SUMMARY `added`)
- `Caddyfile` (01-02-PLAN `files_modified`, Task 1 `<files>`, sowie 01-02-SUMMARY `added`)
- `docker-compose.yml` (01-02-PLAN `files_modified`, Task 2 `<files>`, sowie 01-02-SUMMARY `added`)
- `README.md` (01-02-PLAN `files_modified`, Task 3 `<files>`, sowie 01-02-SUMMARY `added`)

### Explizit modifizierte Dateien
- `.env.example`
- `livekit.yaml`
- `Caddyfile`
- `docker-compose.yml`
- `README.md`

### Template-Klone
- Keine Clone-Instruction in Phase 01.

---

## Phase 02 (`.planning/phases/02-frontend-widget/`)

### Explizit erstellte Dateien
- `tests/widget.test.tsx` (02-01-PLAN Task 0/Task 3)
- `tests/api-token.test.ts` (02-01-PLAN Task 0/Task 3)
- `vitest.config.ts` (02-01-PLAN Task 3)
- `app/api/token/route.ts` (02-02-PLAN `files_modified`, Task 1; 02-02-SUMMARY `created`)
- `components/LiveKitProvider.tsx` (02-02-PLAN `files_modified`, Task 2; 02-02-SUMMARY `created`)
- `components/widget/FloatingButton.tsx` (02-03-PLAN `files_modified`, Task 1; 02-03-SUMMARY `created`)
- `components/widget/ChatPanel.tsx` (02-03-PLAN `files_modified`, Task 2; 02-03-SUMMARY `created`)
- `components/widget/index.tsx` (02-03-PLAN `files_modified`, Task 3; 02-03-SUMMARY `created`)
- `components/widget/VoiceVisualizer.tsx` (02-04-PLAN Task 1; 02-04-SUMMARY Key Changes)
- `.planning/phases/02-frontend-widget/02-VERIFICATION.md` (02-05-PLAN Task 2)

### Explizit modifizierte Dateien
- `package.json` (02-01-PLAN `files_modified`)
- `tsconfig.json` (02-01-PLAN `files_modified`)
- `next.config.mjs` (02-01-PLAN `files_modified`)
- `components.json` (02-01-PLAN `files_modified`)
- `tailwind.config.ts` (02-01-PLAN `files_modified`)
- `app/layout.tsx` (02-01-PLAN `files_modified`)
- `app/page.tsx` (02-01-PLAN `files_modified`; 02-03-SUMMARY nennt `app/(app)/page.tsx` als tatsächlich geändert)
- `app/globals.css` (02-01-PLAN `files_modified`)
- `components/widget/ChatPanel.tsx` (02-04-PLAN `files_modified`)
- `components/widget/VoiceVisualizer.tsx` (02-04-PLAN `files_modified`)
- `app/globals.css` (02-05-PLAN `files_modified`)
- `app/layout.tsx` (02-05-PLAN `files_modified`)
- `tailwind.config.ts` (02-05-PLAN `files_modified`)
- `components/root-layout.tsx` (02-06-PLAN `files_modified`)
- `layout.tsx` (02-06-PLAN `files_modified`, Task 2 delete cleanup)

### Template-Klone
- `https://github.com/livekit-examples/agent-starter-embed.git` -> **Zielpfad laut 02-01-PLAN: `.` (Repo-Root)** (Task 1, `git clone ... .`).

---

## Phase 03 (`.planning/phases/03-agent-core/`)

### Explizit erstellte Dateien
- `apps/agent/tests/test_agent.py` (03-00-PLAN Task 2)
- `apps/agent/requirements.txt` (03-01-PLAN `files_modified`)
- `apps/agent/.env.example` (03-01-PLAN `files_modified`)
- `apps/agent/agent.py` (03-01-PLAN `files_modified`)
- `apps/agent/WHITE_LABELING.md` (03-03-PLAN `files_modified`, Task 2)
- `apps/agent/conftest.py` (03-CP-PLAN Task 2)

### Explizit modifizierte Dateien
- `apps/agent/tests/test_agent.py` (03-00/03-03/03-CP)
- `apps/agent/requirements.txt` (03-01)
- `apps/agent/.env.example` (03-01)
- `apps/agent/agent.py` (03-01/03-02/03-CP)
- `apps/agent/WHITE_LABELING.md` (03-03)
- `.planning/STATE.md` (03-CP)
- `.planning/ROADMAP.md` (03-CP)
- `.planning/phases/03-agent-core/03-00-SUMMARY.md` (03-CP)
- `.planning/phases/03-agent-core/03-01-SUMMARY.md` (03-CP)

### Template-Klone
- `https://github.com/livekit-examples/agent-starter-python` -> **Zielpfad laut 03-01-PLAN: `apps/agent`** (Task 1).

---

## Aufgabe 2 — Abgleich mit Repo-Realität (Root-Einträge)

Scope: alle Root-Einträge außer `.git`, `.cursor`, `.planning`, `infrastructure/`, `.gitignore` (wie vorgegeben).

### GEPLANT

Begründung: In Phase-Dokumenten explizit genannt **oder** durch 02-01-Template-Klon nach `.` (Repo-Root) abgedeckt.

- `apps` (03-01-PLAN Template-Klonziel `apps/agent`)
- `.env.example` (01-01-PLAN)
- `Caddyfile` (01-02-PLAN)
- `docker-compose.yml` (01-02-PLAN)
- `livekit.yaml` (01-01-PLAN)
- `README.md` (01-02-PLAN)
- `app`, `components`, `tests` (02-PLANs explizite Pfade unter diesen Ordnern)
- `package.json`, `tsconfig.json`, `components.json`, `vitest.config.ts` (02-01-PLAN)
- `action-bar.tsx`, `agent-client.tsx`, `app-config.ts`, `app-icon.png`, `audio-visualizer.tsx`, `build-and-test.yaml`, `button.tsx`, `chat-entry.tsx`, `chat-input.tsx`, `CommitMono-400-Italic.otf`, `CommitMono-400-Regular.otf`, `CommitMono-700-Italic.otf`, `CommitMono-700-Regular.otf`, `device-select.tsx`, `env.ts`, `error-message.tsx`, `eslint.config.mjs`, `favicon.ico`, `file.svg`, `globals.css`, `globe.svg`, `LICENSE`, `lk-logo-dark.svg`, `lk-logo.svg`, `microphone-toggle.tsx`, `next-env.d.ts`, `next.config.ts`, `next.svg`, `package-lock.json`, `page.tsx`, `popup-page-dynamic.tsx`, `popup-page.tsx`, `popup-view.tsx`, `postcss.config.mjs`, `readme-hero-dark.webp`, `readme-hero-light.webp`, `renovate.json`, `root-layout.tsx`, `route.ts`, `screenshot-dark.webp`, `screenshot-light.webp`, `select.tsx`, `session-view.tsx`, `standalone-bundle-root.tsx`, `styles.css`, `styles.d.ts`, `styles.ts`, `sync-to-production.yaml`, `taskfile.yaml`, `template-graphic.svg`, `TEMPLATE.md`, `theme-provider.tsx`, `theme-toggle.tsx`, `toggle.tsx`, `track-toggle.tsx`, `transcript.tsx`, `trigger.tsx`, `tsconfig.webpack.json`, `types.ts`, `use-agent-control-bar.ts`, `use-chat-and-transcription.ts`, `use-connection-details.ts`, `use-publish-permissions.ts`, `useDebug.ts`, `useDelayedValue.ts`, `utils.ts`, `vercel.svg`, `webpack.config.js`, `welcome-dynamic.tsx`, `welcome-view.tsx`, `welcome.tsx`, `window.svg`, `.github`, `(app)`, `(iframe)`, `api`, `assets`, `chat`, `connection-details`, `embed`, `embed-iframe`, `embed-popup`, `fonts`, `lib`, `livekit`, `popup`, `public`, `styles`, `test`, `workflows`
  - Referenz für diesen Block: 02-01-PLAN Task 1 (`git clone ... .`) + 02-01/02-02/02-03/02-04/02-05/02-06-SUMMARY.

### UNGEPLANT

Begründung: Kein Phasenplan nennt diese Root-Pfade als Projektartefakte; es sind Git-Interndaten/Build-Cruft/Debug-Outputs.

- `.next`
- `.pytest_cache`
- `node_modules`
- `advisor_out.txt`
- `init_out.txt`
- `heads`
- `hooks`
- `info`
- `logs`
- `objects`
- `origin`
- `pack`
- `refs`
- `remotes`
- `tags`
- `applypatch-msg.sample`
- `commit-msg.sample`
- `config`
- `description`
- `exclude`
- `fsmonitor-watchman.sample`
- `HEAD`
- `index`
- `main`
- `pack-fe97193e4f09082fb52e466c709935d4caaefba6.idx`
- `pack-fe97193e4f09082fb52e466c709935d4caaefba6.pack`
- `pack-fe97193e4f09082fb52e466c709935d4caaefba6.rev`
- `packed-refs`
- `post-update.sample`
- `pre-applypatch.sample`
- `pre-commit.sample`
- `pre-merge-commit.sample`
- `pre-push.sample`
- `pre-rebase.sample`
- `pre-receive.sample`
- `prepare-commit-msg.sample`
- `push-to-checkout.sample`
- `sendemail-validate.sample`
- `update.sample`

### AMBIVALENT

- `.eslintrc.json` (Template-/Tooling-Datei, in 02-Plänen nicht explizit genannt; zugleich durch `clone ... .` implizit reinholbar)
- `.prettierignore` (dito)
- `.prettierrc` (dito)

---

## Aufgabe 3 — Meta-Auswertung

### Zählung (nach obiger Klassifikation)

- `GEPLANT`: **102**
- `UNGEPLANT`: **41**
- `AMBIVALENT`: **3**
- Gesamt im Scope: **146**

### Template-Klon-Instruktionen vs. Zielpfad-Einhaltung

- **Phase 02 (02-01-PLAN)**: Clone-Instruktion vorhanden (`agent-starter-embed`), Zielpfad laut Plan ist `.` (Repo-Root).  
  - Ergebnis gegenüber Plantext: **Zielpfad eingehalten** (Klon in Root).
- **Phase 03 (03-01-PLAN)**: Clone-Instruktion vorhanden (`agent-starter-python`), Zielpfad `apps/agent`.  
  - Ergebnis gegenüber Plantext: **Zielpfad eingehalten**.

**Festgestellter struktureller Kern laut Plantext:**  
Die 02-01-Clone-Instruktion selbst zielt auf den Repo-Root (`.`) und erzeugt damit die breite Root-Belegung direkt auf Planungsebene.
