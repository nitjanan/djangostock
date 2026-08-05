# Bootstrap 5 UI Redesign — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the project from Bootstrap 4.1.0 to 5.3.8, apply the approved "STG Modern" visual design (Design A + KPI summary cards) to the shared shell and three representative pages, without changing any business logic.

**Architecture:** A single shared `layouts.html` means the Bootstrap version bump is global and instant — every page gets Bootstrap 5 CSS/JS the moment Task 1 lands, whether or not its templates have been visually migrated yet. Task 1 therefore bundles the CDN swap with a project-wide mechanical compatibility sweep (`data-toggle`→`data-bs-toggle` etc.) so nothing breaks. The *visual* redesign (colors, fonts, new components) stays scoped to the shell (navbar/sidebar/layouts.css) and 3 representative pages — the rest of the ~400 templates are out of scope for this phase and are addressed by later, separate plans.

**Tech Stack:** Django 3.2 templates, Bootstrap 5.3.8 (CDN), django-crispy-forms + crispy-bootstrap5, jQuery (kept for existing app scripts), vanilla Bootstrap 5 JS (bundle build, no separate Popper needed).

**A note on the SRI hashes below:** the `integrity="sha384-..."` values in Task 1 were not guessed — they were verified by downloading the actual files from jsDelivr and computing SHA-384 locally, cross-checked against Bootstrap's official docs site. If you ever bump the Bootstrap version beyond 5.3.8, you MUST regenerate the hash the same way (download the real file, hash it yourself) — a mismatched `integrity` attribute makes the browser refuse to load the file at all, which would break the whole site's CSS/JS, not just skip a security check. Never hand-type or guess an SRI hash.

## Global Constraints

- No business-logic changes. Where a view needs a new value (KPI card data), add the smallest possible addition — never modify existing query filters/permissions.
- Never rename a CSS class or context variable that Python code passes in as a literal string (e.g. `"tab-active"`, `"enableNav"`, `"disableNav"`, `"active show"`, `"show"` visibility toggles, or any `{{ xxx_page }}` / `{{ xxx_show }}` context var driven from `stock/views.py`). These are logic, not decoration — only their *color/spacing* may change, never their name.
- Keep jQuery loaded exactly as today (both existing `<script>` tags, unchanged order) — app scripts (`setCompany`, sidebar toggle, scroll listener, favicon badge, tab-width resize) must keep working byte-for-byte.
- Every task that touches a template must leave the page rendering with zero Django template errors and zero remaining Bootstrap-4-only classes/attributes in the files it touched.
- Design tokens (colors, fonts, radius) come from the approved mockup `.superpowers/mockups/a-stg-modern.html` — reuse those exact values, don't reinvent.

---

### Task 1: Bootstrap 5 upgrade + project-wide compatibility sweep

This is one atomic task: the CDN bump and the attribute-rename sweep must land together, otherwise the site is broken in between (Bootstrap 5 JS doesn't recognize `data-toggle`, and Bootstrap 4 JS wouldn't recognize `data-bs-toggle`).

**Files:**
- Modify: `stock/templates/layouts.html`
- Modify: all templates under `stock/templates/` containing `data-toggle=`, `data-target=`, or `data-dismiss=` (22 files, 126 occurrences — see step 3)

**Interfaces:**
- Produces: Bootstrap 5.3.8 loaded globally via `bootstrap.bundle.min.js` (includes Popper v2). A jQuery shim `$.fn.modal` supporting `.modal('show')` / `.modal('hide')`, used unchanged by 15 existing files.

- [ ] **Step 1: Swap the Bootstrap/Font Awesome CDN links and add Design A fonts**

In `stock/templates/layouts.html`, replace:

```html
    <!-- Bootstrap CSS CDN -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.0/css/bootstrap.min.css" integrity="sha384-9gVQ4dYFwwWSjIDZnLEWnxCjeSWFphJiwGPXr1jddIhOegiu1FwO5qRGvFXOdJZ4" crossorigin="anonymous">

    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">
    
    <link rel="stylesheet" type='text/css' href="{% static 'css/layouts.css' %}">
```

with:

```html
    <!-- Bootstrap CSS CDN -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB" crossorigin="anonymous">

    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">

    <!-- Design system fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@500;600;700&family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">

    <link rel="stylesheet" type='text/css' href="{% static 'css/layouts.css' %}">
```

- [ ] **Step 2: Swap the Bootstrap JS bundle, drop the separate Popper CDN, add the jQuery `.modal()` shim**

In `stock/templates/layouts.html`, replace:

```html
    <!-- jQuery CDN - Slim version (=without AJAX) -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <!-- Popper.JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.0/umd/popper.min.js" integrity="sha384-cs/chFZiN24E4KMATLdqdvsezGxaGsi4hLGOzlXwp5UZB1LY//20VyM2taTB4QvJ" crossorigin="anonymous"></script>
    <!-- Bootstrap JS -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.0/js/bootstrap.min.js" integrity="sha384-uefMccjFJAIv6A+rW+L4AHf99KvxDjWSu1z9VI8SKNVmz4sk7buKt/6v9KI65qnm" crossorigin="anonymous"></script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>

	<script>
        
        $(document).ready(function () {
            $('#sidebarCollapse').on('click', function () {
                $('#sidebar').toggleClass('active');
            });
        });
```

with:

```html
    <!-- jQuery CDN - Slim version (=without AJAX) -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <!-- Bootstrap 5 JS bundle (includes Popper v2 - no separate Popper script needed) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js" integrity="sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI" crossorigin="anonymous"></script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>

	<script>
        // Bootstrap 5 dropped jQuery plugin registration. A handful of existing
        // pages call $(el).modal('show'/'hide') directly — this shim keeps that
        // exact call syntax working against Bootstrap 5's vanilla JS API.
        if (window.bootstrap && window.jQuery) {
            jQuery.fn.modal = function (action) {
                return this.each(function () {
                    var instance = bootstrap.Modal.getOrCreateInstance(this);
                    if (action === 'show') instance.show();
                    else if (action === 'hide') instance.hide();
                    else if (action === 'toggle') instance.toggle();
                });
            };
        }

        $(document).ready(function () {
            $('#sidebarCollapse').on('click', function () {
                $('#sidebar').toggleClass('active');
            });
        });
```

- [ ] **Step 3: Run the project-wide `data-toggle`/`data-target`/`data-dismiss` sweep**

First, capture the current count so the "after" check has something to compare against:

Run: `grep -rE "data-(toggle|target|dismiss)=" stock/templates --include="*.html" -l | wc -l`
Expected: `22`

Run this PowerShell to do the rename across every template file (Windows dev machine — use the PowerShell tool, not Bash, so encoding stays UTF-8 for the Thai text in these files):

```powershell
Get-ChildItem -Path stock/templates -Filter *.html -Recurse | ForEach-Object {
    $content = Get-Content -Raw -LiteralPath $_.FullName -Encoding UTF8
    $updated = $content -replace 'data-toggle=', 'data-bs-toggle=' `
                         -replace 'data-target=', 'data-bs-target=' `
                         -replace 'data-dismiss=', 'data-bs-dismiss='
    if ($updated -ne $content) {
        [System.IO.File]::WriteAllText($_.FullName, $updated, (New-Object System.Text.UTF8Encoding($false)))
    }
}
```

- [ ] **Step 4: Verify the sweep**

Run: `grep -rE "data-(toggle|target|dismiss)=" stock/templates --include="*.html" -l | wc -l`
Expected: `0`

Run: `grep -rE "data-bs-(toggle|target|dismiss)=" stock/templates --include="*.html" -l | wc -l`
Expected: `22`

- [ ] **Step 5: Django template sanity check**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).` — confirms no template got mangled into invalid syntax by the regex replace (the patterns only match literal attribute names, not `{% %}`/`{{ }}` tags, so this should be a formality).

- [ ] **Step 6: Manual smoke test**

Start the dev server (`python manage.py runserver`), log in, and check on any page that still has a dropdown/collapse (e.g. the sidebar's "Request" submenu, or the navbar's user/category dropdown if visible): clicking still expands/collapses it. This confirms Bootstrap 5's JS is correctly wired to the renamed attributes.

- [ ] **Step 7: Commit**

```bash
git add stock/templates/layouts.html
git add -u stock/templates
git commit -m "feat: upgrade Bootstrap 4 to 5.3.8 with project-wide data-bs-* compatibility sweep"
```

---

### Task 1b: Fix project-wide filter-form layout collapse (`.form-row` removed in Bootstrap 5)

**Inserted after Task 1 shipped.** Bootstrap 5 removed `.form-row` entirely — it was Bootstrap 4's flex container specifically for form grids (a lighter-gutter sibling of `.row`). Every filter form in this project wraps its `.form-group col-md-N` columns in `<div class="form-row">`. Under Bootstrap 4 that div established `display: flex`, which is what made the columns sit side-by-side. Under Bootstrap 5, `.form-row` has no CSS at all, so the wrapper is an inert block-level div and every column collapses to full width, stacked vertically — every filter form project-wide currently looks broken (confirmed live by the human partner immediately after Task 1 landed, with a screenshot showing exactly this).

This was a severity misjudgment in the original plan: `.form-row` was bucketed with the *cosmetic* Bootstrap-4-only renames (`text-left`, `badge-pill`, etc. — deferred to per-page work in later phases) when it is actually structural, like the `data-toggle` sweep in Task 1. It needs the same project-wide, immediate treatment.

**Files:**
- Modify: all templates under `stock/templates/` containing `form-row` (42 files — see step 1)

**Interfaces:**
- Produces: every existing `<div class="form-row">` becomes `<div class="row">`, restoring Bootstrap 5's own flex grid behavior for the `col-md-N` children already inside. No other markup changes — column classes, field names, and all `{{ }}`/`{% %}` template logic stay exactly as they are.

- [ ] **Step 1: Capture the baseline**

Run: `grep -rl "form-row" stock/templates --include="*.html" | wc -l`
Expected: `42`

- [ ] **Step 2: Run the sweep**

Use the PowerShell tool (not Bash), for the same UTF-8-safety reason as Task 1's sweep:

```powershell
Get-ChildItem -Path stock/templates -Filter *.html -Recurse | ForEach-Object {
    $content = Get-Content -Raw -LiteralPath $_.FullName -Encoding UTF8
    $updated = $content -replace 'class="form-row"', 'class="row"' `
                         -replace "class='form-row'", "class='row'"
    if ($updated -ne $content) {
        [System.IO.File]::WriteAllText($_.FullName, $updated, (New-Object System.Text.UTF8Encoding($false)))
    }
}
```

This only matches `form-row` when it is the *entire* class attribute value (`class="form-row"` or with single quotes) — deliberately narrow, so it can't accidentally clip a hypothetical `class="form-row-something-else"` or a multi-class attribute where `form-row` sits next to other classes. Confirm with step 1's grep (searching for the bare substring `form-row`) that this narrower replace still catches all 42 files; if any file uses `form-row` combined with another class in the same attribute (e.g. `class="form-row mb-2"`), report that file in NEEDS_CONTEXT rather than guessing how to handle it — do not broaden the regex without checking each such case individually first.

- [ ] **Step 3: Verify**

Run: `grep -rl "form-row" stock/templates --include="*.html" | wc -l`
Expected: `0`

Run: `python manage.py check`
Expected: only the one pre-existing `fields.W340` warning noted in the plan's ledger — no new issues.

- [ ] **Step 4: Manual verification**

Start the dev server, open a page with a filter form that was previously broken (e.g. Report → "สรุปใบสั่งซื้อที่อนุมัติ" / `viewPO.html`, or the Express oil invoice page) and confirm the filter fields now sit in a proper multi-column grid again (not stacked full-width). This is the human partner's exact complaint — the fix must be visibly confirmed, not just grep-verified.

- [ ] **Step 5: Commit**

```bash
git add -u stock/templates
git commit -m "fix: restore filter-form grid layout after Bootstrap 5 removed .form-row"
```

---

### Task 2: Switch crispy-forms to the Bootstrap 5 template pack

**Files:**
- Modify: `djangostock/settings.py:60-61` (INSTALLED_APPS)
- Modify: `djangostock/settings.py:217` (CRISPY_TEMPLATE_PACK)

**Interfaces:**
- Consumes: Task 1's Bootstrap 5 CSS being loaded globally (crispy-bootstrap5's markup — `mb-3` wrappers, `form-select`, `form-check` — needs Bootstrap 5 CSS to render correctly; that's now true site-wide after Task 1).
- Produces: every `{{ field|as_crispy_field }}` / `{% crispy form %}` call site project-wide now renders Bootstrap 5 markup. No template call sites change.

- [ ] **Step 1: Replace crispy_bootstrap4 with crispy_bootstrap5 in INSTALLED_APPS**

Nothing in this codebase references a template pack by name (`grep -rE "crispy.*bootstrap4|\{%\s*crispy\s+\w+\s+['\"]bootstrap4" stock/templates` returns no matches) — `CRISPY_TEMPLATE_PACK` is the only thing that selects a pack, and every render goes through it. So `crispy_bootstrap4` becomes genuinely unused the moment step 2 flips the default pack; keep it registered and it's dead config. Remove it.

In `djangostock/settings.py`, replace:

```python
    'crispy_forms',
    'crispy_bootstrap4',
```

with:

```python
    'crispy_forms',
    'crispy_bootstrap5',
```

(`crispy-bootstrap4` stays in `requirements.txt` — leaving the *package* installed but unregistered is harmless and outside this task's scope; removing the Django app registration is what actually matters, since that's the part that's dead.)

- [ ] **Step 2: Switch the default template pack**

In `djangostock/settings.py`, replace:

```python
CRISPY_TEMPLATE_PACK = 'bootstrap4'
```

with:

```python
CRISPY_TEMPLATE_PACK = 'bootstrap5'
```

- [ ] **Step 3: Verify**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Start the dev server and open any page with a crispy-rendered form filter (e.g. `/report/po/` if that's the URL for `viewPOReport`, or the login page) — fields should render with visible labels, spacing, and a working submit button. No raw `{% crispy %}` template errors in the page or server console.

- [ ] **Step 4: Commit**

```bash
git add djangostock/settings.py
git commit -m "feat: switch crispy-forms to the bootstrap5 template pack"
```

---

### Task 2b: Fix login page 500 error — add CRISPY_ALLOWED_TEMPLATE_PACKS (CRITICAL, found during Task 10)

**Inserted after Task 3b.** Task 2 fixed the `as_crispy_field` filter path but missed that django-crispy-forms 2.0's `{% crispy %}` **tag** validates the pack name against a separate whitelist that doesn't include `'bootstrap5'` by default — breaking every `{% crispy form %}`-tag page project-wide, including `/account/login`. Never caught earlier because every later task's verification bypassed login via direct session injection. Full brief, root-cause traceback, and controller-confirmed fix at `.superpowers/sdd/2026-08-03-bootstrap5-ui-redesign-phase1/task-2b-brief.md`.

---

### Task 3: Restyle navbar.html to the STG Modern design

**Files:**
- Modify: `stock/templates/navbar.html:87` (only the inline background-color; structure/logic untouched)

**Interfaces:**
- Consumes: Design tokens defined in Task 5 (`--stg-mist`, `.navbar` rules in `layouts.css`) — this task only needs to stop hardcoding a conflicting inline color so Task 5's CSS can take effect.

- [ ] **Step 1: Remove the hardcoded inline background so the stylesheet controls it**

In `stock/templates/navbar.html`, replace:

```html
<nav class="navbar navbar-expand-md navbar-light" style="background-color: #EBF5FB;">
```

with:

```html
<nav class="navbar navbar-expand-md navbar-light">
```

(Task 5 adds a `layouts.css` rule for `.main .topbar` / `nav.navbar` background. No other line in this file changes — the company-switcher dropdown, search form, tab loop, and all `{{ }}` context variables stay exactly as they are.)

- [ ] **Step 2: Verify**

This file has no independent visual meaning until Task 5's CSS lands — defer visual verification to Task 5's step. For now just confirm the file still parses:

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add stock/templates/navbar.html
git commit -m "style: remove hardcoded navbar background color for design system"
```

---

### Task 3b: Finish navbar.html's Bootstrap 5 class migration (gap found by Task 10's verification sweep)

**Inserted after Task 9 shipped, found by running Task 10's own Step 1 check early.** Task 3 was scoped too narrowly — it only removed one hardcoded inline background-color. navbar.html still had real, live, rendering Bootstrap-4-only classes (`ml-5` on the mobile toggler, `badge-pill`/`badge-dark` on all 17 company-tab notification badges) that were never migrated, violating the plan's Global Constraint of zero remaining Bootstrap-4-only classes in files a task touched. Full brief at `.superpowers/sdd/2026-08-03-bootstrap5-ui-redesign-phase1/task-3b-brief.md` (written directly, not via the numbered task-brief script, for the same "3b" vs "3" heading-collision reason as Task 1b).

---

### Task 4: Restyle sidebar.html badges to Bootstrap 5 syntax

**Files:**
- Modify: `stock/templates/sidebar.html` (badge class renames only — 7 occurrences)

**Interfaces:**
- Produces: notification count badges (`pc_all`, `ma_all`, `is_purchasing_pr`, `add_po_all`, `all_pr_ap`, `all_cp_ap`, `all_po_ap`) keep showing with a colored pill background under Bootstrap 5 (Bootstrap 5 removed the combined `.badge-warning` class — it requires separate `.badge` + `.bg-warning`).

- [ ] **Step 1: Rename badge classes**

In `stock/templates/sidebar.html`, there are 7 occurrences of this exact pattern (one per count badge — `pc_all`, `ma_all`, `is_purchasing_pr` (via `add_po_all` line), `ap_all`, `all_pr_ap`, `all_cp_ap`, `all_po_ap`):

```html
<span class="float-right badge badge-pill badge-warning notification mr-5">
```

Replace **every** occurrence with:

```html
<span class="float-end badge rounded-pill bg-warning notification me-5">
```

This is a pure find-and-replace across the file (the text inside the span — `{{pc_all}}`, `{{ma_all}}`, etc. — is untouched). Use your editor's "replace all in file" rather than editing each `{% if %}` block individually, since the surrounding Django template logic (which counter, which `{% if %}` guard) must stay byte-for-byte identical.

- [ ] **Step 2: Verify**

Run: `grep -c "badge-pill\|badge-warning" stock/templates/sidebar.html`
Expected: `0`

Run: `grep -c "rounded-pill.*bg-warning\|bg-warning.*rounded-pill" stock/templates/sidebar.html`
Expected: `7`

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add stock/templates/sidebar.html
git commit -m "style: migrate sidebar notification badges to Bootstrap 5 class syntax"
```

---

### Task 5: Design tokens + shell restyle in layouts.css

This is the task that actually makes Tasks 3–4's changes (and the shell overall) look like "STG Modern." The bottom section of the file (from the `PREMIUM IOS/GMAIL STYLE NOTIFICATION BADGE` comment onward — `#nav-tabs`, `#company-select`, `.badge-notification`) is recently-built, sophisticated, working code and is **not touched** — this task only edits the top section (tokens, body, sidebar, active-state colors) and appends new reusable component classes.

**Files:**
- Modify: `static/css/layouts.css` (lines 1–207, i.e. everything before the `SIDEBAR STYLE` section's `@media (max-width: 1330px)` block ends and the premium-badge comment begins)
- Modify: `stock/templates/layouts.html:28-108` (inline `<style>` block — update the two colors that duplicate/override layouts.css, so both sources agree)

**Interfaces:**
- Produces: CSS custom properties (`--stg-ink`, `--stg-indigo`, `--stg-indigo-deep`, `--stg-periwinkle`, `--stg-mist`, `--stg-red`, `--stg-bg`) and reusable component classes (`.card-stg`, `.filter-card`, `.table-stg`, `.doc-link`, `.badge-status` + `.st-done`/`.st-wait`/`.st-urgent`, `.pagination-stg`, `.btn-stg`, `.kpi-row`, `.kpi-card` + `.kpi-hot`/`.kpi-ok`) that Tasks 6–9 consume.

- [ ] **Step 1: Replace the top of `static/css/layouts.css`**

Replace lines 1–207 (from the `@import` at the top through the end of the `@media (max-width: 1330px) { ... }` block, i.e. everything before the `/* PREMIUM IOS/GMAIL STYLE NOTIFICATION BADGE */` comment) with:

```css
:root {
    --stg-ink: #23295e;
    --stg-indigo: #3d478f;
    --stg-indigo-deep: #2a3170;
    --stg-periwinkle: #7386d5;
    --stg-mist: #eef0fa;
    --stg-red: #ed3237;
    --stg-bg: #f4f5fa;
    --stg-radius: 14px;
}

body {
    font-family: 'Sarabun', sans-serif;
    background: var(--stg-bg);
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Prompt', sans-serif;
}

p {
    font-family: 'Sarabun', sans-serif;
    font-size: 1.1em;
    font-weight: 300;
    line-height: 1.7em;
    color: #999;
}

a,
a:hover,
a:focus {
    color: inherit;
    text-decoration: none;
    transition: all 0.3s;
}

.navbar {
    padding: 15px 10px;
    background: #fff;
    border: none;
    border-radius: 0;
    margin-bottom: 40px;
    box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
}

.navbar-btn {
    box-shadow: none;
    outline: none !important;
    border: none;
}

.line {
    width: 100%;
    height: 1px;
    border-bottom: 1px dashed #ddd;
    margin: 40px 0;
}

i,
span {
    display: inline-block;
}

/* ---------------------------------------------------
    SIDEBAR STYLE
----------------------------------------------------- */

.wrapper {
    display: flex;
    align-items: stretch;
}

#sidebar {
    min-width: 250px;
    max-width: 250px;
    background: linear-gradient(180deg, var(--stg-indigo) 0%, var(--stg-indigo-deep) 100%);
    color: #dfe3f7;
    transition: all 0.3s;
}

#sidebar.active {
    min-width: 80px;
    max-width: 80px;
    text-align: center;
}

#sidebar.active .sidebar-header h3,
#sidebar.active .CTAs {
    display: none;
}

#sidebar.active .sidebar-header strong {
    display: block;
}

#sidebar ul li a {
    text-align: left;
}

#sidebar.active ul li a {
    padding: 20px 10px;
    text-align: center;
    font-size: 0.85em;
}

#sidebar.active ul li a i {
    margin-right: 0;
    display: block;
    font-size: 1.8em;
    margin-bottom: 5px;
}

#sidebar.active ul ul a {
    padding: 10px !important;
}

#sidebar.active .dropdown-toggle::after {
    top: auto;
    bottom: 10px;
    right: 50%;
    -webkit-transform: translateX(50%);
    -ms-transform: translateX(50%);
    transform: translateX(50%);
}

#sidebar .sidebar-header {
    padding: 20px;
    background: rgba(255, 255, 255, 0.08);
}

#sidebar .sidebar-header strong {
    display: none;
    font-size: 1.8em;
}

#sidebar ul.components {
    padding: 20px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

#sidebar ul li a {
    padding: 10px;
    font-size: 1.1em;
    display: block;
    color: #dfe3f7;
}

#sidebar ul li a:hover {
    color: var(--stg-indigo);
    background: #fff;
}

#sidebar ul li a i {
    margin-right: 10px;
}

#sidebar ul li.active>a,
a[aria-expanded="true"] {
    color: #fff;
    background: rgba(255, 255, 255, 0.14);
}

a[data-bs-toggle="collapse"] {
    position: relative;
}

.dropdown-toggle::after {
    display: block;
    position: absolute;
    top: 50%;
    right: 20px;
    transform: translateY(-50%);
}

ul ul a {
    font-size: 0.9em !important;
    padding-left: 30px !important;
    background: rgba(0, 0, 0, 0.12);
}

ul.CTAs {
    padding: 20px;
}

ul.CTAs a {
    text-align: center;
    font-size: 0.9em !important;
    display: block;
    border-radius: 5px;
    margin-bottom: 5px;
}

a.download {
    background: #fff;
    color: var(--stg-indigo);
}

a.article,
a.article:hover {
    background: var(--stg-indigo-deep) !important;
    color: #fff !important;
}

/* ---------------------------------------------------
    CONTENT STYLE
----------------------------------------------------- */

#content {
    width: 100%;
    padding: 20px;
    min-height: 100vh;
    transition: all 0.3s;
}

/* ---------------------------------------------------
    REUSABLE COMPONENTS (STG Modern design system)
----------------------------------------------------- */

.card-stg {
    background: #fff;
    border: 0;
    border-radius: var(--stg-radius);
    box-shadow: 0 1px 2px rgba(35, 41, 94, .05), 0 8px 24px rgba(35, 41, 94, .06);
}

.filter-card label {
    font-size: 12.5px;
    font-weight: 600;
    color: #6b7195;
    margin-bottom: 5px;
}

.table-stg {
    margin: 0;
    font-size: 14.5px;
}

.table-stg thead th {
    background: var(--stg-mist);
    color: #3a4160;
    font-weight: 600;
    font-size: 13px;
    border: 0;
    padding: 11px 18px;
    white-space: nowrap;
}

.table-stg tbody td,
.table-stg tbody th {
    padding: 12px 18px;
    border-color: #f0f1f8;
    vertical-align: middle;
}

.table-stg tbody tr:hover {
    background: #fafbfe;
}

.doc-link {
    color: var(--stg-indigo);
    font-weight: 700;
    text-decoration: none;
    font-variant-numeric: tabular-nums;
}

.doc-link:hover {
    text-decoration: underline;
}

.badge-status {
    font-size: 12px;
    font-weight: 600;
    border-radius: 99px;
    padding: 4px 12px;
}

.badge-status.st-done {
    background: #e5f6ec;
    color: #177245;
}

.badge-status.st-wait {
    background: #fff4e0;
    color: #a06008;
}

.badge-status.st-urgent {
    background: #fdeaea;
    color: var(--stg-red);
}

.btn-stg {
    background: var(--stg-indigo);
    border: 0;
    color: #fff;
    font-weight: 600;
    border-radius: 10px;
}

.btn-stg:hover {
    background: var(--stg-indigo-deep);
    color: #fff;
}

.pagination-stg .page-link {
    border: 0;
    color: #4d568c;
    font-weight: 600;
    border-radius: 9px;
    margin: 0 3px;
    font-size: 14px;
}

.pagination-stg .page-item.active .page-link {
    background: var(--stg-indigo);
    color: #fff;
}

.pagination-stg .page-link:hover {
    background: var(--stg-mist);
}

/* KPI summary row */

.kpi-row {
    --bs-gutter-x: 1rem;
}

.kpi-card {
    background: #fff;
    border: 1px solid #e5e8ee;
    border-radius: 10px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    height: 100%;
}

.kpi-card .kpi-label {
    font-size: 12.5px;
    color: #69748c;
    font-weight: 500;
}

.kpi-card .kpi-value {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -.01em;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
    color: var(--stg-ink);
}

.kpi-card .kpi-sub {
    font-size: 12px;
    color: #9aa3b5;
}

.kpi-card.kpi-hot {
    border-top: 3px solid #e8a33d;
}

.kpi-card.kpi-hot .kpi-value {
    color: #b97f27;
}

.kpi-card.kpi-ok .kpi-value {
    color: #1f9d5b;
}

/* ---------------------------------------------------
    MEDIAQUERIES
----------------------------------------------------- */
/* อันเดิม 768 */
@media (max-width: 1330px) {
    #sidebar {
        min-width: 80px;
        max-width: 80px;
        text-align: center;
        margin-left: -80px !important;
    }
    .dropdown-toggle::after {
        top: auto;
        bottom: 10px;
        right: 50%;
        -webkit-transform: translateX(50%);
        -ms-transform: translateX(50%);
        transform: translateX(50%);
    }
    #sidebar.active {
        margin-left: 0 !important;
    }
    #sidebar .sidebar-header h3,
    #sidebar .CTAs {
        display: none;
    }
    #sidebar .sidebar-header strong {
        display: block;
    }
    #sidebar ul li a {
        padding: 20px 10px;
    }
    #sidebar ul li a span {
        font-size: 0.85em;
    }
    #sidebar ul li a i {
        margin-right: 0;
        display: block;
    }
    #sidebar ul ul a {
        padding: 10px !important;
    }
    #sidebar ul li a i {
        font-size: 1.3em;
    }
    #sidebar {
        margin-left: 0;
    }
    #sidebarCollapse span {
        display: none;
    }
}
```

Leave everything from `/* PREMIUM IOS/GMAIL STYLE NOTIFICATION BADGE */` to the end of the file (badge-notification, `#nav-tabs`, `#company-select`, their media queries) **completely unchanged**.

- [ ] **Step 2: Sync the duplicate color in `layouts.html`'s inline `<style>` block**

`stock/templates/layouts.html` has its own `<style>` block that also sets `#sidebar .sidebar-header` and duplicates `.navbar`/`.fixed-top` rules. Only the one duplicate that visibly conflicts with Design A needs updating — the sidebar header background. Replace:

```html
    <style>
        #sidebar .sidebar-header {
            padding: 20px;
            background: #d5daf2;
        }
```

with:

```html
    <style>
        #sidebar .sidebar-header {
            padding: 20px;
            background: rgba(255, 255, 255, 0.08);
        }
```

(This inline block loads after `layouts.css` in the document, so without this change its old `#d5daf2` value would win the cascade and the sidebar header would still show the old lavender color. Nothing else in this inline block needs to change — `.tab-active`, `.disableTab`, `.disableNav`, `.enableNav`, `.pointer`, `.fixed-top` etc. are logic-driven class names from `stock/views.py` and keep their current values.)

- [ ] **Step 3: Verify**

Run the dev server, log in, and visually confirm:
- Sidebar shows an indigo-to-deep-indigo gradient (not flat purple `#7386D5`)
- Sidebar header area is a subtle translucent white, not lavender
- Sidebar collapse toggle (`#sidebarCollapse`) still works (jQuery `.toggleClass('active')` untouched)
- Company tab switching (the `setCompany()` AJAX call) still works and still shows/hides badges correctly — this exercises the untouched bottom section of layouts.css

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add static/css/layouts.css stock/templates/layouts.html
git commit -m "feat: add STG Modern design tokens and reusable component classes"
```

---

### Task 6: Build the reusable KPI row component

**Files:**
- Create: `stock/templates/partials/kpi_row.html`

**Interfaces:**
- Consumes: a context variable `kpi_cards` — a list of dicts, each with keys `label` (str, required), `value` (number, required), `sub` (str, optional), `tone` (str, optional — `"hot"` or `"ok"`, matches the `.kpi-hot`/`.kpi-ok` CSS classes from Task 5).
- Produces: renders `.kpi-row` / `.kpi-card` markup (Task 5's CSS). Any future page adopts this component by building a `kpi_cards` list in its view and adding `{% include 'partials/kpi_row.html' %}` to its template — no other wiring needed.

- [ ] **Step 1: Create the partial**

```html
{% load humanize %}
{% if kpi_cards %}
<div class="row g-3 kpi-row mb-3">
  {% for card in kpi_cards %}
  <div class="col-6 col-lg-3">
    <div class="kpi-card{% if card.tone %} kpi-{{ card.tone }}{% endif %}">
      <span class="kpi-label">{{ card.label }}</span>
      <span class="kpi-value">{{ card.value|intcomma }}</span>
      {% if card.sub %}<span class="kpi-sub">{{ card.sub }}</span>{% endif %}
    </div>
  </div>
  {% endfor %}
</div>
{% endif %}
```

The `{% if kpi_cards %}` guard means any page that doesn't pass `kpi_cards` (i.e. every page not yet migrated) silently renders nothing — safe to `{% include %}` defensively in the future without checking first.

- [ ] **Step 2: Verify**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).` (Django's template loader validates the file is well-formed on first render; `check` alone won't catch template syntax errors in an unreferenced file, so this step is superseded by Task 7's visual check — this step just confirms the app still boots.)

- [ ] **Step 3: Commit**

```bash
git add stock/templates/partials/kpi_row.html
git commit -m "feat: add reusable KPI summary row component"
```

---

### Task 7: Apply the design system to viewExOiInvoice (Express oil)

**Files:**
- Modify: `stock/views.py:7656-7688` (`viewExOiInvoice`)
- Modify: `stock/templates/express/viewExOiInvoice.html`

**Interfaces:**
- Consumes: `partials/kpi_row.html` (Task 6), `.card-stg`/`.filter-card`/`.table-stg`/`.doc-link`/`.pagination-stg` (Task 5).
- Produces: `kpi_cards` = `[{'label': 'จำนวนรายการทั้งหมด', 'value': <int>}, {'label': 'ยอดรวมหน้านี้', 'value': <Decimal>, 'sub': 'บาท (เฉพาะหน้าที่แสดง)'}]`.

- [ ] **Step 1: Add KPI data to the view**

In `stock/views.py`, `viewExOiInvoice` currently reads (lines 7675–7688 — note: line numbers shift as `stock/views.py` is edited by earlier tasks/other work; match by the code content shown, not the line number):

```python
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    
    context = {
        'ois': dataPage,
        'filter':myFilter,
        'ex_o_i_page': "tab-active",
        'ex_o_i_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "express/viewExOiInvoice.html", context)
```

Replace with:

```python
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    # ยอดรวมเฉพาะรายการที่แสดงในหน้านี้ (get_total_price ต้อง query ทีละแถว
    # จาก pg_db อยู่แล้วเพื่อแสดงในตาราง จึงรวมยอดจากแถวเดียวกันนี้ ไม่ query เพิ่ม)
    page_oi_total = sum(oi.get_total_price() for oi in dataPage)

    kpi_cards = [
        {'label': 'จำนวนรายการทั้งหมด', 'value': dataPage.paginator.count},
        {'label': 'ยอดรวมหน้านี้', 'value': page_oi_total, 'sub': 'บาท (เฉพาะหน้าที่แสดง)'},
    ]

    context = {
        'ois': dataPage,
        'filter':myFilter,
        'kpi_cards': kpi_cards,
        'ex_o_i_page': "tab-active",
        'ex_o_i_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "express/viewExOiInvoice.html", context)
```

- [ ] **Step 2: Restyle the template**

In `stock/templates/express/viewExOiInvoice.html`, replace the full `{% block content %}` section:

```html
{% block content %}
<div class="container my-3">
<h3 align="center">ใบจ่ายสินค้าภายใน - น้ำมัน Express</h3>
<div class="card my-3 bg-light div-shadow">
  <div class="card-body">
    <form method="get">
      {% csrf_token %}
      <div class="form-row">
        <div class="form-group col-md-2 mb-0">
          {{ filter.form.docnum|as_crispy_field }}
        </div>
        <div class="form-group col-md-3 mb-0">
          {{ filter.form.depcod|as_crispy_field }}
        </div>
        <div class="form-group col-md-3 mb-0">
          {{ filter.form.depname|as_crispy_field }}
        </div>
        <div class="form-group col-md-4 mb-0">
          {{ filter.form.remark|as_crispy_field }}
        </div>
        <div class="form-group col-md-2 mb-0">
          {{ filter.form.start_created|as_crispy_field }}
        </div>
        <div class="form-group col-md-2 mb-0">
          {{ filter.form.end_created|as_crispy_field }}
        </div>
        <div class="form-group col-md-1 mb-0">
          <div>
            <label for=""></label>
            <div class="my-2">
              <button type="submit" class="btn btn-info">กรอง<i class="fas fa-filter"></i></button>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</div>
<div class="card div-shadow">
  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-striped my-3">
        <thead class="thead-dark">
          <tr>
            <th scope="col">เลขที่เอกสาร</th>
            <th scope="col">วันที่จ่าย</th>
            <th scope="col">สินค้า</th>
            <th scope="col">exp แผนกคชจ.</th>
            <th scope="col">แผนกคชจ.</th>
            <th scope="col">หมายเหตุ</th>
            <th scope="col">จำนวนเงิน</th>
          </tr>
        </thead>
        <tbody>
        {% for oi in ois %}
          <tr>
            <th scope="row"><a href="">{{oi.docnum}}</a></th>
            <td>{{oi.docdat |date:"d/m/Y" }}</td>
            <td>{{oi.get_items|safe }}</td>
            <td>{{oi.depcod}}</td>
            <td>{{oi.get_depnam}}</td>
            <td>{{oi.remark}}</td>
            <td class="text-right">{{oi.get_total_price | intcomma}}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
      <br/>
      <!--Pagination-->
      <nav aria-label="Page navigation example">
        <ul class="pagination justify-content-center">
        {% if ois.has_previous %}
            <li class="page-item">
            <a class="page-link" href="{% my_url ois.previous_page_number 'page' request.GET.urlencode %}">Previous</a>
          </li>
        {% else %}
            <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a>
          </li>
        {% endif %}

        {% if ois.number|add:'-4' > 1 %}
            <li class="page-item"><a class="page-link" href="{% my_url ois.number|add:'-5' 'page' request.GET.urlencode %}">&hellip;</a></li>
        {% endif %}

        {% for i in ois.paginator.page_range %}
            {% if ois.number == i %}
                <li class="page-item active" aria-current="page">
              <span class="page-link">
                {{ i }}
                <span class="sr-only">(current)</span>
              </span>
            </li>
            {% elif i > ois.number|add:'-5' and i < ois.number|add:'5' %}
                 <li class="page-item"><a class="page-link" href="{% my_url i 'page' request.GET.urlencode %}">{{ i }}</a></li>
            {% endif %}
        {% endfor %}

        {% if ois.paginator.num_pages > ois.number|add:'4' %}
           <li class="page-item"><a class="page-link" href="{% my_url ois.number|add:'5' 'page' request.GET.urlencode %}">&hellip;</a></li>
        {% endif %}

        {% if ois.has_next %}
            <li class="page-item">
            <a class="page-link"  href="{% my_url ois.next_page_number 'page' request.GET.urlencode %}">Next</a>
          </li>
        {% else %}
            <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1" aria-disabled="true">Next</a>
          </li>
        {% endif %}
      </ul>
    </nav>
    <!--end of Pagination-->
</div>
{% endblock%}
```

with:

```html
{% block content %}
<div class="container my-3">
<h3 align="center">ใบจ่ายสินค้าภายใน - น้ำมัน Express</h3>

{% include 'partials/kpi_row.html' %}

<div class="card-stg filter-card my-3">
  <div class="card-body">
    <form method="get">
      {% csrf_token %}
      <div class="form-row">
        <div class="form-group col-md-2 mb-0">
          {{ filter.form.docnum|as_crispy_field }}
        </div>
        <div class="form-group col-md-3 mb-0">
          {{ filter.form.depcod|as_crispy_field }}
        </div>
        <div class="form-group col-md-3 mb-0">
          {{ filter.form.depname|as_crispy_field }}
        </div>
        <div class="form-group col-md-4 mb-0">
          {{ filter.form.remark|as_crispy_field }}
        </div>
        <div class="form-group col-md-2 mb-0">
          {{ filter.form.start_created|as_crispy_field }}
        </div>
        <div class="form-group col-md-2 mb-0">
          {{ filter.form.end_created|as_crispy_field }}
        </div>
        <div class="form-group col-md-1 mb-0">
          <div>
            <label for=""></label>
            <div class="my-2">
              <button type="submit" class="btn btn-stg">กรอง<i class="fas fa-filter ms-1"></i></button>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</div>
<div class="card-stg">
  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-stg my-3">
        <thead class="table-dark">
          <tr>
            <th scope="col">เลขที่เอกสาร</th>
            <th scope="col">วันที่จ่าย</th>
            <th scope="col">สินค้า</th>
            <th scope="col">exp แผนกคชจ.</th>
            <th scope="col">แผนกคชจ.</th>
            <th scope="col">หมายเหตุ</th>
            <th scope="col">จำนวนเงิน</th>
          </tr>
        </thead>
        <tbody>
        {% for oi in ois %}
          <tr>
            <th scope="row"><a class="doc-link" href="">{{oi.docnum}}</a></th>
            <td>{{oi.docdat |date:"d/m/Y" }}</td>
            <td>{{oi.get_items|safe }}</td>
            <td>{{oi.depcod}}</td>
            <td>{{oi.get_depnam}}</td>
            <td>{{oi.remark}}</td>
            <td class="text-end">{{oi.get_total_price | intcomma}}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
      <br/>
      <!--Pagination-->
      <nav aria-label="Page navigation example">
        <ul class="pagination pagination-stg justify-content-center">
        {% if ois.has_previous %}
            <li class="page-item">
            <a class="page-link" href="{% my_url ois.previous_page_number 'page' request.GET.urlencode %}">Previous</a>
          </li>
        {% else %}
            <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a>
          </li>
        {% endif %}

        {% if ois.number|add:'-4' > 1 %}
            <li class="page-item"><a class="page-link" href="{% my_url ois.number|add:'-5' 'page' request.GET.urlencode %}">&hellip;</a></li>
        {% endif %}

        {% for i in ois.paginator.page_range %}
            {% if ois.number == i %}
                <li class="page-item active" aria-current="page">
              <span class="page-link">
                {{ i }}
                <span class="visually-hidden">(current)</span>
              </span>
            </li>
            {% elif i > ois.number|add:'-5' and i < ois.number|add:'5' %}
                 <li class="page-item"><a class="page-link" href="{% my_url i 'page' request.GET.urlencode %}">{{ i }}</a></li>
            {% endif %}
        {% endfor %}

        {% if ois.paginator.num_pages > ois.number|add:'4' %}
           <li class="page-item"><a class="page-link" href="{% my_url ois.number|add:'5' 'page' request.GET.urlencode %}">&hellip;</a></li>
        {% endif %}

        {% if ois.has_next %}
            <li class="page-item">
            <a class="page-link"  href="{% my_url ois.next_page_number 'page' request.GET.urlencode %}">Next</a>
          </li>
        {% else %}
            <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1" aria-disabled="true">Next</a>
          </li>
        {% endif %}
      </ul>
    </nav>
    <!--end of Pagination-->
</div>
{% endblock%}
```

(Only class names and the two new lines — `{% include %}` and the KPI view code — changed. Every `{{ }}` variable, URL tag, and `{% for %}`/`{% if %}` block is identical to before.)

- [ ] **Step 3: Verify**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Start the dev server, navigate to the Express → "ใบจ่ายสินค้าภายใน - น้ำมัน" page:
- Two KPI cards show above the filter card (total record count, this-page total)
- Filter form still submits and filters correctly (same fields, same GET params)
- Table renders with the new dark header, doc-number links still work
- Pagination still works (Previous/Next, page numbers, ellipsis for far pages)

- [ ] **Step 4: Commit**

```bash
git add stock/views.py stock/templates/express/viewExOiInvoice.html
git commit -m "feat: apply STG Modern design + KPI cards to Express oil invoice page"
```

---

### Task 8: Apply the design system to viewPO.html (PO report)

**Files:**
- Modify: `stock/views.py:5081-5134` (`viewPOReport` — match by the code content shown below, not this line range; earlier edits in this session may have shifted it)
- Modify: `stock/templates/report/viewPO.html`

**Interfaces:**
- Consumes: `partials/kpi_row.html` (Task 6), `.card-stg`/`.filter-card`/`.table-stg`/`.doc-link`/`.pagination-stg`/`.btn-stg` (Task 5).
- Produces: `kpi_cards` = `[{'label': 'จำนวนรายการทั้งหมด', 'value': <int>}, {'label': 'มูลค่ารวม (ตามตัวกรอง)', 'value': <Decimal>, 'sub': 'บาท'}]`.

- [ ] **Step 1: Add KPI data to the view**

In `stock/views.py`, `viewPOReport` currently reads:

```python
def viewPOReport(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseOrder.objects.filter(approver_status = 2, branch_company__code__in = company_in, is_cancel = False).distinct() #ใส่ distinct เพราะ filter purchaseorderitem__item__machine ทำให้เบิ้ลรายการตาม items

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs
    data = data.select_related(
        'cp',
        'credit',
        'distributor',
        'pr',
        'stockman_user',
    )

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    dataPage.object_list = list(dataPage.object_list)

    po_ids = [po.id for po in dataPage.object_list if po.pr_id]
    pr_rows = (
        PurchaseOrderItem.objects
        .filter(
            po_id__in=po_ids,
            item__requisit__pr_ref_no__isnull=False,
        )
        .exclude(item__requisit__pr_ref_no='')
        .values(
            'po_id',
            'item__requisit__pr_ref_no',
            'item__requisit__purchase_requisition_id',
        )
        .distinct()
        .order_by('po_id', 'item__requisit__pr_ref_no')
    )

    prs_by_po = defaultdict(list)
    for pr in pr_rows:
        prs_by_po[pr['po_id']].append(pr)

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'is_po_approve_report': is_po_approve_report(request.user),
        'prs_by_po':prs_by_po,
        'rp_po_page': "tab-active",
        'rp_po_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "report/viewPO.html", context)
```

Replace with (two additions: `po_total_amount` right after the filter is applied, and `kpi_cards` right before `context`):

```python
def viewPOReport(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseOrder.objects.filter(approver_status = 2, branch_company__code__in = company_in, is_cancel = False).distinct() #ใส่ distinct เพราะ filter purchaseorderitem__item__machine ทำให้เบิ้ลรายการตาม items

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs
    po_total_amount = data.aggregate(total=Sum('total_after_discount'))['total'] or 0
    data = data.select_related(
        'cp',
        'credit',
        'distributor',
        'pr',
        'stockman_user',
    )

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    dataPage.object_list = list(dataPage.object_list)

    po_ids = [po.id for po in dataPage.object_list if po.pr_id]
    pr_rows = (
        PurchaseOrderItem.objects
        .filter(
            po_id__in=po_ids,
            item__requisit__pr_ref_no__isnull=False,
        )
        .exclude(item__requisit__pr_ref_no='')
        .values(
            'po_id',
            'item__requisit__pr_ref_no',
            'item__requisit__purchase_requisition_id',
        )
        .distinct()
        .order_by('po_id', 'item__requisit__pr_ref_no')
    )

    prs_by_po = defaultdict(list)
    for pr in pr_rows:
        prs_by_po[pr['po_id']].append(pr)

    kpi_cards = [
        {'label': 'จำนวนรายการทั้งหมด', 'value': dataPage.paginator.count},
        {'label': 'มูลค่ารวม (ตามตัวกรอง)', 'value': po_total_amount, 'sub': 'บาท'},
    ]

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'is_po_approve_report': is_po_approve_report(request.user),
        'prs_by_po':prs_by_po,
        'kpi_cards': kpi_cards,
        'rp_po_page': "tab-active",
        'rp_po_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "report/viewPO.html", context)
```

(`Sum` is already imported at the top of `stock/views.py` — no new import needed.)

- [ ] **Step 2: Restyle the template**

In `stock/templates/report/viewPO.html`, replace:

```html
{% block content %}
<div class="container my-3">
<h3 align="center">สรุปใบสั่งซื้อที่อนุมัติ</h3>
<div class="card my-3 bg-light div-shadow">
  <div class="card-body">
```

with:

```html
{% block content %}
<div class="container my-3">
<h3 align="center">สรุปใบสั่งซื้อที่อนุมัติ</h3>

{% include 'partials/kpi_row.html' %}

<div class="card-stg filter-card my-3">
  <div class="card-body">
```

Then, in the same file, replace:

```html
    <div class="d-flex flex-wrap align-items-center mt-2" style="gap: 0.5rem;">
        <button type="submit" form="po-filter-form" class="btn btn-info">กรอง <i class="fas fa-filter"></i></button>
```

with:

```html
    <div class="d-flex flex-wrap align-items-center mt-2" style="gap: 0.5rem;">
        <button type="submit" form="po-filter-form" class="btn btn-stg">กรอง <i class="fas fa-filter"></i></button>
```

Then replace:

```html
<div class="card div-shadow">
  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-bordered my-3">
        <thead class="table-active">
```

with:

```html
<div class="card-stg">
  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-stg my-3">
        <thead class="table-active">
```

Then replace the row-rendering `<th>` link and the two `text-right` cells:

```html
            <th scope="row"><a class="{% if po.is_re_approve %}text-danger{%endif%}" href="{%url 'showPO' po.id 4 %}">{{po.ref_no}}</a></th>
```

with:

```html
            <th scope="row"><a class="doc-link {% if po.is_re_approve %}text-danger{%endif%}" href="{%url 'showPO' po.id 4 %}">{{po.ref_no}}</a></th>
```

and replace:

```html
            <td class="text-right">{% if po.total_after_discount %}{{po.total_after_discount | intcomma}}{%endif%}</td>
            <td class="text-right">{% if po.vat %}{{po.vat | intcomma}}{%else%}0.00{%endif%}</td>
            <td class="text-right">{% if po.amount %}{{po.amount | intcomma}}{%endif%}</td>
```

with:

```html
            <td class="text-end">{% if po.total_after_discount %}{{po.total_after_discount | intcomma}}{%endif%}</td>
            <td class="text-end">{% if po.vat %}{{po.vat | intcomma}}{%else%}0.00{%endif%}</td>
            <td class="text-end">{% if po.amount %}{{po.amount | intcomma}}{%endif%}</td>
```

Finally, in the pagination block, replace:

```html
        <ul class="pagination justify-content-center">
```

with:

```html
        <ul class="pagination pagination-stg justify-content-center">
```

and replace:

```html
                <span class="sr-only">(current)</span>
```

with:

```html
                <span class="visually-hidden">(current)</span>
```

Every `{{ }}` context variable, `{% url %}` tag, and the `is_po_approve_report`/`is_re_approve` conditionals are unchanged — only class names.

- [ ] **Step 3: Verify**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Start the dev server, navigate to Report → "สรุปใบสั่งซื้อที่อนุมัติ":
- Two KPI cards show above the filter card
- All filter fields (including the newer ones — product ID range, unit price range, distributor ID, category) still submit correctly
- The "กรอง" / Excel export buttons (po/poe/poa download) still work — these use `form="po-filter-form"`, unrelated to the class renames
- Table renders, PO ref links still navigate to `showPO`
- Pagination works

- [ ] **Step 4: Commit**

```bash
git add stock/views.py stock/templates/report/viewPO.html
git commit -m "feat: apply STG Modern design + KPI cards to PO report page"
```

---

### Task 9: Apply the design system to viewPOItem.html (PO item report)

**Files:**
- Modify: `stock/views.py:5136-5158` (`viewPOItemReport` — match by the code content shown below, not this line range; Task 8's edit shifts everything after `viewPOReport` down by a few lines)
- Modify: `stock/templates/report/viewPOItem.html`

**Interfaces:**
- Consumes: `partials/kpi_row.html` (Task 6), `.card-stg`/`.filter-card`/`.table-stg`/`.doc-link`/`.pagination-stg`/`.btn-stg` (Task 5).
- Produces: `kpi_cards` = `[{'label': 'จำนวนรายการทั้งหมด', 'value': <int>}, {'label': 'มูลค่ารวม (ตามตัวกรอง)', 'value': <Decimal>, 'sub': 'บาท'}]`.

- [ ] **Step 1: Add KPI data to the view**

In `stock/views.py`, `viewPOItemReport` currently reads:

```python
def viewPOItemReport(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseOrderItem.objects.filter(po__approver_status = 2, po__branch_company__code__in = company_in, po__is_cancel = False).order_by('-po__created')

    #กรองข้อมูล
    myFilter = PurchaseOrderItemFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
        'po_item':dataPage,
        'filter':myFilter,
        'rp_poi_page': "tab-active",
        'rp_poi_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "report/viewPOItem.html", context)
```

Replace with:

```python
def viewPOItemReport(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseOrderItem.objects.filter(po__approver_status = 2, po__branch_company__code__in = company_in, po__is_cancel = False).order_by('-po__created')

    #กรองข้อมูล
    myFilter = PurchaseOrderItemFilter(request.GET, queryset = data)
    data = myFilter.qs
    poi_total_amount = data.aggregate(total=Sum('price'))['total'] or 0

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    kpi_cards = [
        {'label': 'จำนวนรายการทั้งหมด', 'value': dataPage.paginator.count},
        {'label': 'มูลค่ารวม (ตามตัวกรอง)', 'value': poi_total_amount, 'sub': 'บาท'},
    ]

    context = {
        'po_item':dataPage,
        'filter':myFilter,
        'kpi_cards': kpi_cards,
        'rp_poi_page': "tab-active",
        'rp_poi_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "report/viewPOItem.html", context)
```

- [ ] **Step 2: Restyle the template**

In `stock/templates/report/viewPOItem.html`, replace:

```html
{% block content %}
<div class="container my-3">
<h3 align="center">รายงานตามสินค้าที่สั่งซื้อ</h3>
<div class="card my-3 bg-light div-shadow">
  <div class="card-body">
```

with:

```html
{% block content %}
<div class="container my-3">
<h3 align="center">รายงานตามสินค้าที่สั่งซื้อ</h3>

{% include 'partials/kpi_row.html' %}

<div class="card-stg filter-card my-3">
  <div class="card-body">
```

Then replace the filter submit button:

```html
              <button type="submit" class="btn btn-info">กรอง<i class="fas fa-filter"></i></button>
```

with:

```html
              <button type="submit" class="btn btn-stg">กรอง<i class="fas fa-filter"></i></button>
```

Then replace the results card + table + header:

```html
<div class="card div-shadow">
  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-bordered my-3">
        <thead class="table-active">
```

with:

```html
<div class="card-stg">
  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-stg my-3">
        <thead class="table-active">
```

Then replace the unit-price cell and the requisit/PR/CP/PO links:

```html
            <td class="text-right">{{item.unit_price | intcomma}}</td>
            <th scope="row">
              <ul>
                <li><a href="{% url 'showRequisition' item.item.requisit.id 4 %}">{{item.item.requisit.ref_no}}</a></li>
                <li><a href="{% url 'showPR' item.item.requisit.purchase_requisition_id 4 %}">{{item.item.requisit.pr_ref_no}}</a></li>
                {% if item.po.cp.ref_no %}<li><a class="{% if item.po.cp.is_re_approve %}text-danger{%endif%}" href="{%url 'showComparePricePO' item.po.cp.id 4 %}">{{item.po.cp.ref_no}}</a></li>{%endif%}
                <li><a class="{% if item.po.is_re_approve %}text-danger{%endif%}" href="{%url 'showPO' item.po.id 4 %}">{{item.po.ref_no}}</a></li>
              </ul>
            </th>
```

with:

```html
            <td class="text-end">{{item.unit_price | intcomma}}</td>
            <th scope="row">
              <ul>
                <li><a class="doc-link" href="{% url 'showRequisition' item.item.requisit.id 4 %}">{{item.item.requisit.ref_no}}</a></li>
                <li><a class="doc-link" href="{% url 'showPR' item.item.requisit.purchase_requisition_id 4 %}">{{item.item.requisit.pr_ref_no}}</a></li>
                {% if item.po.cp.ref_no %}<li><a class="doc-link {% if item.po.cp.is_re_approve %}text-danger{%endif%}" href="{%url 'showComparePricePO' item.po.cp.id 4 %}">{{item.po.cp.ref_no}}</a></li>{%endif%}
                <li><a class="doc-link {% if item.po.is_re_approve %}text-danger{%endif%}" href="{%url 'showPO' item.po.id 4 %}">{{item.po.ref_no}}</a></li>
              </ul>
            </th>
```

Finally, in the pagination block, replace:

```html
        <ul class="pagination justify-content-center">
```

with:

```html
        <ul class="pagination pagination-stg justify-content-center">
```

and replace:

```html
                <span class="sr-only">(current)</span>
```

with:

```html
                <span class="visually-hidden">(current)</span>
```

- [ ] **Step 3: Verify**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Start the dev server, navigate to Report → "รายงานตามสินค้าที่สั่งซื้อ":
- Two KPI cards show above the filter card
- All filter fields still submit correctly (PO ref, product ID range, name, unit price range, distributor, stockman, category, machine, note, PR ref, CP ref, date range)
- The three Excel export buttons (sp/sf/df) still work
- Table renders, all 4 link types (requisition/PR/CP/PO) still navigate correctly
- Pagination works

- [ ] **Step 4: Commit**

```bash
git add stock/views.py stock/templates/report/viewPOItem.html
git commit -m "feat: apply STG Modern design + KPI cards to PO item report page"
```

---

### Task 10: Phase 1 final verification sweep

**Files:** none (verification only)

- [ ] **Step 1: Confirm no Bootstrap-4-only classes remain in the touched files**

Run:
```bash
grep -rE "\bthead-dark\b|\bthead-light\b|\bsr-only\b|\btext-left\b|\btext-right\b|\bfloat-left\b|\bfloat-right\b|\bml-[0-9]|\bmr-[0-9]|\bpl-[0-9]|\bpr-[0-9]|badge-pill|badge-warning|badge-dark|div-shadow" \
  stock/templates/layouts.html stock/templates/navbar.html stock/templates/sidebar.html \
  stock/templates/express/viewExOiInvoice.html stock/templates/report/viewPO.html stock/templates/report/viewPOItem.html
```
Expected: no output (no matches) — everything in these 6 files was accounted for in Tasks 1–9. (`div-shadow` is expected to be gone from the 3 representative pages since `.card-stg` replaces it; it may still exist elsewhere in the codebase, which is fine — out of Phase 1 scope.)

- [ ] **Step 2: Full project sanity check**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `python manage.py makemigrations --check --dry-run`
Expected: `No changes detected` — confirms no model was accidentally touched.

- [ ] **Step 3: End-to-end manual walkthrough**

With the dev server running and logged in:
1. Sidebar collapse toggle, company tab switching, search — all work as before (jQuery untouched)
2. Any page NOT in Phase 1 scope (e.g. `viewRequisition` or `viewMA`) still opens, its dropdowns/tabs still work (proves the Task 1 sweep didn't miss anything on unmigrated pages) — spot check 2–3 pages
3. The 3 representative pages show the new look with working KPI cards, filters, tables, pagination, and exports

- [ ] **Step 4: Update the design spec status**

In `docs/superpowers/specs/2026-08-03-bootstrap5-ui-redesign-design.md`, no changes needed — the spec already scopes this to Phase 1. (Later phases get their own spec when the user is ready to continue the rollout.)
