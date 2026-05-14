# shadcn/ui monorepo template

This is a Next.js monorepo template with shadcn/ui.

## Environment variables

These are used when the app talks to the FastAPI backend (see repo root `infrastructure/.env.example`).

| Variable | Where | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Browser and server (inlined at build for client bundles) | Public URL of the API as seen from the **host machine** (e.g. `http://localhost:8000` in dev, `http://localhost:8800` in prod Compose). |
| `API_URL_INTERNAL` | Server-only (Next.js server components, route handlers) | Base URL for the API **inside Docker** (e.g. `http://backend:8000`). Do not use for client-only code. |

Root **`Makefile`** and **`infrastructure/docker-compose.*.yml`** set sensible defaults for the `web` service; copy or extend them in your `.env` under `infrastructure/`.

## Adding components

To add components to your app, run the following command at the root of your `web` app:

```bash
pnpm dlx shadcn@latest add button -c apps/web
```

This will place the ui components in the `packages/ui/src/components` directory.

## Using components

To use the components in your app, import them from the `ui` package.

```tsx
import { Button } from "@workspace/ui/components/button";
```
