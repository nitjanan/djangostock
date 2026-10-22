# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Internal procurement / stock / fleet-maintenance system for a group of Thai companies (Django 4.2, Python 3.9). UI text, model `verbose_name`s, group names, status values and most comments are in **Thai** — keep new code consistent with that. Single Django app: `stock`. Project package: `djangostock`.

## Commands

The venv lives in `.venv` (Windows). Local DB is MySQL/MariaDB `djangostockdb` on localhost as `root` with an empty password (see `djangostock/settings.py`).

```bash
.venv/Scripts/python manage.py runserver
.venv/Scripts/python manage.py makemigrations stock
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py test stock                                   # all tests
.venv/Scripts/python manage.py test stock.tests_ma_approve                  # one module
.venv/Scripts/python manage.py test stock.tests.PurchaseOrderItemDoubleSubmitTestCase   # one class
.venv/Scripts/python manage.py test stock.tests_ma_approve.MAApproveNoteTestCase.test_approve_saves_note
```

There is no linter/formatter configured. Deployment is Heroku-style (`Procfile`: gunicorn + `release: migrate`, `runtime.txt`).

## Architecture

### Code layout (big files)
- `stock/views.py` (~12.6k lines) holds essentially all views — function-based views, DRF API views, Excel/report exports (pandas, openpyxl, xlwt, tablib). Search it with Grep rather than reading top to bottom.
- `stock/models.py` — all models. `Base*` models are lookup/master tables (company, unit, car, approve status, PO type, …). Most models set explicit `db_table`.
- `stock/context_processors.py` — ~15 context processors registered in settings that compute sidebar badge counters (pending PR/PO/CP/MA approvals, etc.) and visible tabs on **every** request. Changes to approval logic usually need matching changes here so counters stay correct.
- `stock/filters.py` (django-filter), `stock/forms.py` (crispy-forms + Select2), `stock/admin.py` (import-export, related-admin).
- `djangostock/urls.py` — single flat URL conf for the whole app (no per-app `urls.py`).
- Templates in `stock/templates/<feature>/`, base layout `layouts.html`, `navbar.html`, `sidebar.html`.
- `stock/migrations_old/` is a dead archive; real migrations are in `stock/migrations/`.

### Document workflow
The core domain is a chain of documents, each with its own `*_ref_number()` generator in `models.py` (per branch company, date-based):

Requisition (ใบขอเบิก) → PurchaseRequisition / PR (ใบขอซื้อ) → ComparisonPrice / CP (ใบเปรียบเทียบราคา, with `ComparisonPriceDistributor` bidders) → PurchaseOrder / PO (ใบสั่งซื้อ) → Receive (รับของ) → Invoice; plus RateDistributor (supplier rating tied to a PO), Maintenance / MA (ซ่อมบำรุง) and CarLogbook (fleet log, anomaly detection in `carlog_anomaly.py`).

A PO can originate from a PR or from a CP; several rules differ by origin (e.g. a PO created from a CP inherits its approver from the CP and the approver cannot be edited — see `can_edit_approver_user_po` in `views.py`). Approval statuses are rows of `BaseApproveStatus` looked up **by Thai name** (e.g. `BaseApproveStatus.objects.get(name=post_status)`), and some models store the status as a Thai string directly (e.g. `Maintenance.approve_status`).

### Multi-company scoping
- On login the selected branch company is stored in `request.session['company_code']` (and `'company'`). Almost every view filters by `request.session.get('company_code', 'ALL')`.
- `stock.middleware.RequireCompanyCodeMiddleware` logs out any authenticated user whose session lacks `company_code`. **Tests must set `session['company_code']` after `client.login()`** or requests redirect to sign-in.
- `UserProfile` (one-to-one with `User`) holds position, department, signature, visible tabs (`BaseVisible`) and visible companies.

### Permissions — two parallel systems
1. **Django groups with Thai/English names**, checked via helpers `is_purchasing` (`'จัดซื้อ'`), `is_supplies` (`'พัสดุ'`), `is_view_report_all`, `is_edit_pr`, etc. in `views.py`.
2. **`PositionBasePermission`**: position → `BasePermission` (by `codename`, e.g. `CAAPR` approve PR, `CAAPO` approve PO, `CAACP1..4/D/A` approve CP, `CAECP*`) scoped per `branch_company`. CP approval permissions also carry `ap_amount_min`/`ap_amount_max` amount bands. Approver lookups go through `user.userprofile.position`.

### Second database: Express (read-only)
`DATABASES['pg_db']` is a remote PostgreSQL (Express accounting system). Models `ExOESTNH/ExOESTND/ExOEINVH/ExOEINVD/ExAPTRNH` are `managed = False` and must be queried with `.objects.using('pg_db')`. Used for spare-part/fuel issue and invoice data in maintenance and car-log reports. Tests should avoid code paths that hit `pg_db`.

### APIs
DRF + SimpleJWT (`jwt/refresh/`, `jwt/verify/`, `login/api/`), PO read APIs under `po/api/...`, and AppSheet integration endpoints under `api/*_appsheet/` (`serializers.py`).

## Testing gotchas

- Tests run against MySQL/MariaDB (test DB created from `default`). MariaDB does **not** reset AUTO_INCREMENT between `TestCase` transactions, so tests must not rely on implicit PKs. `CreatePOFromComparisonPriceTestCase` in `stock/tests.py` is order-fragile for this reason — put new DB-touching test classes in a separate `stock/tests_<feature>.py` module rather than adding them to `stock/tests.py`.
- `STATICFILES_STORAGE` is `CompressedManifestStaticFilesStorage`; tests run with `DEBUG=False` and no `collectstatic`, so any test that renders a template referencing `{% static %}` can fail with "Missing staticfiles manifest entry". Prefer asserting on redirects / DB state, or exercise code paths that redirect.
- `settings.py` reassigns `SECRET_KEY` near the bottom (the Stripe block) — the effective Django `SECRET_KEY` is not the one at the top, while `SIMPLE_JWT['SIGNING_KEY']` captured the earlier value.

## Design docs

Feature specs/plans are kept in `docs/superpowers/specs/` and `docs/superpowers/plans/` (dated filenames).
