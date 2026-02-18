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
