# All-Details Procurement Report — Design

**Date:** 2026-08-31
**Branch:** feature/search-all-rq-pr-cm-po
**Status:** Approved design, pending implementation plan

## Goal

Add a new report page that lists the full procurement chain in one searchable,
paginated table with a compact dashboard on top, rendered into the currently
empty `stock/templates/report/viewAllDetails.html`.

Chain (conceptual):

```
Requisition → RequisitionItem → PurchaseRequisition → ComparisonPrice →
ComparisonPriceItem → ComparisonPriceDistributor → PurchaseOrder → PurchaseOrderItem
```

## Context / findings

- `viewAllDetails.html` is a new empty file. There is **no** existing view, URL,
  nav-tabs, JS, or CSS for it. This is a new page, not an enhancement of
  existing behaviour. The "nav-tabs" in the original task refers to the shared
  company selector in `navbar.html`; the dashboard simply goes at the top of the
  `{% block content %}`.
- It belongs in the **report** section: templates under `templates/report/`,
  submenu `reportSubmenu` in `sidebar.html`, routes under `report/` in
  `djangostock/urls.py`. Sibling views: `viewPOReport`, `viewPOItemReport`,
  `viewRateDistributorReport`, `viewCLReport`.
- Sibling report views share a pattern:
  `active = request.session.get('company_code', 'ALL')` →
  `company_in = findCompanyIn(request)` → base queryset filtered by
  `branch_company__code__in=company_in` → django-filter `FilterSet` →
  `Paginator(data, N)` → context flags `*_page: "tab-active"`,
  `*_show: "show"`, `active: "active show"`, `"colorNav": "enableNav"`.
  Pagination in templates uses the `{% my_url %}` tag with
  `request.GET.urlencode` to preserve filters across pages.
- Report views have **no per-view permission decorator**; access is governed by
  sidebar visibility / middleware. This design matches that (decision: "match
  existing report views").

## Actual model relationships (as-built)

| From | Field | To | Notes |
|---|---|---|---|
| `RequisitionItem` | `.requisit` (FK) | `Requisition` | real link. `requisition_id` IntegerField is dead, ignore it |
| `PurchaseRequisition` | `.requisition` (FK) | `Requisition` | PR attaches to the Requisition, not to the item. Reverse: `requisition.purchaserequisition_set` |
| `ComparisonPriceItem` | `.item` (FK) | `RequisitionItem` | reverse: `requisitionitem.comparisonpriceitem_set` |
| `ComparisonPriceItem` | `.bidder` (FK) | `ComparisonPriceDistributor` | |
| `ComparisonPriceItem` | `.cp` | — | bare IntegerField (no FK). Populated and queried elsewhere in the codebase, but this feature deliberately does not use it: it routes to `ComparisonPrice` through `bidder.cp`, the real FK, which has no referential-integrity gap. |
| `ComparisonPriceDistributor` | `.cp` (FK) | `ComparisonPrice` | `.is_select` BooleanField marks chosen bidder |
| `PurchaseOrder` | `.cp` (FK, nullable) | `ComparisonPrice` | |
| `PurchaseOrder` | `.pr` (FK, nullable) | `PurchaseRequisition` | |
| `PurchaseOrder` | `.approver_status` (FK) | `BaseApproveStatus` | |
| `PurchaseOrderItem` | `.po` (FK) | `PurchaseOrder` | reverse: `requisitionitem`... via `.item` |
| `PurchaseOrderItem` | `.item` (FK) | `RequisitionItem` | reverse: `requisitionitem.purchaseorderitem_set` |

Spine = **`RequisitionItem`**. Every downstream stage links back to it. The CP
reference for a row is reached via `comparisonpriceitem.bidder.cp`.
There is no direct `ComparisonPrice → PurchaseRequisition` FK; they only meet at
`PurchaseOrder`.

## Decisions

1. **Row granularity:** one row per `RequisitionItem`, fanning out on the deepest
   stage reached — one row per `PurchaseOrderItem` if any exist; else one row per
   `ComparisonPriceItem`; else a single bare row. Missing stages render `-`.
   Incomplete chains are never dropped.
2. **Scoping:** match existing report views — company scope via `findCompanyIn`,
   no new decorator, CSRF preserved (GET form + `{% csrf_token %}`).
3. **Dashboard counts:** reflect the current filter (computed on the filtered
   queryset before pagination), labelled as filtered ("ตามการกรอง").
4. **Actions:** reuse existing `show*` pages, plus a vanilla-JS inline expand row
   showing the full chain trace.

## Files changed

| File | Change |
|---|---|
| `djangostock/urls.py` | `path('report/all/details/', views.viewAllDetailsReport, name='viewAllDetailsReport')` near the other `report/` routes (~line 170) |
| `stock/views.py` | new `viewAllDetailsReport(request)` |
| `stock/filters.py` | new `AllDetailsFilter(django_filters.FilterSet)` on `RequisitionItem` + label assignments (repo style) |
| `stock/templates/report/viewAllDetails.html` | dashboard + filter form + table + `{% my_url %}` pagination + expand JS |
| `stock/templates/sidebar.html` | new `<li>` in `reportSubmenu`; add `rp_all_page` to the submenu `aria-expanded` condition |
| `stock/tests_all_details_report.py` | new test file (kept separate per repo test-isolation note) |

No model changes. **No migration.**

## View design — `viewAllDetailsReport(request)`

```
active = request.session.get('company_code', 'ALL')
company_in = findCompanyIn(request)

base = (RequisitionItem.objects
        .filter(requisit__branch_company__code__in=company_in)
        .select_related('requisit', 'requisit__name', 'product'))

myFilter = AllDetailsFilter(request.GET, queryset=base)
qs = myFilter.qs.distinct()

# dashboard counts — on qs, pre-pagination
dashboard = {
  'requisitions':       qs.values('requisit').distinct().count(),
  'requisition_items':  qs.count(),
  'purchase_reqs':      PurchaseRequisition.objects
                          .filter(requisition__requisitionitem__in=qs).distinct().count(),
  'comparison_prices':  ComparisonPriceDistributor.objects
                          .filter(comparisonpriceitem__item__in=qs)
                          .values('cp').distinct().count(),
  'comparison_items':   ComparisonPriceItem.objects.filter(item__in=qs).count(),
  'distributors':       ComparisonPriceDistributor.objects
                          .filter(comparisonpriceitem__item__in=qs)
                          .values('distributor').distinct().count(),
  'purchase_orders':    PurchaseOrder.objects
                          .filter(purchaseorderitem__item__in=qs).distinct().count(),
  'po_items':           PurchaseOrderItem.objects.filter(item__in=qs).count(),
}

p = Paginator(qs, 25)
page = request.GET.get('page')
dataPage = p.get_page(page)
dataPage.object_list = list(dataPage.object_list)
ids = [ri.id for ri in dataPage.object_list]

poi = (PurchaseOrderItem.objects.filter(item_id__in=ids)
        .select_related('po', 'po__cp', 'po__pr', 'po__distributor', 'po__approver_status', 'unit')
        .order_by('id'))
cpi = (ComparisonPriceItem.objects.filter(item_id__in=ids)
        .select_related('bidder', 'bidder__distributor', 'bidder__cp', 'unit')
        .order_by('id'))
prs = (PurchaseRequisition.objects
        .filter(requisition__requisitionitem__id__in=ids)
        .select_related('requisition').order_by('id'))

# group poi/cpi by item_id, prs by requisition_id; assemble `rows`:
#   for ri in dataPage.object_list:
#     item_pois = poi_by_item[ri.id]
#     item_cpis = cpi_by_item[ri.id]
#     item_prs  = prs_by_req[ri.requisit_id]
#     if item_pois:  one Row per po item (each carries its po, po.cp, po.distributor,
#                    and the matching cp item if resolvable via same RequisitionItem)
#     elif item_cpis: one Row per cp item (carries bidder, bidder.cp, bidder.distributor)
#     else:          one bare Row (requisition + item + prs only)

context = {
  'rows': rows,
  'page_obj': dataPage,
  'filter': myFilter,
  'dashboard': dashboard,
  'rp_all_page': "tab-active",
  'rp_all_show': "show",
  active: "active show",
  "colorNav": "enableNav",
}
return render(request, "report/viewAllDetails.html", context)
```

`Row` is a lightweight dict/namedtuple with keys: `requisition`, `item`,
`purchase_reqs` (list), `comparison_price`, `comparison_item`, `distributor`,
`is_selected_distributor`, `purchase_order`, `po_item`, `stage`, `amount`,
`created`.

- **`stage`** derived: `PO` if `purchase_order` else `CP` if `comparison_item`
  else `PR` if `purchase_reqs` else `RQ`.
- **`amount`** = `po_item.price` if PO row, else `comparison_item.price` if CP
  row, else `None`.

Query budget: 1 (paginator count) + 1 (page) + 3 (poi/cpi/prs) + 8 (dashboard)
+ small overhead ≈ 15, independent of page size. Test pins an upper bound.

## `AllDetailsFilter` (model = `RequisitionItem`)

Global:

- `search` — `CharFilter(method='filter_search')`, OR via `Q`, result `.distinct()`:
  - `requisit__ref_no`, `requisit__pr_ref_no`
  - `product_name`, `product__id`, `machine`, `description`
  - `requisit__name__first_name`, `requisit__name__last_name`
  - `comparisonpriceitem__bidder__cp__ref_no`
  - `comparisonpriceitem__bidder__distributor__name`
  - `purchaseorderitem__po__ref_no`
  - `purchaseorderitem__po__cp__ref_no`
  - `purchaseorderitem__po__pr__ref_no`
  - `purchaseorderitem__po__distributor__name`

Field filters:

| Filter | Field / method | Lookup |
|---|---|---|
| `rq_ref_no` | `requisit__ref_no` | icontains |
| `pr_ref_no` | method: `requisit__pr_ref_no` OR `purchaseorderitem__po__pr__ref_no` | icontains |
| `cp_ref_no` | method: `comparisonpriceitem__bidder__cp__ref_no` OR `purchaseorderitem__po__cp__ref_no` | icontains |
| `po_ref_no` | `purchaseorderitem__po__ref_no` | icontains |
| `requester` | `ModelChoiceFilter` on `requisit__name`, queryset `User.objects.all()` | exact |
| `product_name` | `product_name` | icontains |
| `product_id` | `product__id` | exact/startswith |
| `machine` | `machine` | icontains |
| `description` | `description` | icontains |
| `distributor` | method: `comparisonpriceitem__bidder__distributor__name` OR `purchaseorderitem__po__distributor__name` | icontains |
| `quantity_min` / `quantity_max` | `quantity` | gte / lte |
| `amount_min` / `amount_max` | `purchaseorderitem__price` | gte / lte |
| `start_created` / `end_created` | `requisit__created`, `DateInput(type=date)` | gte / lte |
| `stage` | `ChoiceFilter(method)` — `PR` (has purchaserequisition), `CP` (has comparisonpriceitem), `PO` (has purchaseorderitem) | Exists-based |
| `po_status` | `purchaseorderitem__po__approver_status` | exact |

All method filters call `.distinct()`. Thai labels assigned in the module body
following the `RequisitionFilter.base_filters[...] .label` convention.

## Template — `report/viewAllDetails.html`

- `{% extends 'layouts.html' %}`, loads `static crispy_forms_tags templatehelpers humanize`.
- `<div class="container my-3">`, `<h3 align="center">รายละเอียดการจัดซื้อทั้งหมด</h3>`.
- **Dashboard:** `<div class="row">` of 8 `<div class="col-6 col-md-3 mb-2">` cards
  (Bootstrap 4 `.card` + `.div-shadow` like siblings). Each card: label + count.
  A small caption states the counts follow the current filter.
  Responsive: 2-up on mobile (`col-6`), 4-up from `md`.
- **Filter panel:** `<form method="get">` + `{% csrf_token %}`, `.form-row` of
  `.form-group.col-md-2` crispy fields (mirrors `viewPOItem.html`). Global
  `search` field spans wider. Submit button `กรอง` + a `ล้าง` (reset) link
  pointing at the bare `{% url 'viewAllDetailsReport' %}`.
- **Table:** `.table-responsive` > `.table.table-bordered`. Columns:
  ใบขอเบิก · รายการ · ใบขอซื้อ · ใบเปรียบเทียบ · รายการเปรียบเทียบ · ร้านค้า ·
  ใบสั่งซื้อ · รายการสั่งซื้อ · ขั้นตอน · จำนวนเงิน · วันที่ · จัดการ.
  - Ref cells link to `show*` with mode arg `4`:
    `{% url 'showRequisition' row.requisition.id 4 %}`,
    `{% url 'showPR' pr.id 4 %}` (loop `row.purchase_reqs`),
    `{% url 'showComparePricePO' row.comparison_price.id 4 %}`,
    `{% url 'showPO' row.purchase_order.id 4 %}`.
  - Missing stage → `-`.
  - Distributor cell shows a check/badge when `row.is_selected_distributor`.
  - `ขั้นตอน` renders `row.stage` as a Bootstrap badge (reuse existing badge
    classes; RQ/PR/CP/PO colour ramp).
  - `จัดการ`: a `ดูสายงาน` button toggling a hidden detail `<tr>` (JS below).
- **Expand row:** hidden `<tr class="chain-detail">` per row, rendered inline,
  showing the vertical trace
  `REQ ref → PR ref(s) → CP ref → ร้านค้า → PO ref → PO item` with the same
  `show*` links. Toggled by a small vanilla-JS listener in `{% block javascript %}`
  (no framework; pattern like `viewPOItem.html`'s script block).
- **Empty state:** when `rows` is empty, a single full-width row:
  "ไม่พบข้อมูล ลองปรับเงื่อนไขการค้นหาหรือการกรอง".
- **Pagination:** copy the sibling `{% my_url %}` pagination `<nav>` block
  verbatim, using `page_obj` and `request.GET.urlencode` so filter state
  survives page changes.

## Sidebar

In `reportSubmenu` (`sidebar.html`), add:

```html
<li>
  <a class="{{ rp_all_page }}" href="{% url 'viewAllDetailsReport' %}">รายละเอียดการจัดซื้อทั้งหมด</a>
</li>
```

and add `rp_all_page` to the parent `<a ... aria-expanded="{% if rp_po_page or rp_poi_page or rp_rd_page or rp_cl_page or rp_all_page %}true{% else %}false{% endif %}">` condition.

## Tests — `stock/tests_all_details_report.py`

New `TestCase` (own file per the repo's PK-drift test-isolation note). A
`setUp`/helper builds base rows (`BaseBranchCompany`, `BaseApproveStatus`,
`User`, `Product`, `Requisition`, ...) then scenario fixtures.

| Test | Assertion |
|---|---|
| page loads | `GET` name `viewAllDetailsReport` → 200, template `report/viewAllDetails.html` used |
| dashboard counts | context `dashboard` values match a hand-built fixture |
| full chain row | a RequisitionItem with PR + CP item + selected distributor + PO item → row shows every stage ref, `stage == 'PO'` |
| partial chain row | RequisitionItem with Requisition + PR only (no CP/CP item/PO) → still present, CP/PO cells `-`, `stage == 'PR'` |
| requisition-only row | RequisitionItem with no PR/CP/PO → present, `stage == 'RQ'` |
| search — each ref | `?search=<rq/pr/cp/po ref>`, `?search=<distributor name>`, `?search=<product name>` each return the expected row |
| filters | `stage`, `start_created`/`end_created`, `distributor`, `po_status`, `product_id` each narrow correctly |
| pagination | 30 items → page 1 has 25 rows, `?page=2` has 5; `?search=x&page=2` keeps `search` in `page_obj` links (assert `my_url` output contains `search=x`) |
| fan-out / no dupes | one RequisitionItem on 2 PurchaseOrderItems → exactly 2 rows for it; one on 1 PO item is not duplicated by CP-item joins |
| company scope | item under another `branch_company` not returned for a session scoped elsewhere |
| query budget | `with self.assertNumQueries(<=N)` around the list view for a multi-row page (N pinned once implementation settles, target ~15–18) |

## Non-goals / constraints

- No model changes, no migration.
- No new data endpoints beyond the one HTML view; no client-side filtering of the
  full dataset.
- Do not alter sibling report views, existing URLs, or existing templates other
  than the one `sidebar.html` submenu addition.
- Existing `show*` detail pages are reused; no new detail pages.
