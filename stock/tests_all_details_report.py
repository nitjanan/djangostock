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

    # ----- Task 2 test -----
    def test_filter_instance_and_params_accepted(self):
        from stock.filters import AllDetailsFilter
        resp = self.client.get(reverse(URL_NAME), {"search": "x", "stage": "PO"})
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.context["filter"], AllDetailsFilter)

    # ----- Task 3 tests: row assembly -----
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
        # Row assembly must not be N+1: the query count for the report must be
        # constant regardless of how many procurement chains are on the page.
        # (The absolute count is dominated by base-template nav/permission queries
        # unrelated to _all_details_rows; what this guards is const-ness.)
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        for i in range(3):
            self._build_chain(stage="PO", rq_ref=f"REQ-Q{i}", pr_ref=f"PR-Q{i}",
                              cp_ref=f"CP-Q{i}", po_ref=f"PO-Q{i}", product_code=f"Q{i}")
        with CaptureQueriesContext(connection) as ctx3:
            self.client.get(reverse(URL_NAME))
        count3 = len(ctx3)

        for i in range(3, 8):
            self._build_chain(stage="PO", rq_ref=f"REQ-Q{i}", pr_ref=f"PR-Q{i}",
                              cp_ref=f"CP-Q{i}", po_ref=f"PO-Q{i}", product_code=f"Q{i}")
        with CaptureQueriesContext(connection) as ctx8:
            self.client.get(reverse(URL_NAME))
        count8 = len(ctx8)

        self.assertEqual(count3, count8,
                         msg=f"query count scales with rows: {count3} -> {count8} (N+1)")
        self.assertLess(count8, 70,
                        msg=f"view issued {count8} queries for 8 chains — investigate query balloon")

    def test_global_search_matches_each_ref_type(self):
        chain = self._build_chain(rq_ref="REQ-A-1", pr_ref="PR-A-1", cp_ref="CP-A-1",
                                  po_ref="PO-A-1", product_code="PA1",
                                  product_name="Laptop", distributor_name="ACME Ltd")
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
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-HO"})

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
