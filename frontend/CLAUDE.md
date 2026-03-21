# Frontend — Luxis

## Stack

Next.js 15 (App Router, React 19) + shadcn/ui + Tailwind CSS + TanStack Query.

## Routing

- `(dashboard)/` — authenticated layout with sidebar
- `(dashboard)/page.tsx` — dashboard
- `(dashboard)/relaties/` — contacts CRUD
- `(dashboard)/zaken/` — cases CRUD
- `login/page.tsx` — login page (public)

## Patterns

- API calls via `@/lib/api.ts` (Axios instance with JWT interceptor)
- Custom hooks in `@/hooks/` for data fetching (TanStack Query)
- shadcn/ui components in `@/components/ui/` — do NOT edit manually, use `npx shadcn@latest add`
- All custom components in `@/components/`
- All UI text in **Nederlands**

## Design System

- Modern, data-dense, professional (Gmail/HubSpot-stijl)
- Sidebar with collapse (HubSpot-stijl)
- Skeleton loaders for loading states
- Toast notifications for success/error
- Status badges with color coding per case status
- Tables: sortable, filterable, with pagination

## State Management

- Server state: TanStack Query (useQuery, useMutation)
- Auth state: custom `useAuth` hook with localStorage tokens
- No global state library needed (yet)

## TypeScript Rules

- **Nooit `|| undefined` wijzigen naar `|| null`** — semantisch verschillend in TypeScript. Optional fields moeten `undefined` blijven, niet `null`.
- **Altijd build verificatie na TypeScript wijzigingen:** draai `npx tsc --noEmit` voordat je commit. Dit vangt type-errors die anders pas bij deploy/PR opvallen.
- Bij twijfel over `null` vs `undefined`: check het Pydantic schema (backend) en het TypeScript interface — ze moeten matchen.

## E2E Testing (Playwright)

- Config: `frontend/playwright.config.ts` — 3-project setup (setup → auth → chromium)
- Auth: storageState pattern — login in `auth.setup.ts`, reuse via `e2e/.auth/user.json`
- Helpers: `frontend/e2e/helpers/` — `auth.ts` (login, token injection), `api.ts` (seed/cleanup via backend API)
- **`force: true` on clicks** — Next.js dev overlay `<nextjs-portal>` blocks click events
- **`getByPlaceholder()`** for forms without `htmlFor`/`id` attributes
- **Regex for `waitForURL`** — `waitForURL(/\/relaties\/[a-f0-9-]+$/)` not `waitForURL("**/relaties/**")`
- **Sequential execution** — `workers: 1`, `fullyParallel: false` for test interdependency
- **Cleanup in `afterAll`** — delete test data via API helpers to avoid pollution
