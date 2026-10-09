from decimal import Decimal

import xlrd
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from stock.filters import PurchaseOrderItemFilter
from stock.models import (
    BaseAddress, BaseApproveStatus, BaseBranchCompany, BaseUnit, BaseVatType,
    Category, ComparisonPrice, Distributor, Product, PurchaseOrder, PurchaseOrderItem,
    PurchaseRequisition, Requisition, RequisitionItem, UserProfile,
)


class _POItemFixture(TestCase):
    """Shared fixture for /report/purchaseOrder/item tests. Holds no tests of its own."""

    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        cls.vat = BaseVatType.objects.create(id="1", name="VAT 7%")
        cls.unit = BaseUnit.objects.create(name="ชิ้น")
        cls.status = BaseApproveStatus.objects.create(id=2, name="อนุมัติ")
        cls.category = Category.objects.create(name="Cat", slug="cat")
        cls.user = User.objects.create_user(username="reporter", password="pw")
        UserProfile.objects.create(user=cls.user).branch_company.add(cls.branch)
        cls.distributor = Distributor.objects.create(id="D-1", name="Shop")

        # PO ที่ po.pr = PR-A แต่มีสินค้าจาก PR-A และ PR-B
        pr_a = cls._pr("PR-A")
        cls.po_from_pr = cls._po("PO-1", pr=pr_a)
        cls.item_a = cls._item(cls.po_from_pr, "P-001", "PR-A", "100")
        cls.item_b = cls._item(cls.po_from_pr, "P-002", "PR-B", "200")
        # PO ที่สร้างจากใบเปรียบ ไม่มี po.pr แต่สินค้ามาจาก PR-C
        cp = ComparisonPrice.objects.create(organizer=cls.user, branch_company=cls.branch,
                                            address_company=cls.address, ref_no="CP-9",
                                            select_bidder=cls.distributor)
        cls.po_from_cp = cls._po("PO-2", cp=cp)
        cls.item_c = cls._item(cls.po_from_cp, "P-003", "PR-C", "300")

    @classmethod
    def _pr(cls, ref_no):
        return PurchaseRequisition.objects.create(ref_no=ref_no, branch_company=cls.branch,
                                                  address_company=cls.address)

    @classmethod
    def _po(cls, ref_no, pr=None, cp=None):
        return PurchaseOrder.objects.create(
            vat_type=cls.vat, distributor=cls.distributor, approver_status=cls.status,
            address_company=cls.address, branch_company=cls.branch, ref_no=ref_no, pr=pr, cp=cp,
            total_price=Decimal("1"), total_after_discount=Decimal("1"), vat=Decimal("0"),
            amount=Decimal("1"),
        )

    @classmethod
    def _item(cls, po, product_code, pr_ref_no, unit_price):
        rq = Requisition.objects.create(
            name=cls.user, chief_approve_user_name=cls.user, supplies_approve_user_name=cls.user,
            branch_company=cls.branch, address_company=cls.address,
            ref_no="RQ-" + product_code, pr_ref_no=pr_ref_no,
        )
        product = Product.objects.create(id=product_code, name=product_code,
                                         slug="slug-" + product_code, category=cls.category)
        item = RequisitionItem.objects.create(requisition_id=rq.id, requisit=rq, product=product,
                                              product_name=product_code, quantity=Decimal("1"))
        return PurchaseOrderItem.objects.create(po=po, item=item, unit=cls.unit, quantity=Decimal("1"),
                                                unit_price=Decimal(unit_price), price=Decimal(unit_price))

    def _client(self):
        client = Client()
        client.login(username="reporter", password="pw")
        session = client.session
        session["company_code"] = "HO"
        session.save()
        return client


class PurchaseOrderItemFilterTestCase(_POItemFixture):
    """Filters on /report/purchaseOrder/item and the Excel exports launched from it."""

    def _filter(self, params):
        return list(PurchaseOrderItemFilter(params, queryset=PurchaseOrderItem.objects.all()).qs)

    # ----- filter -----
    def test_pr_ref_no_matches_pr_shown_on_row(self):
        self.assertEqual(self._filter({"pr_ref_no": "PR-B"}), [self.item_b])
        self.assertEqual(self._filter({"pr_ref_no": "PR-A"}), [self.item_a])

    def test_pr_ref_no_finds_items_of_po_created_from_cp(self):
        self.assertEqual(self._filter({"pr_ref_no": "PR-C"}), [self.item_c])

    def test_invalid_unit_price_is_ignored(self):
        f = PurchaseOrderItemFilter({"unit_price_min": "abc"}, queryset=PurchaseOrderItem.objects.all())
        self.assertIn("unit_price_min", f.form.errors)
        self.assertEqual(len(f.qs), 3)

    # ----- excel export ใช้ filter ชุดเดียวกับหน้าเว็บ -----
    def _export_first_column(self, url_name, params):
        resp = self._client().get(reverse(url_name), params)
        sheet = xlrd.open_workbook(file_contents=resp.content).sheet_by_index(0)
        return [sheet.cell_value(r, 0) for r in range(1, sheet.nrows)]

    def test_export_by_product_value_respects_ref_no_filters(self):
        for params, expected in (({"po_ref_no": "PO-2"}, "P-003"), ({"pr_ref_no": "PR-B"}, "P-002"),
                                 ({"cp_ref_no": "CP-9"}, "P-003")):
            col = self._export_first_column("exportExcelSummaryByProductValue", params)
            products = [c for c in col if str(c).startswith("P-")]
            self.assertEqual(products, [expected], params)

    def test_export_by_product_frequently_respects_ref_no_filters(self):
        col = self._export_first_column("exportExcelSummaryByProductFrequently", {"po_ref_no": "PO-1"})
        self.assertCountEqual([c for c in col if str(c).startswith("P-")], ["P-001", "P-002"])

    def test_export_by_distributor_frequently_respects_ref_no_filters(self):
        col = self._export_first_column("exportExcelSummaryByDistributorFrequently", {"pr_ref_no": "NOPE"})
        self.assertNotIn("D-1", col)
        col = self._export_first_column("exportExcelSummaryByDistributorFrequently", {"pr_ref_no": "PR-C"})
        self.assertIn("D-1", col)

    def test_export_by_distributor_product_discount_counts_filtered_po_only(self):
        PurchaseOrderItem.objects.filter(pk=self.item_a.pk).update(discount="10")
        PurchaseOrderItem.objects.filter(pk=self.item_c.pk).update(discount="30")
        resp = self._client().get(reverse("exportExcelSummaryByDistributorFrequently"), {"po_ref_no": "PO-2"})
        sheet = xlrd.open_workbook(file_contents=resp.content).sheet_by_index(0)
        self.assertEqual(sheet.cell_value(1, 0), "D-1")
        self.assertEqual(sheet.cell_value(1, 2), 30)


class ExcelDiscountTestCase(_POItemFixture):
    """discount on PurchaseOrderItem / PurchaseOrder is free text: a plain amount
    or "x%". Excel totals must turn "%" into baht like calculateUnitDiscount() /
    calculateDiscount() in the PO templates, not let the database cast "10%" to 10."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # PO-1: รายการ A 1 x 100 ลด 10% = 10, รายการ B 1 x 200 ลด 5 บาท = 5 / ท้ายบิล 5% ของ 1000 = 50
        PurchaseOrderItem.objects.filter(pk=cls.item_a.pk).update(discount="10%")
        PurchaseOrderItem.objects.filter(pk=cls.item_b.pk).update(discount="5")
        PurchaseOrder.objects.filter(pk=cls.po_from_pr.pk).update(discount="5%", total_price=Decimal("1000"))
        # PO-2: รายการ C 1 x 300 ลด 20% = 60 / ท้ายบิล 7 บาท
        PurchaseOrderItem.objects.filter(pk=cls.item_c.pk).update(discount="20%")
        PurchaseOrder.objects.filter(pk=cls.po_from_cp.pk).update(discount="7", total_price=Decimal("300"))

    def test_export_by_distributor_discount_columns(self):
        resp = self._client().get(reverse("exportExcelSummaryByDistributorFrequently"))
        sheet = xlrd.open_workbook(file_contents=resp.content).sheet_by_index(0)
        self.assertEqual(sheet.cell_value(1, 0), "D-1")
        self.assertAlmostEqual(sheet.cell_value(1, 2), 75)  # 10 + 5 + 60
        self.assertAlmostEqual(sheet.cell_value(1, 4), 57)  # 50 + 7
        self.assertEqual(sheet.cell_value(2, 0), "รวมทั้งสิ้น")
        self.assertAlmostEqual(sheet.cell_value(2, 2), 75)
        self.assertAlmostEqual(sheet.cell_value(2, 4), 57)

    def test_export_po_item_discount_column(self):
        import io
        import pandas as pd
        resp = self._client().get(reverse("exportExcelPO"))
        df = pd.read_excel(io.BytesIO(resp.content))
        by_ref = dict(zip(df["เลขที่"], df["รวมส่วนลดสินค้า"]))
        self.assertAlmostEqual(float(by_ref["PO-1"]), 15)
        self.assertAlmostEqual(float(by_ref["PO-2"]), 60)
