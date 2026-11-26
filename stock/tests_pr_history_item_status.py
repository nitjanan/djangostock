import datetime

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from stock.filters import PurchaseRequisitionFilter
from stock.models import (
    BaseAddress, BaseApproveStatus, BaseBranchCompany, BaseVatType, PurchaseOrder, PurchaseOrderItem,
    PurchaseRequisition, Requisition, RequisitionItem, UserProfile,
)


class PRHistoryItemStatusTestCase(TestCase):
    """หน้าประวัติใบขอซื้อ: ป้ายสถานะสินค้า (ยังไม่ดำเนินการ / กำลังดำเนินการ / รับสินค้าแล้ว + วันที่รับ) และช่องกรองตามสถานะ
    สถานะรับของมาจาก PO ของสินค้านั้น (po.is_receive / po.receive_update) ไม่ใช่ RequisitionItem.is_receive"""

    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        cls.vat_type = BaseVatType.objects.create(name="Vat 7%")
        cls.user = User.objects.create_user(username="pr-history", password="pw", first_name="สมชาย")
        UserProfile.objects.create(user=cls.user).branch_company.add(cls.branch)
        cls.approved = BaseApproveStatus.objects.get_or_create(id=2, defaults={'name': 'อนุมัติ'})[0]

        cls.pr_wait = cls._pr("PR-WAIT", [dict(quantity_used=None)])
        cls.pr_doing = cls._pr("PR-DOING", [dict(quantity_used=2)])
        cls.pr_received = cls._pr("PR-RECV", [dict(quantity_used=2)])
        cls.pr_mix = cls._pr("PR-MIX", [dict(quantity_used=0), dict(quantity_used=1)])

        #PO ที่ยังไม่รับ -> ยังเป็นกำลังดำเนินการ
        cls._po("PO-OPEN", cls._item(cls.pr_doing))
        #รับ 2 ครั้ง (2 PO) -> แสดงวันที่ล่าสุด
        cls._po("PO-R1", cls._item(cls.pr_received), receive_update=datetime.date(2026, 3, 1), is_receive=True)
        cls._po("PO-R2", cls._item(cls.pr_received), receive_update=datetime.date(2026, 4, 2), is_receive=True)
        #มีแค่วันที่รับ (is_receive ยังเป็น False) ก็ถือว่ารับแล้ว
        cls._po("PO-MIX", cls._item(cls.pr_mix, 1), receive_update=datetime.date(2026, 5, 3))
        #PO ที่ถูกยกเลิกไม่นับ แม้จะรับแล้ว
        cls._po("PO-CANCEL", cls._item(cls.pr_doing), receive_update=datetime.date(2026, 1, 1), is_receive=True,
                is_cancel=True)

    @classmethod
    def _pr(cls, ref_no, items):
        rq = Requisition.objects.create(
            name=cls.user, chief_approve_user_name=cls.user, supplies_approve_user_name=cls.user,
            branch_company=cls.branch, address_company=cls.address, ref_no="RQ-" + ref_no)
        for i, item in enumerate(items):
            #RequisitionItem.is_receive ตั้งเป็น True ไว้ทุกตัว เพื่อยืนยันว่าหน้านี้ไม่ได้ใช้ field นี้แล้ว
            RequisitionItem.objects.create(requisition_id=rq.id, requisit=rq, product_name=f"{ref_no} item {i}",
                                           is_receive=True, **item)
        return PurchaseRequisition.objects.create(
            ref_no=ref_no, requisition=rq, branch_company=cls.branch, address_company=cls.address,
            purchase_status=cls.approved, approver_status=cls.approved)

    @staticmethod
    def _item(pr, index=0):
        return pr.requisition.requisitionitem_set.order_by('id')[index]

    @classmethod
    def _po(cls, ref_no, item, **po_fields):
        po = PurchaseOrder.objects.create(
            ref_no=ref_no, stockman_user=cls.user, branch_company=cls.branch, address_company=cls.address,
            vat_type=cls.vat_type, approver_status=cls.approved, is_draft=False, **po_fields)
        PurchaseOrderItem.objects.create(po=po, item=item, quantity=1)
        return po

    def filtered(self, value):
        qs = PurchaseRequisitionFilter({'item_status': value}, queryset=PurchaseRequisition.objects.all()).qs
        return sorted(pr.ref_no for pr in qs)

    def login(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'HO'   # RequireCompanyCodeMiddleware
        session.save()

    def test_filter_by_item_status(self):
        self.assertEqual(self.filtered('wait'), ['PR-MIX', 'PR-WAIT'])
        self.assertEqual(self.filtered('doing'), ['PR-DOING'])
        self.assertEqual(self.filtered('received'), ['PR-MIX', 'PR-RECV'])

    def test_empty_status_returns_all(self):
        self.assertEqual(self.filtered(''), ['PR-DOING', 'PR-MIX', 'PR-RECV', 'PR-WAIT'])

    def test_pr_with_many_matching_items_listed_once(self):
        rq = self.pr_doing.requisition
        RequisitionItem.objects.create(requisition_id=rq.id, requisit=rq, product_name="extra", quantity_used=5)
        self.assertEqual(self.filtered('doing'), ['PR-DOING'])

    def test_page_shows_badges_with_latest_receive_date(self):
        self.login()
        response = self.client.get(reverse('viewPRHistory'))
        badges = {
            item.product_name: (item.po_received, item.po_receive_date)
            for pr in response.context['prs'] for item in pr.requisition.status_items
        }
        self.assertEqual(badges['PR-RECV item 0'], (True, datetime.date(2026, 4, 2)))
        self.assertEqual(badges['PR-MIX item 1'], (True, datetime.date(2026, 5, 3)))
        self.assertEqual(badges['PR-DOING item 0'], (False, None))
        self.assertEqual(badges['PR-WAIT item 0'], (False, None))

        html = response.content.decode()
        self.assertIn('name="item_status"', html)
        self.assertIn('ist-wait">ยังไม่ดำเนินการ', html)
        self.assertIn('ist-doing">กำลังดำเนินการ', html)
        self.assertIn('ist-received">รับสินค้าแล้ว 02/04/2026', html)

        page = self.client.get(reverse('viewPRHistory'), {'item_status': 'received'})
        self.assertEqual(sorted(pr.ref_no for pr in page.context['prs']), ['PR-MIX', 'PR-RECV'])

    def test_items_loaded_in_one_query(self):
        self.login()
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse('viewPRHistory'))
        item_queries = [q['sql'] for q in ctx.captured_queries if '`RequisitionItem`.`product_name`' in q['sql']]
        self.assertEqual(len(item_queries), 1, item_queries)
