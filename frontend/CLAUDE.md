<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

Turbo monorepo with pnpm workspaces:

- `apps/web/` — Next.js 16 application (App Router, Turbopack)
- `packages/ui/` — Shared component library built on shadcn/ui + Base UI React
- `packages/eslint-config/` — Shared ESLint configurations
- `packages/typescript-config/` — Shared TypeScript base configs

## Commands

Run from repo root (orchestrated via Turbo):

```bash
pnpm dev        # Start all dev servers
pnpm build      # Build all packages
pnpm lint       # Lint all packages
pnpm format     # Prettier format all packages
pnpm typecheck  # TypeScript check all packages
```

Run from `apps/web/` for app-only work (faster):

```bash
pnpm dev        # next dev --turbopack
pnpm build      # next build
pnpm typecheck  # tsc --noEmit
```

## Architecture

**UI components** live in `packages/ui` and are imported as `@workspace/ui`. New shadcn/ui components should be added there, not in `apps/web`. The `next.config.mjs` transpiles this package.

**Styling** uses TailwindCSS 4 with CSS variables. The `cn()` utility (clsx + tailwind-merge) is the standard for conditional classNames. Component variants use `class-variance-authority` (CVA).

**App Router** is used in `apps/web/app/`. Layouts and pages follow Next.js 15+ conventions with React 19.

**RTL support** is enabled (`components.json` rtl: true) — the app targets Persian/Arabic-language users. Keep RTL compatibility in mind when adding layout or directional styles.

**Theme** is managed via `next-themes` with a `ThemeProvider` wrapping the app.

**Path aliases**: `@/*` maps to `apps/web/src/*`; `@workspace/*` maps to packages.
