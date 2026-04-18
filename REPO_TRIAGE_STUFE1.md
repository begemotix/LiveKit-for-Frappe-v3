# REPO TRIAGE STUFE 1

Stand: rein analytische Grobsortierung ohne Repo-Umbauten.

Referenz-Commit fuer Entpack-Unfall: `d9687d6` (`feat(02-01): clone agent-starter-embed template and install dependencies`).

## A) Offensichtlich behalten

- `.cursor`
- `.git`
- `.planning`
- `apps`
- `infrastructure`
- `.gitignore`

## B) Offensichtlicher Muell (Git-Interna im Root / Entpack-Artefakte)

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

## C) Template-Dateien aus Entpack-Unfall (Frontend/Widget im Root)

### C.1 Ordner

- `.github`
- `(app)`
- `(iframe)`
- `api`
- `app`
- `assets`
- `chat`
- `components`
- `connection-details`
- `embed`
- `embed-iframe`
- `embed-popup`
- `fonts`
- `lib`
- `livekit`
- `popup`
- `public`
- `styles`
- `test`
- `tests`
- `workflows`

### C.2 Dateien im Root

- `.env.example`
- `.eslintrc.json`
- `.prettierignore`
- `.prettierrc`
- `action-bar.tsx`
- `agent-client.tsx`
- `app-config.ts`
- `app-icon.png`
- `audio-visualizer.tsx`
- `build-and-test.yaml`
- `button.tsx`
- `chat-entry.tsx`
- `chat-input.tsx`
- `CommitMono-400-Italic.otf`
- `CommitMono-400-Regular.otf`
- `CommitMono-700-Italic.otf`
- `CommitMono-700-Regular.otf`
- `components.json`
- `device-select.tsx`
- `env.ts`
- `error-message.tsx`
- `eslint.config.mjs`
- `favicon.ico`
- `file.svg`
- `globals.css`
- `globe.svg`
- `LICENSE`
- `lk-logo-dark.svg`
- `lk-logo.svg`
- `microphone-toggle.tsx`
- `next-env.d.ts`
- `next.config.ts`
- `next.svg`
- `package-lock.json`
- `package.json`
- `page.tsx`
- `popup-page-dynamic.tsx`
- `popup-page.tsx`
- `popup-view.tsx`
- `postcss.config.mjs`
- `readme-hero-dark.webp`
- `readme-hero-light.webp`
- `README.md`
- `renovate.json`
- `root-layout.tsx`
- `route.ts`
- `screenshot-dark.webp`
- `screenshot-light.webp`
- `select.tsx`
- `session-view.tsx`
- `standalone-bundle-root.tsx`
- `styles.css`
- `styles.d.ts`
- `styles.ts`
- `sync-to-production.yaml`
- `taskfile.yaml`
- `template-graphic.svg`
- `TEMPLATE.md`
- `theme-provider.tsx`
- `theme-toggle.tsx`
- `toggle.tsx`
- `track-toggle.tsx`
- `transcript.tsx`
- `trigger.tsx`
- `tsconfig.json`
- `tsconfig.webpack.json`
- `types.ts`
- `use-agent-control-bar.ts`
- `use-chat-and-transcription.ts`
- `use-connection-details.ts`
- `use-publish-permissions.ts`
- `useDebug.ts`
- `useDelayedValue.ts`
- `utils.ts`
- `vercel.svg`
- `vitest.config.ts`
- `webpack.config.js`
- `welcome-dynamic.tsx`
- `welcome-view.tsx`
- `welcome.tsx`
- `window.svg`

### C.3 Historie je C-Ordner (git log --oneline -- <ordner>)

- `.github`: **spaeter modifiziert**  
  Commits: `b39ea1d, a17be87, fab6f47, ee78bfc, 707a76b, e308af8, 7517999, f195362, 28f9d10, 1603b91, 99f2d14, 42a9a89, 3d3088f, f598c6f, cfc1029, b1544a8, cb17c60, 7974b7d, b77f1f6, 970a30b, 28cddcc, 1781556, dc3baf2`
- `(app)`: **unveraendert seit Entpacken**
- `(iframe)`: **unveraendert seit Entpacken**
- `api`: **unveraendert seit Entpacken**
- `app`: **spaeter modifiziert**  
  Commits: `c272d4c, f20152d, 4c316a4, 88f4edf, 5e45b8d, a17be87, 2647b84, 4d7a989, 9df431b, e412670, ff04258, f284b8a, 204e3a1, c1197aa, d097904, 96b37e6, 930ddbf, e308af8, ef07bf2, 29a7ce3, 0a22e69, 90f90da, e4bdd5f, da92995, 0c5c816, 85cb45c, 497ab5a, 7894f00, f8accc6, 8c4ebc7, d8a0190, 4a0f1bb, 81f112a, a0b3d37, 3e0ce78, c361c16, bd132fa, 01d2b5b, 974e786, 74866d1, e246b6b, 8925bb0, 86946e5, bcbc79a, 3e7d084, 8cd6443, e4feaf4, e60e854, 0aceb3d, 95fda9f, 5d11a4e, 60fee5a, ed3ab38, cb7583e, 6c807d0, 8e891a4, 0587e2a`
- `assets`: **unveraendert seit Entpacken**
- `chat`: **unveraendert seit Entpacken**
- `components`: **spaeter modifiziert**  
  Commits: `c272d4c, a32089c, e753ca2, a11c29b, 47baff3, f20152d, 6abe82c, 3295bf6, 46220a5, 8280d64, f50deb0, 88f4edf, 4f7bc8c, a17be87, 2647b84, c524001, 07a69e9, 2191da8, 0a58c89, 0212c7a, 4d7a989, 9df431b, 3f2a3fc, e412670, ff04258, f284b8a, 204e3a1, c1197aa, 0cd38bb, d097904, c489aff, fc689ab, 2328c2f, a30759a, 6cbb64d, d4b01e7, bdb8aef, ee77eff, c71b154, 7828716, 96b37e6, db16bb7, 930ddbf, c0448f8, 90f90da, a171d49, c9f46e3, e4bdd5f, da92995, 0c5c816, 85cb45c, 790f33c, 497ab5a, 7894f00, 8c4ebc7, 1c3d6ab, d8a0190, 767a7c7, 4a0f1bb, 81f112a, 3e0ce78, c361c16, ad78cd5, 6cc774a, 2e415d1, bd132fa, 01d2b5b, 74866d1, e246b6b, 8925bb0, 86946e5, 710c96a, 3e7d084, 8cd6443, e4feaf4, e60e854, 79f8638, 0aceb3d, 95fda9f, 5d11a4e, ed3ab38, cb7583e, b01e99f, 6c807d0, 17fb428, 8e891a4`
- `connection-details`: **unveraendert seit Entpacken**
- `embed`: **unveraendert seit Entpacken**
- `embed-iframe`: **unveraendert seit Entpacken**
- `embed-popup`: **spaeter modifiziert**  
  Commits: `c272d4c`
- `fonts`: **spaeter modifiziert**  
  Commits: `ff04258`
- `lib`: **spaeter modifiziert**  
  Commits: `f50deb0, 88f4edf, 5e45b8d, 68b6fff, a17be87, 2647b84, d4b01e7, ee77eff, 7828716, e4bdd5f, 1c3d6ab, 4a0f1bb, 974e786, e246b6b, 0aceb3d, 60fee5a, ed3ab38, cb7583e, 8e891a4`
- `livekit`: **unveraendert seit Entpacken**
- `popup`: **unveraendert seit Entpacken**
- `public`: **spaeter modifiziert**  
  Commits: `204e3a1, c1197aa, e246b6b, bcbc79a, 0587e2a`
- `styles`: **spaeter modifiziert**  
  Commits: `a17be87, ff04258`
- `test`: **unveraendert seit Entpacken**
- `tests`: **spaeter modifiziert**  
  Commits: `c272d4c, 47baff3, 4c316a4, 521662c`
- `workflows`: **unveraendert seit Entpacken**

## D) Phase-1-Duplikate (Root, Originale unter infrastructure/)

- `docker-compose.yml`
- `Caddyfile`
- `livekit.yaml`

## E) Unklar

- `.next`
- `.pytest_cache`
- `node_modules`
- `advisor_out.txt`
- `init_out.txt`
