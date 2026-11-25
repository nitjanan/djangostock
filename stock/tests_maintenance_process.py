import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from stock.maintenance_process import pr_status
from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCar,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceItem,
    Distributor,
    Invoice,
    Maintenance,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
)


class MaintenanceProcessApiTestCase(TestCase):
    """API ให้ dashboard: ใบแจ้งซ่อม -> ใบขอเบิก -> ใบขอซื้อ / เปรียบเทียบราคา / ใบสั่งซื้อ / ใบจ่ายสินค้า"""

    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.branch, address=cls.address)
        cls.vat = BaseVatType.objects.create(id="1", name="VAT 7%")
        for pk, name in [(1, "รอดำเนินการ"), (2, "อนุมัติ"), (3, "ไม่อนุมัติ"), (4, "ไม่ดำเนินการ")]:
            BaseApproveStatus.objects.create(id=pk, name=name)
        cls.car = BaseCar.objects.create(id="1", name="รถ 1")
        cls.user = User.objects.create_user(username="dashboard_api", password="pw")
        cls.distributor = Distributor.objects.create(id="D1", name="ร้านอะไหล่")
        cls.created = datetime.datetime(2026, 11, 3, 8, 30)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _get(self, start="2026-11-01", end="2026-11-30"):
        url = reverse("getapiMaintenanceProcess", args=[start, end])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        return res.json()

    def _ma(self, **kwargs):
        defaults = dict(
            branch_company=self.branch, car=self.car, created=self.created,
            broke_reason="ล้อระเบิด", approve_status="อนุมัติซ่อมบำรุง",
        )
        return Maintenance.objects.create(**{**defaults, **kwargs})

    def _rq(self, ma, ref_no="RQ-1"):
        rq = Requisition.objects.create(
            name=self.user, chief_approve_user_name=self.user,
            supplies_approve_user_name=self.user, branch_company=self.branch,
            address_company=self.address, ref_no=ref_no, ma_id=ma.id, ma_ref_no=ma.ref_no,
        )
        item = RequisitionItem.objects.create(
            requisition_id=rq.id, requisit=rq, product_name="ยาง", quantity=Decimal("1"),
        )
        return rq, item

    def _po(self, items, ref_no, **kwargs):
        po = PurchaseOrder.objects.create(
            ref_no=ref_no, vat_type=self.vat, distributor=self.distributor,
            branch_company=self.branch, address_company=self.address, is_draft=False, **kwargs,
        )
        for item in items:
            PurchaseOrderItem.objects.create(po=po, item=item, quantity=Decimal("1"))
        return po

    def test_requires_login(self):
        url = reverse("getapiMaintenanceProcess", args=["2026-11-01", "2026-11-30"])
        self.assertEqual(APIClient().get(url).status_code, 401)

    def test_job_without_requisition(self):
        ma = self._ma(approve_status="ขออนุมัติซ่อมบำรุง")
        [row] = self._get()
        self.assertEqual(row["id"], ma.id)
        self.assertEqual(row["ref_no"], ma.ref_no)
        self.assertEqual(row["broke_reason"], "ล้อระเบิด")
        self.assertEqual(row["approve_status"], "ขออนุมัติซ่อมบำรุง")
        self.assertIsNone(row["chief_update"])
        self.assertEqual(row["requisitions"], [])

    def test_excludes_cancelled_jobs_and_out_of_range(self):
        self._ma(is_cancel=True)
        self._ma(created=datetime.datetime(2026, 10, 31, 23))
        self.assertEqual(self._get(), [])

    def test_full_chain_with_po_from_pr(self):
        ma = self._ma()
        rq, item = self._rq(ma)
        PurchaseRequisition.objects.create(
            requisition=rq, branch_company=self.branch, address_company=self.address,
            ref_no="PR-1", purchase_status_id=2, approver_status_id=2,
        )
        self._po(
            [item], "PO-1", approver_status_id=2, is_receive=False,
            due_receive_update=datetime.date(2026, 11, 21), amount=Decimal("3900.00"),
        )

        [row] = self._get()
        [rq_row] = row["requisitions"]
        self.assertEqual(rq_row["ref_no"], "RQ-1")
        self.assertEqual([(p["ref_no"], p["status"]) for p in rq_row["purchase_requisitions"]],
                         [("PR-1", "approved")])
        [po] = rq_row["purchase_orders"]
        self.assertEqual(po["ref_no"], "PO-1")
        self.assertEqual(po["status"], "approved")
        self.assertFalse(po["is_receive"])
        self.assertEqual(po["due_receive_update"], "2026-11-21")
        self.assertEqual(po["amount"], 3900.0)

    def test_purchased_parts_come_from_approved_po_lines(self):
        ma = self._ma()
        rq, item = self._rq(ma)
        item2 = RequisitionItem.objects.create(
            requisition_id=rq.id, requisit=rq, product_name="กระทะล้อ", quantity=Decimal("1"),
        )
        unit = BaseUnit.objects.create(name="เส้น")
        po = self._po([], "PO-OK", approver_status_id=2)
        PurchaseOrderItem.objects.create(
            po=po, item=item, quantity=Decimal("2"), unit=unit, price=Decimal("8000.00"),
            is_receive=True,
        )
        # ใบที่ยังไม่อนุมัติ ยังไม่นับเป็นอะไหล่ที่ใช้
        self._po([item2], "PO-WAIT", approver_status_id=1)

        [row] = self._get()
        self.assertEqual(row["parts"]["purchased"], [{
            "source": "PO", "received": True, "docnum": "PO-OK",
            "docdat": PurchaseOrder.objects.get(id=po.id).created.isoformat(),
            "stkcod": "", "name": "ยาง", "stktyp": "",
            "qty": 2.0, "unit": "เส้น", "amount": 8000.0,
        }])

    def test_po_from_comparison_without_pr_is_linked_through_items(self):
        ma = self._ma()
        rq, item = self._rq(ma)
        item2 = RequisitionItem.objects.create(
            requisition_id=rq.id, requisit=rq, product_name="กระทะล้อ", quantity=Decimal("1"),
        )
        cp = ComparisonPrice.objects.create(
            organizer=self.user, branch_company=self.branch, address_company=self.address,
            ref_no="CP-1", approver_status_id=1,
        )
        ComparisonPriceItem.objects.create(item=item, cp=cp.id, quantity=Decimal("1"))
        ComparisonPriceItem.objects.create(item=item2, cp=cp.id, quantity=Decimal("1"))
        # PO ใบเดียวมีหลายรายการ ต้องไม่ซ้ำ
        self._po([item, item2], "PO-CP", cp=cp, approver_status_id=1)

        [rq_row] = self._get()[0]["requisitions"]
        self.assertEqual(rq_row["purchase_requisitions"], [])
        self.assertEqual([(c["ref_no"], c["status"]) for c in rq_row["comparisons"]],
                         [("CP-1", "pending")])
        self.assertEqual([p["ref_no"] for p in rq_row["purchase_orders"]], ["PO-CP"])

    def test_skips_cancelled_po_and_draft_pr(self):
        ma = self._ma()
        rq, item = self._rq(ma)
        PurchaseRequisition.objects.create(
            requisition=rq, branch_company=self.branch, address_company=self.address,
            ref_no="PR-DRAFT", is_draft=True,
        )
        self._po([item], "PO-CANCEL", is_cancel=True)

        [rq_row] = self._get()[0]["requisitions"]
        self.assertEqual(rq_row["purchase_requisitions"], [])
        self.assertEqual(rq_row["purchase_orders"], [])

    def test_issued_from_stock_shows_invoice(self):
        ma = self._ma()
        rq, _ = self._rq(ma)
        Invoice.objects.create(
            ref_no="IV-1", branch_company=self.branch, requisit=rq,
            bring_name=self.user, payer_name=self.user,
        )

        [rq_row] = self._get()[0]["requisitions"]
        self.assertEqual([iv["ref_no"] for iv in rq_row["invoices"]], ["IV-1"])


class PrStatusTestCase(TestCase):
    def test_needs_both_purchase_and_approver(self):
        self.assertEqual(pr_status(2, 2), "approved")
        self.assertEqual(pr_status(2, 1), "pending")
        self.assertEqual(pr_status(None, None), "pending")

    def test_rejected_by_either(self):
        self.assertEqual(pr_status(3, 1), "rejected")
        self.assertEqual(pr_status(2, 3), "rejected")
        self.assertEqual(pr_status(2, 4), "not_proceed")
