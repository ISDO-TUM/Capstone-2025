# Capstone Frontend (React + TypeScript + Vite)

Full rewrite of the Capstone UI using React 19, TypeScript, Vite 7, Tailwind, and (soon) shadcn/ui. Keep this README up to date so backend teammates know how to run, lint, and ship the app.

---

## Stack
- React 19 with the new compiler-ready JSX runtime
- TypeScript strict mode (see `tsconfig.app.json`)
- Vite 7 for dev server + build
- TailwindCSS 3 with PostCSS + autoprefixer
- ESLint flat config with TypeScript + React Hooks/Refresh plugins
- Placeholder UI copy; replace with real screens before release

## Requirements
- Node 20.18 LTS (use `nvm use 20` or Volta)
- pnpm or npm (repo currently uses npm + lockfile)
- Recommended IDE setup: VS Code + `dbaeumer.vscode-eslint` + `csstools.postcss`

## Getting Started
```bash
cd frontend
npm install            # once
npm run dev            # http://localhost:5173
```

### Useful Scripts
- `npm run dev` – hot reload dev server
- `npm run lint` – ESLint (fails on unused code, type issues)
- `npm run build` – type-check + production bundle
- `npm run preview` – serve the built bundle locally

## Integrating with the Backend
1. Backend lives in the repo root (`app.py`, `templates`, etc.). Until APIs are ready, stub data inside React components or create msw handlers.
2. When APIs are exposed, configure base URLs via environment variables. Vite reads variables prefixed with `VITE_` from `.env`, e.g. `VITE_API_BASE_URL=https://api.example.com`.
3. Share a generated TypeScript client (OpenAPI/Orval) to avoid mismatched contracts.
4. For auth/session context provided by the backend templates, expose REST endpoints or migrate to a dedicated auth provider; React SPA will not read server-rendered templates.

## Styling + shadcn Plan
- Tailwind is already wired via `postcss.config.js` and `tailwind.config.js`.
- Once ready for shadcn/ui, run `npx shadcn-ui@latest init` and commit the generated config + components under `frontend/src/components/ui`.
- Prefer CSS variables in `src/index.css` for theme tokens the backend may eventually share.

## CI / Quality Checks
Run these before pushing to shared branches:
```bash
npm run lint
npm run build
```
Add Vitest and Playwright once real components exist so we can guard regressions.

## Repo Hygiene
- Keep this README updated (new scripts, env vars, component libraries).
- When backend contracts change, document the required environment variables and expected responses here.
- Commit lockfiles (`package-lock.json`) so teammates stay in sync.
