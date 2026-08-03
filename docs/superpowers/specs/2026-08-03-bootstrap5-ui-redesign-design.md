# Bootstrap 5 UI Redesign — Phase 1 (Design System Foundation)

## Goal

Modernize the frontend visual design across the whole project (400+ Django
templates) and upgrade from Bootstrap 4.1.0 to Bootstrap 5.3.3, without
changing any business logic. This spec covers **Phase 1 only**: build the
shared design system (shell + reusable components) and prove it on a small
set of representative pages. Later phases (not covered here) roll the same
patterns out to the remaining templates module by module.

## Visual direction

Chosen from three mockups reviewed via local HTML prototypes
(`.superpowers/mockups/{a-stg-modern,b-command-dark,c-paper-light}.html`):

- **Base: Design A — "STG Modern"** — evolves the existing STG purple/indigo
  identity rather than replacing it. Sidebar with an indigo→deep-indigo
  gradient, active nav item rendered as a white pill, soft-shadow cards,
  rounded corners (14px), Prompt (headings) + Sarabun (body) fonts. The
  existing brand red (`#ED3237`) is kept as the notification/accent color.
- **Added element: KPI summary cards**, adapted from Design B ("Command
  Dark"), restyled to Design A's light palette — a row of stat cards at the
  top of relevant pages (see "KPI card data contract" below).

Design tokens (from the approved mockup, `a-stg-modern.html`):

| Token | Value |
|---|---|
| `--stg-ink` | `#23295e` |
| `--stg-indigo` | `#3d478f` |
| `--stg-indigo-deep` | `#2a3170` |
| `--stg-periwinkle` | `#7386d5` |
| `--stg-mist` | `#eef0fa` |
| `--stg-red` (existing brand red, kept) | `#ed3237` |
| `--stg-bg` | `#f4f5fa` |
| Card radius | `14px` |
| Headings | Prompt 500/600/700 |
| Body | Sarabun 400/500/600/700 |

## KPI card data contract

A new reusable partial (`stock/templates/partials/kpi_row.html`) renders a
row of stat cards. Two data sources, chosen per page — **no new backend
queries of material cost**:

1. **Workflow pages** (Request, Approve, Receive, home/dashboard-style
   pages): reuse the pending-count values already computed for the sidebar
   badges (e.g. `pc_all`, `ap_all`, `is_purchasing_pr`, `ma_all`,
   `add_po_all`, `all_pr_ap`, `all_cp_ap`, `all_po_ap` — see
   `stock/templates/sidebar.html`). No new queries; just surfaced in a
   second place.
2. **List/report pages** (Express, Report, and similar filtered-list
   views): show "records in current filter" + "total amount," computed
   from the already-paginated/filtered queryset the page already builds.
   If a view doesn't currently compute a filtered sum, adding a single
   `.aggregate(Sum(...))` call is acceptable; this is the only backend
   touch allowed in Phase 1, and only when the page already has the
   relevant queryset in hand.

Pages with no natural summary data do **not** get a KPI row — it is not
mandatory everywhere.

## Technical migration approach

| Area | Decision |
|---|---|
| Bootstrap | 4.1.0 CDN → 5.3.3 CDN, single `bootstrap.bundle.min.js` (ships Popper v2 — drop the separate Popper 1.14 CDN `<script>` tag) |
| jQuery | **Kept.** `layouts.html`/`navbar.html` custom scripts (company-switch AJAX, sidebar collapse toggle, scroll-based navbar color, favicon badge canvas, tab-width resize logic) stay as-is. Bootstrap 5's own JS does not require jQuery, so there's no conflict keeping it loaded for app code. |
| Forms | `CRISPY_TEMPLATE_PACK` in `djangostock/settings.py`: `'bootstrap4'` → `'bootstrap5'`. `crispy-bootstrap5==0.7` is already in `requirements.txt` and installed — add `'crispy_bootstrap5'` to `INSTALLED_APPS` alongside (or in place of, once migration completes) `crispy_bootstrap4`. |
| Bootstrap API renames | Fixed mapping applied wherever these classes/attributes appear: `data-toggle`→`data-bs-toggle`, `data-target`→`data-bs-target`, `data-dismiss`→`data-bs-dismiss`, `.ml-*`/`.mr-*`→`.ms-*`/`.me-*`, `.pl-*`/`.pr-*`→`.ps-*`/`.pe-*`, `.float-left`/`.float-right`→`.float-start`/`.float-end`, `.text-left`/`.text-right`→`.text-start`/`.text-end`, `.badge-pill`→`.rounded-pill`, `.badge-{color}`→`.bg-{color}` (on a `.badge` element), `.thead-dark`/`.thead-light`→`.table-dark`/`.table-light`, `.sr-only`→`.visually-hidden`, `.form-row`→`.row.g-3`, `.custom-control`/`.custom-checkbox`/`.custom-radio`/`.custom-select`→`.form-check`/`.form-select`, `.close`→`.btn-close` |

This mapping is documented here so later phases (rolling out to the
remaining ~400 templates) can apply it mechanically.

## Phase 1 scope

**Shared shell (required foundation):**
- `stock/templates/layouts.html`
- `stock/templates/navbar.html`
- `stock/templates/sidebar.html`
- `static/css/layouts.css`
- `djangostock/settings.py` (crispy config only)

**New component:**
- `stock/templates/partials/kpi_row.html` (new, reusable)

**Representative pages** (prove the pattern end-to-end, already in active
use this session):
- `stock/templates/express/viewExOiInvoice.html`
- `stock/templates/report/viewPO.html`
- `stock/templates/report/viewPOItem.html`

**Explicitly out of scope for Phase 1:**
- The remaining ~400 templates (future phases, separate spec/plan each,
  reusing this phase's shell + component + rename map)
- Any business logic / `views.py` changes beyond an optional single
  aggregate query per representative list page, per the KPI data contract
  above
- Dark mode
- `stock/templates/mobileApp/menu.html` and related mobile views (separate
  concern)

## Validation

- Visual check in browser: shell renders correctly, sidebar collapse /
  company-switch dropdown / tab navigation still function (jQuery-driven
  interactions unchanged)
- Each representative page: filters submit correctly, table/pagination
  unchanged, KPI row (where present) shows correct counts
- No Bootstrap 4-only class/attribute left in the touched files
