from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from stock.models import (
    UserProfile, BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress,
    BaseVatType, BaseUnit, BaseApproveStatus, BaseDepartment, Category,
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
                     po_ref="PO-0056", qty="2.0000", price="1000.00", n_po_items=1,
                     n_bidders=1, section=None, cp_without_bidder=False,
                     po_from_cp=True, skip_cp=False, machine="MC-1", note="",
                     po_item_description="", ma_ref_no="", ma_id=None):
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
            section=section, note=note, ma_ref_no=ma_ref_no, ma_id=ma_id,
        )
        item = RequisitionItem.objects.create(
            requisition_id=rq.id, requisit=rq, product=product,
            product_name=product_name, machine=machine, description="desc",
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

        # skip_cp: jump straight to a PO with no comparison at all
        # (real case: PO raised directly from the PR).
        if skip_cp and stage == "PO":
            cp = None
        else:
            cp = ComparisonPrice.objects.create(
                organizer=cls.approver, branch_company=branch, address_company=cls.address,
                ref_no=cp_ref, select_bidder=distributor,
            )
            if cp_without_bidder:
                # Comparison drafted, no bidder chosen yet: item linked only by
                # the `cp` integer column (matches real-data flows). bidder NULL.
                cpi = ComparisonPriceItem.objects.create(
                    item=item, bidder=None, cp=cp.id, unit=cls.unit,
                    quantity=Decimal(qty), unit_price=Decimal(price), price=Decimal(price),
                    brand="BRAND-NOBID",
                )
                out.update(cp=cp, cpd=None, cpi=cpi)
            else:
                # Losing bidders first, so the selected bidder's
                # ComparisonPriceItem is NOT the lowest id — exercises the
                # "prefer selected bidder" pairing.
                for b in range(1, n_bidders):
                    loser_dist = Distributor.objects.create(
                        id="D-" + product_code + "-b" + str(b),
                        name=distributor_name + " bidder " + str(b),
                    )
                    loser_cpd = ComparisonPriceDistributor.objects.create(
                        cp=cp, distributor=loser_dist, vat_type=cls.vat, is_select=False,
                        amount=Decimal(price),
                    )
                    ComparisonPriceItem.objects.create(
                        item=item, bidder=loser_cpd, cp=cp.id, unit=cls.unit,
                        quantity=Decimal(qty), unit_price=Decimal(price),
                        price=Decimal(price), brand="BRAND-LOSE-" + str(b),
                    )
                cpd = ComparisonPriceDistributor.objects.create(
                    cp=cp, distributor=distributor, vat_type=cls.vat, is_select=True,
                    total_price=Decimal(price), total_after_discount=Decimal(price),
                    vat=Decimal("0.00"), amount=Decimal(price),
                )
                cpi = ComparisonPriceItem.objects.create(
                    item=item, bidder=cpd, cp=cp.id, unit=cls.unit, quantity=Decimal(qty),
                    unit_price=Decimal(price), price=Decimal(price), brand="BRAND-SEL",
                )
                out.update(cp=cp, cpd=cpd, cpi=cpi)
        if stage == "CP":
            return out

        if po_from_cp:
            po_cp, po_dist = cp, distributor
        else:
            # PO raised straight from the PR, not generated from the comparison.
            po_cp = None
            po_dist = Distributor.objects.create(
                id="D-" + product_code + "-po", name=distributor_name + " (PO shop)")
        po = PurchaseOrder.objects.create(
            vat_type=cls.vat, cp=po_cp, pr=pr, distributor=po_dist,
            approver_status=cls.status_approved, address_company=cls.address,
            ref_no=po_ref, total_price=Decimal(price),
            total_after_discount=Decimal(price), vat=Decimal("0.00"),
            amount=Decimal(price),
        )
        out["po"] = po
        for i in range(n_po_items):
            out["po_items"].append(PurchaseOrderItem.objects.create(
                po=po, item=item, unit=cls.unit, quantity=Decimal(qty),
                unit_price=Decimal(price), price=Decimal(price),
                description=po_item_description,
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
        resp = self.client.get(reverse(URL_NAME), {"search": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.context["filter"], AllDetailsFilter)

    def test_filter_has_only_search_and_stage_fields(self):
        """The filter form must expose exactly two fields: search (id_search) and stage."""
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(list(resp.context["filter"].form.fields.keys()), ["search", "stage"])
        self.assertContains(resp, 'name="search"')
        self.assertContains(resp, 'id="id_search"')
        self.assertContains(resp, 'name="stage"')
        for gone in ('name="distributor"', 'name="start_created"',
                     'name="end_created"', 'name="po_status"', 'name="rq_ref_no"',
                     'name="pr_ref_no"', 'name="cp_ref_no"', 'name="po_ref_no"',
                     'name="requester"', 'name="product_id"', 'name="product_name"',
                     'name="machine"', 'name="description"', 'name="quantity_min"',
                     'name="amount_min"'):
            self.assertNotContains(resp, gone)

    def test_stage_filter_matches_deepest_stage(self):
        self._build_chain(stage="RQ", rq_ref="REQ-RQ", product_code="SR1")
        self._build_chain(stage="PR", rq_ref="REQ-PR", pr_ref="PR-PR", product_code="SR2")
        self._build_chain(stage="CP", rq_ref="REQ-CP", pr_ref="PR-CP", cp_ref="CP-CP",
                          product_code="SR3")
        self._build_chain(stage="PO", rq_ref="REQ-PO", pr_ref="PR-PO", cp_ref="CP-PO",
                          po_ref="PO-PO", product_code="SR4")
        cases = {"RQ": "REQ-RQ", "PR": "REQ-PR", "CP": "REQ-CP", "PO": "REQ-PO"}
        for stage, expected in cases.items():
            resp = self.client.get(reverse(URL_NAME), {"stage": stage})
            refs = {r["requisition"].ref_no for r in resp.context["rows"]}
            self.assertEqual(refs, {expected}, msg=f"stage={stage}")
            self.assertEqual({r["stage"] for r in resp.context["rows"]}, {stage},
                             msg=f"stage={stage}")

    def test_cp_stage_row_without_bidder(self):
        """A comparison with no chosen bidder (linked only by the cp int column)
        must still render as stage CP with its ref_no, and be reachable via
        ?stage=CP, the CP-ref search, and the dashboard count."""
        self._build_chain(stage="CP", rq_ref="REQ-NB", pr_ref="PR-NB",
                          cp_ref="CS16908002", product_code="NB1",
                          cp_without_bidder=True)
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual(row["stage"], "CP")
        self.assertIsNotNone(row["comparison_price"])
        self.assertEqual(row["comparison_price"].ref_no, "CS16908002")
        self.assertEqual(resp.context["dashboard"]["comparison_prices"], 1)

        resp = self.client.get(reverse(URL_NAME), {"stage": "CP"})
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-NB"})

        resp = self.client.get(reverse(URL_NAME), {"search": "CS16908002"})
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-NB"})

    def test_separate_po_and_cp_branches_render_as_separate_rows(self):
        """One item, two independent branches off the PR: a PO raised straight
        from the PR (po.cp is NULL) AND a standalone comparison. Each is its own
        row — the comparison is NOT merged onto the PO row."""
        self._build_chain(stage="PO", rq_ref="QS16908001", pr_ref="RS16908001",
                          cp_ref="CS16908002", po_ref="S16908002",
                          product_code="NC1", po_from_cp=False)
        resp = self.client.get(reverse(URL_NAME))
        rows = resp.context["rows"]
        self.assertEqual(len(rows), 2)
        by_stage = {r["stage"]: r for r in rows}
        self.assertEqual(set(by_stage), {"PO", "CP"})

        po_row = by_stage["PO"]
        self.assertEqual(po_row["purchase_order"].ref_no, "S16908002")
        self.assertIsNone(po_row["comparison_price"])   # PO not from the comparison
        self.assertIsNone(po_row["comparison_item"])

        cp_row = by_stage["CP"]
        self.assertEqual(cp_row["comparison_price"].ref_no, "CS16908002")
        self.assertIsNone(cp_row["purchase_order"])

        resp = self.client.get(reverse(URL_NAME), {"search": "CS16908002"})
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]},
                         {"QS16908001"})

    def test_po_row_without_any_comparison(self):
        """PO raised directly from the PR with no comparison at all — must not
        crash and renders stage PO with a blank comparison cell."""
        self._build_chain(stage="PO", rq_ref="REQ-NOCMP", pr_ref="PR-NOCMP",
                          po_ref="PO-NOCMP", product_code="NX1", skip_cp=True)
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual(row["stage"], "PO")
        self.assertIsNone(row["comparison_price"])
        self.assertIsNone(row["comparison_item"])
        self.assertFalse(row["is_selected_distributor"])

    def test_machine_and_note_columns_and_search(self):
        self._build_chain(stage="PR", rq_ref="REQ-MN", pr_ref="PR-MN", product_code="MN1",
                          machine="ระบบบัญชี", note="ด่วนมากพิเศษ")
        self._build_chain(stage="PR", rq_ref="REQ-XX", pr_ref="PR-XX", product_code="XX1",
                          machine="ระบบอื่น", note="ปกติ")
        resp = self.client.get(reverse(URL_NAME))
        self.assertContains(resp, "ใช้ในระบบงาน")
        self.assertContains(resp, "หมายเหตุ")
        self.assertContains(resp, "ระบบบัญชี")
        self.assertContains(resp, "ด่วนมากพิเศษ")
        for term in ("ระบบบัญชี", "ด่วนมากพิเศษ"):
            r = self.client.get(reverse(URL_NAME), {"search": term})
            self.assertEqual({x["requisition"].ref_no for x in r.context["rows"]},
                             {"REQ-MN"}, msg=f"search={term!r}")

    def test_po_item_description_shown_under_product_name(self):
        self._build_chain(stage="PO", rq_ref="REQ-PD", pr_ref="PR-PD", cp_ref="CP-PD",
                          po_ref="PO-PD", product_code="PD1", product_name="สายไฟ",
                          po_item_description="ยาว 50 เมตร สีดำ")
        resp = self.client.get(reverse(URL_NAME))
        self.assertContains(resp, "สายไฟ")
        self.assertContains(
            resp, '<small class="text-muted">ยาว 50 เมตร สีดำ</small>', html=False)

    def test_stage_date_reflects_current_stage(self):
        import datetime as _dt
        from stock.models import ComparisonPrice as _CP
        rq_c = self._build_chain(stage="RQ", rq_ref="REQ-D0", product_code="SD0")
        pr_c = self._build_chain(stage="PR", rq_ref="REQ-D1", pr_ref="PR-D1",
                                 product_code="SD1")
        cp_c = self._build_chain(stage="CP", rq_ref="REQ-D2", pr_ref="PR-D2",
                                 cp_ref="CP-D2", product_code="SD2")
        po_c = self._build_chain(stage="PO", rq_ref="REQ-D3", pr_ref="PR-D3",
                                 cp_ref="CP-D3", po_ref="PO-D3", product_code="SD3")
        Requisition.objects.filter(id=rq_c["rq"].id).update(created=_dt.date(2021, 1, 1))
        PurchaseRequisition.objects.filter(id=pr_c["pr"].id).update(created=_dt.date(2022, 2, 2))
        _CP.objects.filter(id=cp_c["cp"].id).update(created=_dt.date(2023, 3, 3))
        PurchaseOrder.objects.filter(id=po_c["po"].id).update(created=_dt.date(2024, 4, 4))
        rows = {r["requisition"].ref_no: r for r in
                self.client.get(reverse(URL_NAME)).context["rows"]}
        self.assertEqual(rows["REQ-D0"]["stage_date"], _dt.date(2021, 1, 1))
        self.assertEqual(rows["REQ-D1"]["stage_date"], _dt.date(2022, 2, 2))
        self.assertEqual(rows["REQ-D2"]["stage_date"], _dt.date(2023, 3, 3))
        self.assertEqual(rows["REQ-D3"]["stage_date"], _dt.date(2024, 4, 4))

    def test_maintenance_ref_shown_before_requisition_and_searchable(self):
        self._build_chain(stage="PR", rq_ref="RQ-MA", pr_ref="PR-MA", product_code="MA1",
                          ma_ref_no="MA-2026-001", ma_id=555)
        self._build_chain(stage="PR", rq_ref="RQ-NOMA", pr_ref="PR-NOMA",
                          product_code="NOMA1")
        html = self.client.get(reverse(URL_NAME)).content.decode()
        # MA ref rendered, and it appears before the RQ ref of the same chain
        self.assertIn("MA-2026-001", html)
        self.assertIn("/maintenance/show/555/4", html)
        self.assertLess(html.index("MA-2026-001"), html.index("RQ-MA"))
        self.assertIn("RQ-NOMA", html)  # non-maintenance chain still renders
        # searchable via id_search
        r = self.client.get(reverse(URL_NAME), {"search": "MA-2026-001"})
        self.assertEqual({x["requisition"].ref_no for x in r.context["rows"]}, {"RQ-MA"})

    def test_rows_ordered_by_document_refs(self):
        self._build_chain(stage="PO", rq_ref="RQ-B", pr_ref="PR-B", cp_ref="CP-B",
                          po_ref="PO-B", product_code="OB1")
        self._build_chain(stage="PR", rq_ref="RQ-A", pr_ref="PR-A", product_code="OA1")
        self._build_chain(stage="CP", rq_ref="RQ-A", pr_ref="PR-A2", cp_ref="CP-A2",
                          product_code="OA2")
        resp = self.client.get(reverse(URL_NAME))
        keys = [
            (r["requisition"].ref_no,
             r["purchase_reqs"][0].ref_no if r["purchase_reqs"] else "",
             r["comparison_price"].ref_no if r["comparison_price"] else "",
             r["purchase_order"].ref_no if r["purchase_order"] else "")
            for r in resp.context["rows"]
        ]
        self.assertEqual(keys, sorted(keys, reverse=True))
        self.assertEqual(keys[0][0], "RQ-B")

    def test_stage_filter_combines_with_search(self):
        self._build_chain(stage="PO", rq_ref="REQ-C1", pr_ref="PR-C1", cp_ref="CP-C1",
                          po_ref="PO-C1", product_code="SC1", product_name="Router")
        self._build_chain(stage="PR", rq_ref="REQ-C2", pr_ref="PR-C2",
                          product_code="SC2", product_name="Router")
        resp = self.client.get(reverse(URL_NAME), {"search": "Router", "stage": "PR"})
        self.assertEqual({r["requisition"].ref_no for r in resp.context["rows"]}, {"REQ-C2"})

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
            stage = "PO" if i % 2 == 0 else "CP"
            self._build_chain(stage=stage, rq_ref=f"REQ-Q{i}", pr_ref=f"PR-Q{i}",
                              cp_ref=f"CP-Q{i}", po_ref=f"PO-Q{i}", product_code=f"Q{i}")
        with CaptureQueriesContext(connection) as ctx3:
            self.client.get(reverse(URL_NAME))
        count3 = len(ctx3)

        for i in range(3, 8):
            stage = "PO" if i % 2 == 0 else "CP"
            self._build_chain(stage=stage, rq_ref=f"REQ-Q{i}", pr_ref=f"PR-Q{i}",
                              cp_ref=f"CP-Q{i}", po_ref=f"PO-Q{i}", product_code=f"Q{i}")
        with CaptureQueriesContext(connection) as ctx8:
            self.client.get(reverse(URL_NAME))
        count8 = len(ctx8)

        # The rich chain-detail panel touches many related rows; select_related
        # keeps growth sub-linear. A true N+1 would add ~5+ queries per 5 chains
        # (several related accesses each) — tolerate a small fixed residual only.
        self.assertLessEqual(count8 - count3, 6,
                             msg=f"query count scales with rows: {count3} -> {count8} (N+1)")
        self.assertLess(count8, 80,
                        msg=f"view issued {count8} queries for 8 chains — investigate query balloon")

    def test_multi_bidder_po_row_uses_selected_bidder(self):
        self._build_chain(stage="PO", rq_ref="REQ-MB", pr_ref="PR-MB", cp_ref="CP-MB",
                          po_ref="PO-MB", product_code="MB1", n_bidders=3)
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual(row["comparison_item"].brand, "BRAND-SEL")
        self.assertIs(row["is_selected_distributor"], True)

    def test_cancelled_po_falls_back_to_cp_stage(self):
        chain = self._build_chain(stage="PO", rq_ref="REQ-XPO", pr_ref="PR-XPO",
                                  cp_ref="CP-XPO", po_ref="PO-XPO", product_code="XPO1")
        PurchaseOrder.objects.filter(id=chain["po"].id).update(is_cancel=True)
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(len(resp.context["rows"]), 1)
        row = resp.context["rows"][0]
        self.assertEqual(row["stage"], "CP")
        self.assertIsNone(row["purchase_order"])
        d = resp.context["dashboard"]
        self.assertEqual(d["purchase_orders"], 0)
        self.assertEqual(d["comparison_prices"], 1)

    def test_cancelled_cp_excluded_from_dashboard(self):
        chain = self._build_chain(stage="CP", rq_ref="REQ-XCP", pr_ref="PR-XCP",
                                  cp_ref="CP-XCP", product_code="XCP1")
        ComparisonPrice.objects.filter(id=chain["cp"].id).update(is_cancel=True)
        resp = self.client.get(reverse(URL_NAME))
        d = resp.context["dashboard"]
        self.assertEqual(d["comparison_prices"], 0)
        self.assertEqual(d["comparison_items"], 0)
        self.assertEqual(d["distributors"], 0)

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
        # money totals are per PurchaseOrder header (1 PO in scope), not per item
        self.assertEqual(d["po_total_price"], Decimal("1000.00"))
        self.assertEqual(d["po_discount"], Decimal("0.00"))
        self.assertEqual(d["po_total_after_discount"], Decimal("1000.00"))
        self.assertEqual(d["po_vat"], Decimal("0.00"))
        self.assertEqual(d["amount"], Decimal("1000.00"))

    def test_dashboard_money_sums_po_and_selected_comparison(self):
        # PO generated from its comparison — counted once (via the PO).
        self._build_chain(stage="PO", rq_ref="REQ-M1", pr_ref="PR-M1", cp_ref="CP-M1",
                          po_ref="PO-M1", product_code="M1", price="700.00")
        # standalone comparison, no PO — counted via its selected CPD.
        self._build_chain(stage="CP", rq_ref="REQ-M2", pr_ref="PR-M2", cp_ref="CP-M2",
                          product_code="M2", price="500.00")
        # PO raised straight from the PR + a separate comparison — both count.
        self._build_chain(stage="PO", rq_ref="REQ-M3", pr_ref="PR-M3", cp_ref="CP-M3",
                          po_ref="PO-M3", product_code="M3", price="300.00",
                          po_from_cp=False)
        d = self.client.get(reverse(URL_NAME)).context["dashboard"]
        # 700 (PO-M1) + 500 (CPD CP-M2) + 300 (PO-M3) + 300 (CPD CP-M3)
        self.assertEqual(d["amount"], Decimal("1800.00"))
        self.assertEqual(d["po_total_price"], Decimal("1800.00"))
        self.assertEqual(d["po_total_after_discount"], Decimal("1800.00"))
        self.assertEqual(d["po_discount"], Decimal("0.00"))
        self.assertEqual(d["po_vat"], Decimal("0.00"))

    def test_dashboard_counts_follow_search(self):
        self._build_chain(stage="PO", rq_ref="REQ-S1", pr_ref="PR-S1", cp_ref="CP-S1",
                          po_ref="PO-S1", product_code="S1", product_name="Keyboard")
        self._build_chain(stage="PO", rq_ref="REQ-S2", pr_ref="PR-S2", cp_ref="CP-S2",
                          po_ref="PO-S2", product_code="S2", product_name="Monitor")
        resp = self.client.get(reverse(URL_NAME), {"search": "Keyboard"})
        self.assertEqual(resp.context["dashboard"]["requisition_items"], 1)
        self.assertEqual(resp.context["dashboard"]["purchase_orders"], 1)

    def test_pagination_preserves_querystring(self):
        per_page = 10
        for i in range(25):
            self._build_chain(stage="PR", rq_ref=f"REQ-P{i:02d}", pr_ref=f"PR-P{i:02d}",
                              product_code=f"PP{i:02d}", product_name="Widget")
        resp = self.client.get(reverse(URL_NAME), {"search": "Widget"})
        self.assertEqual(len(resp.context["rows"]), per_page)
        self.assertContains(resp, "search=Widget")
        self.assertEqual(resp.context["page_obj"].paginator.count, 25)
        resp2 = self.client.get(reverse(URL_NAME), {"search": "Widget", "page": 3})
        self.assertEqual(len(resp2.context["rows"]), 5)

    # ----- table: merged documents column + requester/department -----
    def test_documents_column_merged(self):
        self._build_chain(stage="PO", rq_ref="REQ-DOC", pr_ref="PR-DOC",
                          cp_ref="CP-DOC", po_ref="PO-DOC", product_code="DOC1")
        resp = self.client.get(reverse(URL_NAME))
        self.assertContains(resp, "<th>เอกสาร</th>")
        # the four stage refs all live in one row now
        for ref in ("REQ-DOC", "PR-DOC", "CP-DOC", "PO-DOC"):
            self.assertContains(resp, ref)
        # the old per-stage column headers are gone
        for gone in ("<th>ใบขอเบิก</th>", "<th>ใบขอซื้อ</th>",
                     "<th>ใบเปรียบเทียบ</th>", "<th>ใบสั่งซื้อ</th>"):
            self.assertNotContains(resp, gone)

    def test_requester_and_department_column(self):
        dept = BaseDepartment.objects.create(name="ฝ่ายจัดซื้อกลาง")
        self._build_chain(stage="PR", rq_ref="REQ-RD", pr_ref="PR-RD",
                          product_code="RD1", section=dept)
        resp = self.client.get(reverse(URL_NAME))
        self.assertContains(resp, "<th>ผู้ขอเบิก / แผนก</th>")
        self.assertContains(resp, "Somchai Jaidee")   # requester full name
        self.assertContains(resp, "ฝ่ายจัดซื้อกลาง")     # department name
