# Enhancement prompt — implement the 9 Figma screens

Copy everything below the line into a new Claude Code session opened at the repo root.

---

## Task

Bring the AML Transaction Monitoring frontend (`frontend/`, React 18 + Vite + Carbon `@carbon/react`) in line with the Figma file **IBM Product Workbench • AML Transaction Monitoring** (file key `8WiAIC5CZImmcupWWXfj0V`). Build the 9 screens below to match the design, and add the backend list/read endpoints they need (`backend/`, FastAPI + SQLAlchemy).

| # | Screen | Figma frame node | Route | Current state in code |
|---|--------|------------------|-------|------------------------|
| 1 | Dashboard — Screen | `7-8571` | `/dashboard` | Inline placeholder `DashboardPage` in `src/App.tsx` |
| 2 | Alerts — List | `7-8572` | `/alerts` | Placeholder `src/features/alerts/AlertListPage.tsx` |
| 3 | Alerts — Detail | `7-8573` | `/alerts/:alertId` | Built: `src/features/alerts/AlertDetailPage.tsx` (restyle it to match) |
| 4 | Transactions — List | `7-8576` | `/transactions` | Doesn't exist. `/transactions` currently renders `TransactionSubmitPage` |
| 5 | Transactions — Detail | `7-8577` | `/transactions/:id` | Built: `src/features/transactions/TransactionDetailPage.tsx` (restyle it to match) |
| 6 | Cases — List | `7-8574` | `/cases` | Placeholder `src/features/cases/CaseListPage.tsx` |
| 7 | Cases — Investigation | `7-8575` | `/cases/:id` | Built: `src/features/cases/CaseWorkspacePage.tsx` (restyle it to match) |
| 8 | Rules — Detection rules | `7-8578` | `/rules` | Placeholder `src/features/rules/RulesPage.tsx` |
| 9 | Rules — Administration | `7-8579` | `/admin` | Placeholder `src/features/admin/AdminPage.tsx` |

Section pages, for context: Dashboard `4-4421`, Alerts `4-4422`, Transactions `4-4423`, Cases `4-4424`, Rules & Admin `4-4425`.

## Step 0: Pull the design before you write any code

1. Load the `figma:figma-design-to-code` skill. For each frame node above, get the design context, export a screenshot, and record the colours and typography it uses. If the Figma MCP returns `403 Token expired`, stop and ask me to refresh the Figma token. Don't guess the layouts.
2. Write `docs/figma-screen-specs.md` with one section per frame: layout regions, every component (Carbon equivalent), table columns, filters, KPI tiles, charts, empty/loading/error states, and every data field shown. Map each field to an existing backend schema field, or mark it **MISSING**.
3. Show me the MISSING list and the proposed new endpoints, then wait for my OK before you start Step 1.

## Step 1: Backend endpoints (only what the screens need)

These exist today: `POST /api/v1/transactions`, `GET /api/v1/transactions/{id}`, `GET /api/v1/alerts/{id}`, `POST/GET /api/v1/cases[/{id}]` plus assign/decision/notes/request-info, `GET /api/v1/audit`, `GET /api/v1/customers/{id}`, `POST /api/auth/v1/auth/login`. `app/rules/router.py` is an empty placeholder and isn't mounted in `app/main.py`.

Add these, following the existing `router → service → repository` pattern and returning `app/common/pagination.PaginatedResponse`:
- `GET /api/v1/alerts`: paginated, filters for status, priority, assignee, and date range; sortable.
- `GET /api/v1/cases`: paginated, filters for state, priority, and assignee.
- `GET /api/v1/transactions`: paginated, filters for type, outcome, amount range, and date range.
- `GET /api/v1/rules` (+ `GET /api/v1/rules/{code}` and the version history the design shows). Mount the rules router.
- `GET /api/v1/dashboard/summary`: KPI counts and chart series, exactly as the Dashboard frame shows them.
- Admin: whatever the Administration frame shows (for example users/roles, rule thresholds), with access restricted to `ADMINISTRATOR`.

Enforce roles with the existing `app/security/dependencies.py`, and write audit events for any mutation. Add pytest coverage in `backend/tests` for every new endpoint (happy path, filters, pagination, and 403 for the wrong role).

## Step 2: Frontend screens

- Use Carbon components and tokens only (`DataTable`, `Pagination`, `Tile`, `Tag`, `Breadcrumb`, `Tabs`, `@carbon/charts-react` for the dashboard charts). Reuse what's already there: `components/status/*` tags, `RiskScoreMeter`, `AlertSummary`, `TransactionSummary`, `CustomerSnapshot`, `AuditTimeline`, the `components/rules/*` parts, and the helpers in `lib/utils.ts`. Replace the inline `style={{…}}` placeholders with SCSS or Carbon classes.
- Add API modules next to `lib/alert-api.ts` and `lib/transaction-api.ts` (`case-api.ts`, `rules-api.ts`, `dashboard-api.ts`, `admin-api.ts`) on top of `lib/api-client.ts`, and add types to `src/types/`.
- Routing: `/transactions` becomes the list. Move submission to `/transactions/new` and reach it from a primary button on the list, unless the Figma frame puts submission somewhere else. Fix the `Sidebar` active state so detail routes (for example `/alerts/12`) highlight their section, and add icons if the design has them. Move `DashboardPage` out of `App.tsx` into `src/features/dashboard/`.
- Every list row links to its detail page, and detail breadcrumbs link back to the list. Keep the current role filtering in `Sidebar.tsx` and the permission logic in `lib/decision-actions.ts`.
- Every screen needs loading (skeleton), empty, and error states.

## Step 3: Verify

1. Run `anthropic-skills:figma-design-accuracy` for each of the 9 frames, and fix discrepancies until they match.
2. Run `npm test`, `npm run lint`, and `npm run build` in `frontend/`, plus `pytest` in `backend/`. All must pass.
3. Update the existing Playwright specs in `frontend/e2e/` that break because of the `/transactions` route change. Add one smoke spec per new list page.
4. Run `mcp__wim-a11y-mcp__audit_directory` on `frontend/src/features` and fix any critical or serious issues.

## Constraints

- Don't touch `frontend/package-lock.json` unless you add a dependency. Don't add UI libraries beyond Carbon.
- Commit each screen (frontend plus its endpoint) separately, so each one is reviewable on its own.
- Ask me rather than invent any field, filter, or chart that the Figma frame doesn't show.
