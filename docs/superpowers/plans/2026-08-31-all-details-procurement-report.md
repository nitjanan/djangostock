# All-Details Procurement Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new report page at `report/all/details/` that renders the full
Requisition→PurchaseOrderItem procurement chain as one searchable, filtered,
paginated table with a compact 8-count dashboard on top.

**Architecture:** A single Django function view (`viewAllDetailsReport`) anchored
on `RequisitionItem`, company-scoped like the sibling report views. A
`django_filters.FilterSet` (`AllDetailsFilter`) provides a global `search` plus
field filters. The view paginates the filtered `RequisitionItem` queryset (25
per page), then in Python fans each item out into one display row per
`PurchaseOrderItem` (else per `ComparisonPriceItem`, else one bare row), so
incomplete chains still appear. Dashboard counts are computed on the filtered
queryset before pagination. The template extends `layouts.html` and reuses the
existing `{% my_url %}` pagination block and `show*` detail pages.

**Tech Stack:** Django (function views, `django-filter`, `Paginator`),
Bootstrap 4 templates, `crispy_forms`, vanilla JS for the row expander.

**Spec:** `docs/superpowers/specs/2026-08-31-all-details-procurement-report-design.md`

## Global Constraints

- No model changes. **No migration.** If a migration seems required, stop and re-check.
- Company scoping: `company_in = findCompanyIn(request)`; base queryset filtered
  by `requisit__branch_company__code__in=company_in`. No new permission decorator
  (matches `viewPOReport` / `viewPOItemReport`).
- `findCompanyIn` calls `UserProfile.objects.get(user=request.user.id)` — every
  test that hits the view MUST create a `UserProfile` for its user and set
  `session['company_code']` to a concrete branch code (not `'ALL'`).
- Pagination: `Paginator(qs, 25)`. Pagination unit = `RequisitionItem`. Template
  pagination uses the sibling `{% my_url %}` block with `request.GET.urlencode`
  so filters survive page changes.
- Context flags required by the shared layout/sidebar: `'rp_all_page': "tab-active"`,
  `'rp_all_show': "show"`, `active: "active show"` (where
  `active = request.session.get('company_code', 'ALL')`), `"colorNav": "enableNav"`.
- New DB-touching tests go in their **own** `stock/tests_all_details_report.py`
  module (never added to `stock/tests.py`) — per the repo's PK-drift
  test-isolation note.
- Model facts to rely on (verified): `RequisitionItem.requisit` FK→`Requisition`;
  `RequisitionItem.requisition_id` is a **required** bare `IntegerField` (pass it
  in tests, otherwise ignore it); `RequisitionItem.machine` is a `CharField`.
  `PurchaseRequisition.requisition` FK→`Requisition`.
  `ComparisonPriceItem.item` FK→`RequisitionItem`, `.bidder` FK→`ComparisonPriceDistributor`,
  `.cp` is an unused bare `IntegerField`.
  `ComparisonPriceDistributor.cp` FK→`ComparisonPrice`, `.is_select` bool.
  `PurchaseOrder.cp` / `.pr` nullable FKs; `.approver_status` FK→`BaseApproveStatus`.
  `PurchaseOrderItem.po` FK→`PurchaseOrder`, `.item` FK→`RequisitionItem`.
  `Product.id` and `Distributor.id` are `CharField` PKs.
- `Requisition`, `PurchaseRequisition`, `ComparisonPrice`, `PurchaseOrder` all run
  an `address_company` auto-lookup in `save()` that raises if no
  `BranchCompanyBaseAdress` exists — tests MUST pass `address_company=` explicitly.
  `ComparisonPrice`/`PurchaseOrder` also auto-generate `ref_no` when `None` — tests
  MUST pass `ref_no=` explicitly.

---

## File Structure

| File | Responsibility |
|---|---|
| `djangostock/urls.py` | one route: `report/all/details/` → `viewAllDetailsReport`, name `viewAllDetailsReport` |
| `stock/filters.py` | `AllDetailsFilter` (FilterSet on `RequisitionItem`) + Thai label assignments |
| `stock/views.py` | `viewAllDetailsReport(request)` — scoping, filter, dashboard counts, pagination, row assembly, render |
| `stock/templates/report/viewAllDetails.html` | dashboard cards, filter form, table, expand rows, `{% my_url %}` pagination, empty state |
| `stock/templates/sidebar.html` | one `<li>` in `reportSubmenu` + add `rp_all_page` to the submenu `aria-expanded` condition |
| `stock/tests_all_details_report.py` | new `TestCase` with a `_build_chain` fixture helper and all scenario tests |

---

## Task 1: Route, view skeleton, template stub, sidebar link, test fixture

**Files:**
- Modify: `djangostock/urls.py` (add one `path(...)` near the other `report/` routes, ~line 170)
- Modify: `stock/views.py` (add `viewAllDetailsReport` — place it next to `viewPOItemReport`, ~line 5168)
- Create: `stock/templates/report/viewAllDetails.html`
- Modify: `stock/templates/sidebar.html` (`reportSubmenu`)
- Create: `stock/tests_all_details_report.py`

**Interfaces:**
- Produces:
  - URL name `viewAllDetailsReport` (no args), path `report/all/details/`.
  - `stock.views.viewAllDetailsReport(request) -> HttpResponse` rendering
    `report/viewAllDetails.html`.
  - Context keys (this task): `rows` (list, empty for now), `page_obj`
    (`Paginator(qs, 25).get_page(...)`), `filter` (a `FilterSet`-like or `None`
    for now — real one arrives in Task 2), `dashboard` (dict of 8 ints, all `0`
    for now), plus the four layout flags from Global Constraints.
  - `stock/tests_all_details_report.py::AllDetailsReportTests` with classmethod
    helper `_build_chain(cls, *, code="HO", stage="PO", **overrides) -> dict`
    (see Step 1) that later tasks reuse.

- [ ] **Step 1: Write the failing test — page loads with empty DB**

Create `stock/tests_all_details_report.py`:

```python
from decimal import Decimal
import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from stock.models import (
    UserProfile, BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress,
    BaseVatType, BaseUnit, BaseApproveStatus, Category,
    Product, Distributor, Requisition, RequisitionItem, PurchaseRequisition,
    ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor,
    PurchaseOrder, PurchaseOrderItem,
)

URL_NAME = "viewAllDetailsReport"


class AllDetailsReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.other_branch = BaseBranchCompany.objects.create(id="2", code="BR", name="Branch")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        # Satisfy the address_company auto-lookup in model .save() for both branches.
        BranchCompanyBaseAdress.objects.create(branch_company=cls.branch, address=cls.address)
        BranchCompanyBaseAdress.objects.create(branch_company=cls.other_branch, address=cls.address)
        cls.vat = BaseVatType.objects.create(id="1", name="VAT 7%")
        cls.unit = BaseUnit.objects.create(name="ชิ้น")
        cls.status_approved = BaseApproveStatus.objects.create(name="อนุมัติ")
        cls.category = Category.objects.create(name="Cat", slug="cat")

        cls.user = User.objects.create_user(username="reporter", password="pw")
        profile = UserProfile.objects.create(user=cls.user)
        profile.branch_company.add(cls.branch, cls.other_branch)

        cls.requester = User.objects.create_user(username="req_user", password="pw",
                                                 first_name="Somchai", last_name="Jaidee")
        cls.approver = User.objects.create_user(username="appr_user", password="pw")

    def setUp(self):
        self.client = Client()
        self.client.login(username="reporter", password="pw")
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    # ----- fixture helper reused by later tasks -----
    @classmethod
    def _build_chain(cls, *, code="HO", stage="PO", product_code="P001",
                     product_name="Computer", distributor_name="ABC Company",
                     rq_ref="REQ-2026-001", pr_ref="PR-00125", cp_ref="CP-0007",
                     po_ref="PO-0056", qty="2.0000", price="1000.00", n_po_items=1):
        """Build a procurement chain up to `stage` in {'RQ','PR','CP','PO'}.
        Returns a dict of the created objects."""
        branch = BaseBranchCompany.objects.get(code=code)
        product = Product.objects.create(id=product_code, name=product_name + " " + product_code,
                                         slug="slug-" + product_code, category=cls.category)
        distributor = Distributor.objects.create(id="D-" + product_code, name=distributor_name)

        rq = Requisition.objects.create(
            name=cls.requester, chief_approve_user_name=cls.approver,
            supplies_approve_user_name=cls.approver, branch_company=branch,
            address_company=cls.address, ref_no=rq_ref, pr_ref_no=pr_ref,
        )
        item = RequisitionItem.objects.create(
            requisition_id=rq.id, requisit=rq, product=product,
            product_name=product_name, machine="MC-1", description="desc",
            quantity=Decimal(qty),
        )
        out = {"branch": branch, "product": product, "distributor": distributor,
               "rq": rq, "item": item, "pr": None, "cp": None, "cpd": None,
               "cpi": None, "po": None, "po_items": []}
        if stage == "RQ":
            return out

        pr = PurchaseRequisition.objects.create(
            requisition=rq, branch_company=branch, address_company=cls.address, ref_no=pr_ref,
        )
        out["pr"] = pr
        if stage == "PR":
            return out

        cp = ComparisonPrice.objects.create(
            organizer=cls.approver, branch_company=branch, address_company=cls.address,
            ref_no=cp_ref, select_bidder=distributor,
        )
        cpd = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=distributor, vat_type=cls.vat, is_select=True,
            amount=Decimal(price),
        )
        cpi = ComparisonPriceItem.objects.create(
            item=item, bidder=cpd, unit=cls.unit, quantity=Decimal(qty),
            unit_price=Decimal(price), price=Decimal(price),
        )
        out.update(cp=cp, cpd=cpd, cpi=cpi)
        if stage == "CP":
            return out

        po = PurchaseOrder.objects.create(
            vat_type=cls.vat, cp=cp, pr=pr, distributor=distributor,
            approver_status=cls.status_approved, address_company=cls.address,
            ref_no=po_ref, amount=Decimal(price),
        )
        out["po"] = po
        for i in range(n_po_items):
            out["po_items"].append(PurchaseOrderItem.objects.create(
                po=po, item=item, unit=cls.unit, quantity=Decimal(qty),
                unit_price=Decimal(price), price=Decimal(price),
            ))
        return out

    # ----- Task 1 test -----
    def test_page_loads_empty_db(self):
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "report/viewAllDetails.html")
        self.assertEqual(list(resp.context["rows"]), [])
        self.assertEqual(resp.context["dashboard"]["requisition_items"], 0)
```

- [ ] **Step 2: Run it, verify it fails**

Run: `python manage.py test stock.tests_all_details_report.AllDetailsReportTests.test_page_loads_empty_db`
Expected: FAIL — `NoReverseMatch: 'viewAllDetailsReport' is not a valid view function or pattern name`.

- [ ] **Step 3: Add the URL**

In `djangostock/urls.py`, next to the other `report/purchaseOrder/...` lines (~line 170), add:

```python
    path('report/all/details/', views.viewAllDetailsReport, name='viewAllDetailsReport'),
```

- [ ] **Step 4: Add the view skeleton**

In `stock/views.py`, immediately before `def viewPOItemReport(request):`, add:

```python
def viewAllDetailsReport(request):
    active = request.session.get('company_code', 'ALL')
    company_in = findCompanyIn(request)

    base = (RequisitionItem.objects
            .filter(requisit__branch_company__code__in=company_in)
            .select_related('requisit', 'requisit__name', 'product')
            .order_by('-requisit__id', 'id'))

    qs = base
    dashboard = _all_details_dashboard(qs)

    p = Paginator(qs, 25)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    dataPage.object_list = list(dataPage.object_list)

    rows = _all_details_rows(dataPage.object_list)

    context = {
        'rows': rows,
        'page_obj': dataPage,
        'filter': None,
        'dashboard': dashboard,
        'rp_all_page': "tab-active",
        'rp_all_show': "show",
        active: "active show",
        "colorNav": "enableNav",
    }
    return render(request, "report/viewAllDetails.html", context)


def _all_details_dashboard(qs):
    zero = ('requisitions', 'requisition_items', 'purchase_reqs', 'comparison_prices',
            'comparison_items', 'distributors', 'purchase_orders', 'po_items')
    return {k: 0 for k in zero}


def _all_details_rows(items):
    return []
```

(`Paginator`, `findCompanyIn`, `RequisitionItem`, `render` are already imported in
`views.py`.)

- [ ] **Step 5: Create the template stub**

Create `stock/templates/report/viewAllDetails.html`:

```html
{% extends 'layouts.html' %}
{% load static %}
{% load crispy_forms_tags %}
{% load templatehelpers %}
{% load humanize %}

{% block content %}
<div class="container my-3">
  <h3 align="center">รายละเอียดการจัดซื้อทั้งหมด</h3>

  <div class="row my-3">
    {% for card in dashboard_cards %}
    <div class="col-6 col-md-3 mb-2">
      <div class="card div-shadow text-center">
        <div class="card-body py-2">
          <div class="text-muted small">{{ card.label }}</div>
          <div class="h4 mb-0">{{ card.value|intcomma }}</div>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
  <p class="text-muted small">ตัวเลขทั้งหมดนับตามเงื่อนไขการกรองปัจจุบัน</p>

  <div class="card div-shadow">
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-bordered my-2">
          <thead class="table-active">
            <tr>
              <th>ใบขอเบิก</th><th>รายการ</th><th>ใบขอซื้อ</th><th>ใบเปรียบเทียบ</th>
              <th>รายการเปรียบเทียบ</th><th>ร้านค้า</th><th>ใบสั่งซื้อ</th>
              <th>รายการสั่งซื้อ</th><th>ขั้นตอน</th><th class="text-right">จำนวนเงิน</th>
              <th>วันที่</th><th>จัดการ</th>
            </tr>
          </thead>
          <tbody>
          {% for row in rows %}
            <tr>
              <td>{% if row.requisition %}<a href="{% url 'showRequisition' row.requisition.id 4 %}">{{ row.requisition.ref_no }}</a>{% else %}-{% endif %}</td>
              <td>{{ row.item.product_name|default:"-" }}</td>
              <td>{% for pr in row.purchase_reqs %}<a href="{% url 'showPR' pr.id 4 %}">{{ pr.ref_no }}</a><br>{% empty %}-{% endfor %}</td>
              <td>{% if row.comparison_price %}<a href="{% url 'showComparePricePO' row.comparison_price.id 4 %}">{{ row.comparison_price.ref_no }}</a>{% else %}-{% endif %}</td>
              <td>{% if row.comparison_item %}{{ row.comparison_item.brand|default:row.comparison_item.quantity }}{% else %}-{% endif %}</td>
              <td>{% if row.distributor %}{{ row.distributor.name }}{% if row.is_selected_distributor %} <span class="badge badge-success">เลือก</span>{% endif %}{% else %}-{% endif %}</td>
              <td>{% if row.purchase_order %}<a href="{% url 'showPO' row.purchase_order.id 4 %}">{{ row.purchase_order.ref_no }}</a>{% else %}-{% endif %}</td>
              <td>{% if row.po_item %}{{ row.po_item.quantity }} × {{ row.po_item.unit_price|intcomma }}{% else %}-{% endif %}</td>
              <td><span class="badge badge-secondary">{{ row.stage }}</span></td>
              <td class="text-right">{% if row.amount != None %}{{ row.amount|intcomma }}{% else %}-{% endif %}</td>
              <td>{{ row.created|date:"d/m/Y" }}</td>
              <td><button type="button" class="btn btn-sm btn-outline-info chain-toggle">ดูสายงาน</button></td>
            </tr>
            <tr class="chain-detail" hidden>
              <td colspan="12">
                <ul class="mb-0">
                  <li>{{ row.requisition.ref_no|default:"-" }}</li>
                  {% for pr in row.purchase_reqs %}<li>{{ pr.ref_no }}</li>{% endfor %}
                  <li>{{ row.comparison_price.ref_no|default:"-" }}</li>
                  <li>{{ row.distributor.name|default:"-" }}</li>
                  <li>{{ row.purchase_order.ref_no|default:"-" }}</li>
                </ul>
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="12" class="text-center text-muted">ไม่พบข้อมูล ลองปรับเงื่อนไขการค้นหาหรือการกรอง</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <br/>
  <nav aria-label="Page navigation">
    <ul class="pagination justify-content-center">
      {% if page_obj.has_previous %}
        <li class="page-item"><a class="page-link" href="{% my_url page_obj.previous_page_number 'page' request.GET.urlencode %}">Previous</a></li>
      {% else %}
        <li class="page-item disabled"><a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a></li>
      {% endif %}
      {% for i in page_obj.paginator.page_range %}
        {% if page_obj.number == i %}
          <li class="page-item active" aria-current="page"><span class="page-link">{{ i }}<span class="sr-only">(current)</span></span></li>
        {% elif i > page_obj.number|add:'-5' and i < page_obj.number|add:'5' %}
          <li class="page-item"><a class="page-link" href="{% my_url i 'page' request.GET.urlencode %}">{{ i }}</a></li>
        {% endif %}
      {% endfor %}
      {% if page_obj.has_next %}
        <li class="page-item"><a class="page-link" href="{% my_url page_obj.next_page_number 'page' request.GET.urlencode %}">Next</a></li>
      {% else %}
        <li class="page-item disabled"><a class="page-link" href="#" tabindex="-1" aria-disabled="true">Next</a></li>
      {% endif %}
    </ul>
  </nav>
</div>
{% endblock %}

{% block javascript %}
<script>
  document.querySelectorAll('.chain-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var detail = btn.closest('tr').nextElementSibling;
      if (detail && detail.classList.contains('chain-detail')) {
        detail.hidden = !detail.hidden;
      }
    });
  });
</script>
{% endblock %}
```

(The `dashboard_cards` list is produced by the view in Task 4; until then the
loop renders nothing, which is fine.)

- [ ] **Step 6: Add the sidebar entry**

In `stock/templates/sidebar.html`, inside `reportSubmenu` (after the
`viewRateDistributorReport` `<li>`, ~line 212), add:

```html
                    <li>
                        <a class="{{rp_all_page}}" href="{% url 'viewAllDetailsReport' %}">รายละเอียดการจัดซื้อทั้งหมด</a>
                    </li>
```

And on the parent toggle (~line 201) add `rp_all_page` to the condition:

```html
                <a href="{% if request.user.is_authenticated %}#reportSubmenu{% endif %}" data-toggle="collapse" aria-expanded="{% if rp_po_page or rp_poi_page or rp_rd_page or rp_cl_page or rp_all_page %}true{% else %}false{% endif %}" class="dropdown-toggle">
```

- [ ] **Step 7: Run the test, verify it passes**

Run: `python manage.py test stock.tests_all_details_report.AllDetailsReportTests.test_page_loads_empty_db`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add djangostock/urls.py stock/views.py stock/templates/report/viewAllDetails.html stock/templates/sidebar.html stock/tests_all_details_report.py
git commit -m "feat: all-details procurement report — route, view skeleton, template, sidebar"
```

---

## Task 2: `AllDetailsFilter` and wire it into the view

**Files:**
- Modify: `stock/filters.py` (add `AllDetailsFilter` + labels at end of file)
- Modify: `stock/views.py` (`viewAllDetailsReport`: build the filter, use `myFilter.qs`)
- Modify: `stock/tests_all_details_report.py` (add filter tests)

**Interfaces:**
- Consumes: `RequisitionItem` model; `_build_chain` helper from Task 1.
- Produces:
  - `stock.filters.AllDetailsFilter(data, queryset) -> FilterSet`; `.qs` returns a
    filtered `RequisitionItem` queryset (callers apply `.distinct()`).
  - Recognised GET params: `search`, `rq_ref_no`, `pr_ref_no`, `cp_ref_no`,
    `po_ref_no`, `requester`, `product_name`, `product_id`, `machine`,
    `description`, `distributor`, `quantity_min`, `quantity_max`, `amount_min`,
    `amount_max`, `start_created`, `end_created`, `stage` (`PR`|`CP`|`PO`),
    `po_status`.
  - View change: `context['filter']` is now the `AllDetailsFilter` instance;
    `qs = myFilter.qs.distinct()` feeds both the dashboard and the paginator.

- [ ] **Step 1: Write the failing tests**

Append to `AllDetailsReportTests`:

```python
    def test_global_search_matches_each_ref_type(self):
        chain = self._build_chain(rq_ref="REQ-A-1", pr_ref="PR-A-1", cp_ref="CP-A-1",
                                  po_ref="PO-A-1", product_code="PA1",
                                  product_name="Laptop", distributor_name="ACME Ltd")
        # noise row that must NOT match the queries below
        self._build_chain(rq_ref="REQ-B-9", pr_ref="PR-B-9", cp_ref="CP-B-9",
                          po_ref="PO-B-9", product_code="PB9", product_name="Chair",
                          distributor_name="Other Co")
        for term in ["REQ-A-1", "PR-A-1", "CP-A-1", "PO-A-1", "Laptop", "ACME"]:
            resp = self.client.get(reverse(URL_NAME), {"search": term})
            refs = {r["requisition"].ref_no for r in resp.context["rows"]}
            self.assertEqual(refs, {"REQ-A-1"}, msg=f"search={term!r}")

    def test_stage_filter(self):
        self._build_chain(stage="PR", rq_ref="REQ-PR", pr_ref="PR-PR", product_code="PR1")
        self._build_chain(stage="PO", rq_ref="REQ-PO", pr_ref="PR-PO", cp_ref="CP-PO",
                          po_ref="PO-PO", product_code="PO1")
        resp = self.client.get(reverse(URL_NAME), {"stage": "PO"})
        refs = {r["requisition"].ref_no for r in resp.context["rows"]}
        self.assertEqual(refs, {"REQ-PO"})

    def test_date_range_filter(self):
        chain = self._build_chain(stage="PR", rq_ref="REQ-DATE", pr_ref="PR-DATE",
                                  product_code="PD1")
        Requisition.objects.filter(id=chain["rq"].id).update(
            created=datetime.date(2020, 1, 1))
        resp = self.client.get(reverse(URL_NAME),
                               {"start_created": "2019-12-01", "end_created": "2020-02-01"})
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-DATE"})
        resp = self.client.get(reverse(URL_NAME), {"start_created": "2021-01-01"})
        self.assertEqual(resp.context["rows"], [])

    def test_distributor_filter(self):
        self._build_chain(rq_ref="REQ-D1", pr_ref="PR-D1", cp_ref="CP-D1", po_ref="PO-D1",
                          product_code="D1", distributor_name="Unique Vendor")
        self._build_chain(rq_ref="REQ-D2", pr_ref="PR-D2", cp_ref="CP-D2", po_ref="PO-D2",
                          product_code="D2", distributor_name="Nope Vendor")
        resp = self.client.get(reverse(URL_NAME), {"distributor": "Unique"})
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-D1"})

    def test_company_scope_excludes_other_branch(self):
        self._build_chain(code="BR", rq_ref="REQ-BR", pr_ref="PR-BR", product_code="BR1",
                          stage="PR")
        self._build_chain(code="HO", rq_ref="REQ-HO", pr_ref="PR-HO", product_code="HO1",
                          stage="PR")
        resp = self.client.get(reverse(URL_NAME))  # session company_code == "HO"
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-HO"})
```

- [ ] **Step 2: Run them, verify they fail**

Run: `python manage.py test stock.tests_all_details_report.AllDetailsReportTests.test_global_search_matches_each_ref_type`
Expected: FAIL — `rows` is empty (view ignores GET params; row assembly still returns `[]` until Task 3, so also `KeyError`/empty). Both are acceptable "red" states; they turn green after Task 3. If you are running strictly task-by-task, mark these tests `@expectedFailure`-free but expect them to pass only once Task 3 lands. (Do not weaken them.)

> Note: Steps here add the filter; the assertions above also need Task 3's row
> assembly. Run the full file green at the end of Task 3.

- [ ] **Step 3: Add `AllDetailsFilter` to `stock/filters.py`**

At the end of `stock/filters.py`:

```python
class AllDetailsFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    rq_ref_no = django_filters.CharFilter(field_name='requisit__ref_no', lookup_expr='icontains')
    pr_ref_no = django_filters.CharFilter(method='filter_pr_ref_no')
    cp_ref_no = django_filters.CharFilter(method='filter_cp_ref_no')
    po_ref_no = django_filters.CharFilter(field_name='purchaseorderitem__po__ref_no', lookup_expr='icontains')
    requester = django_filters.ModelChoiceFilter(field_name='requisit__name', queryset=User.objects.all())
    product_name = django_filters.CharFilter(field_name='product_name', lookup_expr='icontains')
    product_id = django_filters.CharFilter(field_name='product__id', lookup_expr='icontains')
    machine = django_filters.CharFilter(field_name='machine', lookup_expr='icontains')
    description = django_filters.CharFilter(field_name='description', lookup_expr='icontains')
    distributor = django_filters.CharFilter(method='filter_distributor')
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    amount_min = django_filters.NumberFilter(field_name='purchaseorderitem__price', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='purchaseorderitem__price', lookup_expr='lte')
    start_created = django_filters.DateFilter(field_name='requisit__created', lookup_expr='gte',
                                             widget=DateInput(attrs={'type': 'date'}))
    end_created = django_filters.DateFilter(field_name='requisit__created', lookup_expr='lte',
                                           widget=DateInput(attrs={'type': 'date'}))
    stage = django_filters.ChoiceFilter(
        method='filter_stage',
        choices=(('PR', 'มีใบขอซื้อ'), ('CP', 'มีใบเปรียบเทียบ'), ('PO', 'มีใบสั่งซื้อ')),
    )
    po_status = django_filters.ModelChoiceFilter(
        field_name='purchaseorderitem__po__approver_status',
        queryset=BaseApproveStatus.objects.all(),
    )

    class Meta:
        model = RequisitionItem
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        q = (
            Q(requisit__ref_no__icontains=value)
            | Q(requisit__pr_ref_no__icontains=value)
            | Q(product_name__icontains=value)
            | Q(product__id__icontains=value)
            | Q(machine__icontains=value)
            | Q(description__icontains=value)
            | Q(requisit__name__first_name__icontains=value)
            | Q(requisit__name__last_name__icontains=value)
            | Q(comparisonpriceitem__bidder__cp__ref_no__icontains=value)
            | Q(comparisonpriceitem__bidder__distributor__name__icontains=value)
            | Q(purchaseorderitem__po__ref_no__icontains=value)
            | Q(purchaseorderitem__po__cp__ref_no__icontains=value)
            | Q(purchaseorderitem__po__pr__ref_no__icontains=value)
            | Q(purchaseorderitem__po__distributor__name__icontains=value)
        )
        return queryset.filter(q).distinct()

    def filter_pr_ref_no(self, queryset, name, value):
        return queryset.filter(
            Q(requisit__pr_ref_no__icontains=value)
            | Q(purchaseorderitem__po__pr__ref_no__icontains=value)
        ).distinct()

    def filter_cp_ref_no(self, queryset, name, value):
        return queryset.filter(
            Q(comparisonpriceitem__bidder__cp__ref_no__icontains=value)
            | Q(purchaseorderitem__po__cp__ref_no__icontains=value)
        ).distinct()

    def filter_distributor(self, queryset, name, value):
        return queryset.filter(
            Q(comparisonpriceitem__bidder__distributor__name__icontains=value)
            | Q(purchaseorderitem__po__distributor__name__icontains=value)
        ).distinct()

    def filter_stage(self, queryset, name, value):
        if value == 'PR':
            return queryset.filter(requisit__purchaserequisition__isnull=False).distinct()
        if value == 'CP':
            return queryset.filter(comparisonpriceitem__isnull=False).distinct()
        if value == 'PO':
            return queryset.filter(purchaseorderitem__isnull=False).distinct()
        return queryset


AllDetailsFilter.base_filters['search'].label = 'ค้นหา (ใบขอเบิก/ขอซื้อ/เปรียบเทียบ/สั่งซื้อ/สินค้า/ร้านค้า)'
AllDetailsFilter.base_filters['rq_ref_no'].label = 'เลขที่ใบขอเบิก'
AllDetailsFilter.base_filters['pr_ref_no'].label = 'เลขที่ใบขอซื้อ'
AllDetailsFilter.base_filters['cp_ref_no'].label = 'เลขที่ใบเปรียบเทียบ'
AllDetailsFilter.base_filters['po_ref_no'].label = 'เลขที่ใบสั่งซื้อ'
AllDetailsFilter.base_filters['requester'].label = 'ผู้ขอเบิก'
AllDetailsFilter.base_filters['product_name'].label = 'ชื่อสินค้า'
AllDetailsFilter.base_filters['product_id'].label = 'รหัสสินค้า'
AllDetailsFilter.base_filters['machine'].label = 'ใช้ในระบบงาน'
AllDetailsFilter.base_filters['description'].label = 'รายละเอียด'
AllDetailsFilter.base_filters['distributor'].label = 'ร้านค้า'
AllDetailsFilter.base_filters['quantity_min'].label = 'จำนวนตั้งแต่'
AllDetailsFilter.base_filters['quantity_max'].label = 'ถึง'
AllDetailsFilter.base_filters['amount_min'].label = 'ยอดเงินตั้งแต่'
AllDetailsFilter.base_filters['amount_max'].label = 'ถึง'
AllDetailsFilter.base_filters['start_created'].label = 'วันที่ตั้งเบิก'
AllDetailsFilter.base_filters['end_created'].label = 'ถึง'
AllDetailsFilter.base_filters['stage'].label = 'ขั้นตอน'
AllDetailsFilter.base_filters['po_status'].label = 'สถานะใบสั่งซื้อ'
```

`Q`, `django_filters`, `DateInput`, `User`, and `from .models import *` are already
imported at the top of `filters.py`. Confirm `User` is importable there; if not,
add `from django.contrib.auth.models import User`.

- [ ] **Step 4: Wire the filter into the view**

In `stock/views.py`, edit `viewAllDetailsReport` — replace `qs = base` with:

```python
    myFilter = AllDetailsFilter(request.GET, queryset=base)
    qs = myFilter.qs.distinct()
```

and change the context: `'filter': myFilter,` (was `None`). Add the import at the
top of `views.py` where the other filters are imported (search for
`PurchaseOrderItemFilter` in the `from .filters import` block and add
`AllDetailsFilter`).

- [ ] **Step 5: Run the filter tests** (they fully pass only after Task 3; run now to confirm no import/500 errors)

Run: `python manage.py test stock.tests_all_details_report.AllDetailsReportTests.test_company_scope_excludes_other_branch`
Expected: still FAIL on the row-count assertion (rows == []), but NO `500`, NO
`ImportError`. If you see a 500, fix it before continuing.

- [ ] **Step 6: Commit**

```bash
git add stock/filters.py stock/views.py stock/tests_all_details_report.py
git commit -m "feat: AllDetailsFilter — global search + field filters for all-details report"
```

---

## Task 3: Row assembly (fan-out, stages, incomplete chains, query budget)

**Files:**
- Modify: `stock/views.py` (`_all_details_rows`, and a small `_all_details_dashboard` stays as-is until Task 4)
- Modify: `stock/tests_all_details_report.py` (row-shape tests + query-budget test)

**Interfaces:**
- Consumes: `dataPage.object_list` — a `list[RequisitionItem]` (page slice).
- Produces: `_all_details_rows(items: list[RequisitionItem]) -> list[dict]`.
  Each dict has keys: `requisition` (`Requisition`), `item` (`RequisitionItem`),
  `purchase_reqs` (`list[PurchaseRequisition]`), `comparison_price`
  (`ComparisonPrice|None`), `comparison_item` (`ComparisonPriceItem|None`),
  `distributor` (`Distributor|None`), `is_selected_distributor` (`bool`),
  `purchase_order` (`PurchaseOrder|None`), `po_item` (`PurchaseOrderItem|None`),
  `stage` (`'RQ'|'PR'|'CP'|'PO'`), `amount` (`Decimal|None`), `created` (`date`).
  Ordering: input order of `items`; within an item, PO rows in `po_item.id`
  order, else CP rows in `comparison_item.id` order, else one bare row.

- [ ] **Step 1: Write the failing tests**

Append to `AllDetailsReportTests`:

```python
    def test_full_chain_row(self):
        self._build_chain(stage="PO", rq_ref="REQ-FULL", pr_ref="PR-FULL",
                          cp_ref="CP-FULL", po_ref="PO-FULL", product_code="F1")
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual(row["requisition"].ref_no, "REQ-FULL")
        self.assertEqual([pr.ref_no for pr in row["purchase_reqs"]], ["PR-FULL"])
        self.assertEqual(row["comparison_price"].ref_no, "CP-FULL")
        self.assertIsNotNone(row["comparison_item"])
        self.assertEqual(row["purchase_order"].ref_no, "PO-FULL")
        self.assertIsNotNone(row["po_item"])
        self.assertTrue(row["is_selected_distributor"])
        self.assertEqual(row["stage"], "PO")
        self.assertEqual(row["amount"], Decimal("1000.00"))

    def test_partial_chain_row_pr_only(self):
        self._build_chain(stage="PR", rq_ref="REQ-PART", pr_ref="PR-PART", product_code="PT1")
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual([pr.ref_no for pr in row["purchase_reqs"]], ["PR-PART"])
        self.assertIsNone(row["comparison_price"])
        self.assertIsNone(row["purchase_order"])
        self.assertEqual(row["stage"], "PR")
        self.assertIsNone(row["amount"])

    def test_requisition_only_row(self):
        self._build_chain(stage="RQ", rq_ref="REQ-BARE", product_code="B1")
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual(row["purchase_reqs"], [])
        self.assertEqual(row["stage"], "RQ")

    def test_cp_stage_row(self):
        self._build_chain(stage="CP", rq_ref="REQ-CP", pr_ref="PR-CP", cp_ref="CP-CP",
                          product_code="C1")
        resp = self.client.get(reverse(URL_NAME))
        row = resp.context["rows"][0]
        self.assertEqual(row["stage"], "CP")
        self.assertEqual(row["comparison_price"].ref_no, "CP-CP")
        self.assertIsNone(row["purchase_order"])
        self.assertEqual(row["amount"], Decimal("1000.00"))

    def test_fan_out_two_po_items_two_rows_no_dupes(self):
        self._build_chain(stage="PO", rq_ref="REQ-FAN", pr_ref="PR-FAN", cp_ref="CP-FAN",
                          po_ref="PO-FAN", product_code="FN1", n_po_items=2)
        resp = self.client.get(reverse(URL_NAME))
        rows = resp.context["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["requisition"].ref_no for r in rows}, {"REQ-FAN"})
        self.assertEqual(len({id(r["po_item"]) for r in rows}), 2)

    def test_query_budget(self):
        for i in range(5):
            self._build_chain(stage="PO", rq_ref=f"REQ-Q{i}", pr_ref=f"PR-Q{i}",
                              cp_ref=f"CP-Q{i}", po_ref=f"PO-Q{i}", product_code=f"Q{i}")
        with self.assertNumQueries(20):
            self.client.get(reverse(URL_NAME))
```

- [ ] **Step 2: Run them, verify they fail**

Run: `python manage.py test stock.tests_all_details_report.AllDetailsReportTests.test_full_chain_row`
Expected: FAIL — `len(rows) == 0` (assembly returns `[]`).

- [ ] **Step 3: Implement `_all_details_rows`**

In `stock/views.py`, replace the stub `_all_details_rows` with:

```python
def _all_details_rows(items):
    from collections import defaultdict

    if not items:
        return []

    item_ids = [ri.id for ri in items]
    req_ids = {ri.requisit_id for ri in items if ri.requisit_id}

    poi_qs = (PurchaseOrderItem.objects
              .filter(item_id__in=item_ids)
              .select_related('po', 'po__cp', 'po__pr', 'po__distributor',
                              'po__approver_status', 'unit')
              .order_by('id'))
    cpi_qs = (ComparisonPriceItem.objects
              .filter(item_id__in=item_ids)
              .select_related('bidder', 'bidder__distributor', 'bidder__cp', 'unit')
              .order_by('id'))
    pr_qs = (PurchaseRequisition.objects
             .filter(requisition_id__in=req_ids)
             .order_by('id'))

    poi_by_item = defaultdict(list)
    for poi in poi_qs:
        poi_by_item[poi.item_id].append(poi)
    cpi_by_item = defaultdict(list)
    for cpi in cpi_qs:
        cpi_by_item[cpi.item_id].append(cpi)
    prs_by_req = defaultdict(list)
    for pr in pr_qs:
        prs_by_req[pr.requisition_id].append(pr)

    rows = []
    for ri in items:
        prs = prs_by_req.get(ri.requisit_id, [])
        item_pois = poi_by_item.get(ri.id, [])
        item_cpis = cpi_by_item.get(ri.id, [])
        # index this item's CP items by their CP id, to pair with a PO's cp
        cpi_by_cp = {}
        for cpi in item_cpis:
            cp_id = cpi.bidder.cp_id if cpi.bidder_id else None
            if cp_id is not None:
                cpi_by_cp.setdefault(cp_id, cpi)

        if item_pois:
            for poi in item_pois:
                po = poi.po
                cp = po.cp if po else None
                cpi = cpi_by_cp.get(po.cp_id) if po else None
                cpd = cpi.bidder if cpi else None
                distributor = (po.distributor if po and po.distributor_id
                               else (cpd.distributor if cpd else None))
                rows.append({
                    'requisition': ri.requisit,
                    'item': ri,
                    'purchase_reqs': prs,
                    'comparison_price': cp,
                    'comparison_item': cpi,
                    'distributor': distributor,
                    'is_selected_distributor': bool(cpd and cpd.is_select),
                    'purchase_order': po,
                    'po_item': poi,
                    'stage': 'PO',
                    'amount': poi.price,
                    'created': ri.requisit.created if ri.requisit_id else ri.created,
                })
        elif item_cpis:
            for cpi in item_cpis:
                cpd = cpi.bidder
                rows.append({
                    'requisition': ri.requisit,
                    'item': ri,
                    'purchase_reqs': prs,
                    'comparison_price': cpd.cp if cpd else None,
                    'comparison_item': cpi,
                    'distributor': cpd.distributor if cpd else None,
                    'is_selected_distributor': bool(cpd and cpd.is_select),
                    'purchase_order': None,
                    'po_item': None,
                    'stage': 'CP',
                    'amount': cpi.price,
                    'created': ri.requisit.created if ri.requisit_id else ri.created,
                })
        else:
            rows.append({
                'requisition': ri.requisit,
                'item': ri,
                'purchase_reqs': prs,
                'comparison_price': None,
                'comparison_item': None,
                'distributor': None,
                'is_selected_distributor': False,
                'purchase_order': None,
                'po_item': None,
                'stage': 'PR' if prs else 'RQ',
                'amount': None,
                'created': ri.requisit.created if ri.requisit_id else ri.created,
            })
    return rows
```

Add `PurchaseOrderItem`, `ComparisonPriceItem`, `PurchaseRequisition` to the
model imports in `views.py` if not already present (search the top-of-file
`from .models import` — this project uses `from .models import *`, so they are
already available; no change needed).

- [ ] **Step 4: Run the row tests + the Task 2 filter tests**

Run: `python manage.py test stock.tests_all_details_report`
Expected: all tests in the file PASS, including the Task 2 filter tests.
If `test_query_budget` fails on the number, adjust the literal in the test to the
actual count **only if** it is ≤ 22 and does not scale with the 5 fixture rows
(add a 6th `_build_chain` locally to confirm the count is constant, then revert).
If it scales per row, there is an N+1 — fix `_all_details_rows` (usually a missing
`select_related`), do not just raise the number.

- [ ] **Step 5: Commit**

```bash
git add stock/views.py stock/tests_all_details_report.py
git commit -m "feat: all-details report row assembly with stage fan-out and incomplete-chain handling"
```

---

## Task 4: Filtered dashboard counts + template dashboard wiring + pagination test

**Files:**
- Modify: `stock/views.py` (`_all_details_dashboard`, add `dashboard_cards` to context)
- Modify: `stock/templates/report/viewAllDetails.html` (add the filter `<form>`; dashboard loop already present)
- Modify: `stock/tests_all_details_report.py` (dashboard + pagination tests)

**Interfaces:**
- Consumes: `qs` — the filtered, `.distinct()` `RequisitionItem` queryset.
- Produces:
  - `_all_details_dashboard(qs) -> dict` with int values under keys
    `requisitions, requisition_items, purchase_reqs, comparison_prices,
    comparison_items, distributors, purchase_orders, po_items`.
  - `context['dashboard_cards']` — `list[dict(label:str, value:int)]` in display
    order, built in the view from the dashboard dict.

- [ ] **Step 1: Write the failing tests**

Append to `AllDetailsReportTests`:

```python
    def test_dashboard_counts_reflect_filter(self):
        # 1 full PO chain for HO, 1 PR-only chain for HO, 1 chain for BR (out of scope)
        self._build_chain(stage="PO", rq_ref="REQ-DA", pr_ref="PR-DA", cp_ref="CP-DA",
                          po_ref="PO-DA", product_code="DA1", n_po_items=2)
        self._build_chain(stage="PR", rq_ref="REQ-DB", pr_ref="PR-DB", product_code="DB1")
        self._build_chain(code="BR", stage="PO", rq_ref="REQ-DC", pr_ref="PR-DC",
                          cp_ref="CP-DC", po_ref="PO-DC", product_code="DC1")
        resp = self.client.get(reverse(URL_NAME))
        d = resp.context["dashboard"]
        self.assertEqual(d["requisitions"], 2)
        self.assertEqual(d["requisition_items"], 2)
        self.assertEqual(d["purchase_reqs"], 2)
        self.assertEqual(d["comparison_prices"], 1)
        self.assertEqual(d["comparison_items"], 1)
        self.assertEqual(d["distributors"], 1)
        self.assertEqual(d["purchase_orders"], 1)
        self.assertEqual(d["po_items"], 2)

    def test_dashboard_counts_follow_search(self):
        self._build_chain(stage="PO", rq_ref="REQ-S1", pr_ref="PR-S1", cp_ref="CP-S1",
                          po_ref="PO-S1", product_code="S1", product_name="Keyboard")
        self._build_chain(stage="PO", rq_ref="REQ-S2", pr_ref="PR-S2", cp_ref="CP-S2",
                          po_ref="PO-S2", product_code="S2", product_name="Monitor")
        resp = self.client.get(reverse(URL_NAME), {"search": "Keyboard"})
        self.assertEqual(resp.context["dashboard"]["requisition_items"], 1)
        self.assertEqual(resp.context["dashboard"]["purchase_orders"], 1)

    def test_pagination_preserves_querystring(self):
        for i in range(30):
            self._build_chain(stage="PR", rq_ref=f"REQ-P{i:02d}", pr_ref=f"PR-P{i:02d}",
                              product_code=f"PP{i:02d}", product_name="Widget")
        resp = self.client.get(reverse(URL_NAME), {"search": "Widget"})
        self.assertEqual(len(resp.context["rows"]), 25)
        self.assertContains(resp, "search=Widget")
        resp2 = self.client.get(reverse(URL_NAME), {"search": "Widget", "page": 2})
        self.assertEqual(len(resp2.context["rows"]), 5)

    def test_filter_form_renders(self):
        resp = self.client.get(reverse(URL_NAME))
        self.assertContains(resp, 'name="search"')
        self.assertContains(resp, 'name="stage"')
        self.assertContains(resp, 'name="start_created"')
```

- [ ] **Step 2: Run them, verify they fail**

Run: `python manage.py test stock.tests_all_details_report.AllDetailsReportTests.test_dashboard_counts_reflect_filter`
Expected: FAIL — dashboard values are all `0` (stub).

- [ ] **Step 3: Implement `_all_details_dashboard`**

In `stock/views.py`, replace the stub with:

```python
def _all_details_dashboard(qs):
    item_ids = qs.values('id')
    req_ids = qs.values('requisit_id')
    cpi = ComparisonPriceItem.objects.filter(item_id__in=item_ids)
    return {
        'requisitions': qs.values('requisit_id').distinct().count(),
        'requisition_items': qs.count(),
        'purchase_reqs': (PurchaseRequisition.objects
                          .filter(requisition_id__in=req_ids).distinct().count()),
        'comparison_prices': cpi.values('bidder__cp').distinct().count(),
        'comparison_items': cpi.count(),
        'distributors': cpi.values('bidder__distributor').distinct().count(),
        'purchase_orders': (PurchaseOrder.objects
                            .filter(purchaseorderitem__item_id__in=item_ids)
                            .distinct().count()),
        'po_items': PurchaseOrderItem.objects.filter(item_id__in=item_ids).count(),
    }
```

Note: `qs` is already `.distinct()` from the view; passing `qs.values('id')` as a
subquery keeps everything DB-side (no ID list materialised).

- [ ] **Step 4: Build `dashboard_cards` in the view**

In `viewAllDetailsReport`, after `dashboard = _all_details_dashboard(qs)` add:

```python
    dashboard_cards = [
        {'label': 'ใบขอเบิก', 'value': dashboard['requisitions']},
        {'label': 'รายการขอเบิก', 'value': dashboard['requisition_items']},
        {'label': 'ใบขอซื้อ', 'value': dashboard['purchase_reqs']},
        {'label': 'ใบเปรียบเทียบ', 'value': dashboard['comparison_prices']},
        {'label': 'รายการเปรียบเทียบ', 'value': dashboard['comparison_items']},
        {'label': 'ร้านค้า', 'value': dashboard['distributors']},
        {'label': 'ใบสั่งซื้อ', 'value': dashboard['purchase_orders']},
        {'label': 'รายการสั่งซื้อ', 'value': dashboard['po_items']},
    ]
```

and add `'dashboard_cards': dashboard_cards,` to the `context` dict.

- [ ] **Step 5: Add the filter form to the template**

In `stock/templates/report/viewAllDetails.html`, insert this block between the
`<p class="text-muted small">…</p>` line and the results `<div class="card div-shadow">`:

```html
  <div class="card my-3 bg-light div-shadow">
    <div class="card-body">
      <form method="get">
        {% csrf_token %}
        <div class="form-row">
          <div class="form-group col-md-4 mb-0">{{ filter.form.search|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.rq_ref_no|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.pr_ref_no|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.cp_ref_no|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.po_ref_no|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.requester|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.product_id|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.product_name|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.machine|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.description|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.distributor|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.stage|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.po_status|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.quantity_min|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.quantity_max|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.amount_min|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.amount_max|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.start_created|as_crispy_field }}</div>
          <div class="form-group col-md-2 mb-0">{{ filter.form.end_created|as_crispy_field }}</div>
        </div>
        <button type="submit" class="btn btn-info">กรอง <i class="fas fa-filter"></i></button>
        <a href="{% url 'viewAllDetailsReport' %}" class="btn btn-secondary">ล้าง</a>
      </form>
    </div>
  </div>
```

- [ ] **Step 6: Run the whole test file**

Run: `python manage.py test stock.tests_all_details_report`
Expected: every test PASSES.

- [ ] **Step 7: Full regression — report area + existing suite**

Run: `python manage.py test stock`
Expected: no new failures versus a clean `main` run. (The pre-existing
`CreatePOFromComparisonPriceTestCase` fragility is unrelated; if it fails, confirm
it also fails on `main` before continuing.)

- [ ] **Step 8: Commit**

```bash
git add stock/views.py stock/templates/report/viewAllDetails.html stock/tests_all_details_report.py
git commit -m "feat: filtered dashboard counts + filter form for all-details report"
```

---

## Self-Review

**1. Spec coverage**

| Spec item | Task |
|---|---|
| New report page in `report/viewAllDetails.html` | 1 |
| Route + view following sibling report conventions | 1 |
| Sidebar entry + `aria-expanded` condition | 1 |
| Company scoping via `findCompanyIn`, no decorator | 1 (Global Constraints) |
| `AllDetailsFilter` — global `search` + all field filters | 2 |
| Row = one per `RequisitionItem`, fan out on deepest stage | 3 |
| Incomplete chains still shown, `-` for missing stages | 3 (`test_partial_chain_row_pr_only`, `test_requisition_only_row`) + template |
| CP reached via `bidder.cp`; `ComparisonPriceItem.cp` ignored | 3 (`cpi_by_cp` uses `cpi.bidder.cp_id`) |
| No `ComparisonPrice→PR` FK; meet at PO | 3 (PO row pulls `po.cp` + `po.pr` independently) |
| Filtered dashboard, 8 counts, labelled | 4 |
| Pagination 25/page, querystring preserved | 1 (block) + 4 (`test_pagination_preserves_querystring`) |
| `show*` detail links + inline expand row | 1 (template + JS) |
| Empty state | 1 (template `{% empty %}`) |
| Duplicate-row prevention | 3 (`test_fan_out_two_po_items_two_rows_no_dupes`; `.distinct()` in filter methods) |
| N+1 prevention / query budget | 3 (`test_query_budget`) |
| Tests in separate `tests_all_details_report.py` | 1 |
| No model changes / no migration | Global Constraints |

**2. Placeholder scan:** none — every step has concrete code or exact commands.

**3. Type consistency:** `_all_details_rows(items) -> list[dict]` with the key set
defined in Task 3 is the same key set the Task 1 template reads
(`requisition, item, purchase_reqs, comparison_price, comparison_item,
distributor, is_selected_distributor, purchase_order, po_item, stage, amount,
created`). `_all_details_dashboard(qs) -> dict` keys match `dashboard_cards`
construction in Task 4 and the `test_dashboard_counts_reflect_filter` assertions.
`AllDetailsFilter` param names match the template fields and the filter tests.
Context keys (`rows`, `page_obj`, `filter`, `dashboard`, `dashboard_cards`,
layout flags) are consistent across Tasks 1–4.

---

## Execution Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-08-31-all-details-procurement-report.md`.
