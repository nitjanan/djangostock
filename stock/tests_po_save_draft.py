import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BaseDelivery,
    BasePOType,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PurchaseOrderSaveDraftTestCase(TestCase):
    """ใบสั่งซื้อ: ปุ่มบันทึกแบบร่าง (ไม่ส่งไปหาผู้อนุมัติ) และปุ่มบันทึกและส่งอนุมัติ"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='po_draft_user', password='password')
        self.approver = User.objects.create_user(username='po_draft_appr', password='password')
        self.client.login(username='po_draft_user', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_po_draft", name="Test Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(id="po_type_draft", name="Standard PO")
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        self.delivery = BaseDelivery.objects.create(name="คลังสินค้า")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")

        profile = UserProfile.objects.create(user=self.user)
        profile.branch_company.add(self.branch)

        # ใบเปรียบเทียบราคาที่อนุมัติแล้ว -> ใบสั่งซื้อที่ออกจากใบนี้อนุมัติอัตโนมัติตอนส่ง
        self.cp = ComparisonPrice.objects.create(
            organizer=self.user, select_bidder=self.distributor, address_company=self.address,
            branch_company=self.branch, approver_user=self.approver, approver_status_id=2,
        )
        ComparisonPriceDistributor.objects.create(
            cp=self.cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=100.00, amount=107.00,
        )

        self.requisit = Requisition.objects.create(
            purchase_requisition_id=1, pr_ref_no="PR-DRAFT-001", name=self.user,
            chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        PurchaseRequisition.objects.create(requisition=self.requisit, branch_company=self.branch)
        self.req_item = RequisitionItem.objects.create(
            requisition_id=1, requisit=self.requisit, product_name="Test Item 1", quantity=5, quantity_pr=5
        )

    # ---------- helpers ----------
    def _create_po(self, cp=None, with_item=False, **extra):
        data = dict(
            cp=cp, vat_type=self.vat_type, ref_no="PO-DRAFT-001", distributor=self.distributor,
            credit=self.credit, stockman_user=self.user, approver_user=self.approver,
            branch_company=self.branch, address_company=self.address, po_type=self.po_type,
            approver_status_id=1, due_receive_update=datetime.date(2026, 7, 20),
            is_draft=False,  #ใบที่ส่งอนุมัติแล้ว (ค่าเริ่มต้นของ model เป็นแบบร่าง)
        )
        data.update(extra)
        po = PurchaseOrder.objects.create(**data)
        item = None
        if with_item:
            item = PurchaseOrderItem.objects.create(
                po=po, item=self.req_item, quantity=Decimal('5.0000'), unit=self.unit,
                unit_price=Decimal('20.0000'), price=Decimal('100.00'),
            )
        return po, item

    def _price_data(self):
        return {
            'total_price': '100.00', 'discount': '0.00', 'total_after_discount': '100.00',
            'freight': '0.00', 'vat': '7.00', 'amount': '107.00', 'note': '',
            'delivery': self.delivery.id,
        }

    def _post_create_from_cp(self, po, save_draft):
        url = reverse('createPOItemFromComparisonPrice', kwargs={'po_id': po.id})
        data = {
            'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
            'form-0-item': self.req_item.id, 'form-0-quantity': '5.0000', 'form-0-unit': self.unit.id,
            'form-0-unit_price': '20.0000', 'form-0-price': '100.00',
            'save_draft': '1' if save_draft else '',
        }
        data.update(self._price_data())
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        return po

    def _post_edit(self, po, item, save_draft, re_approve='False', **override):
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'True', 'isReApprove': re_approve})
        data = {
            'purchaseorderitem_set-TOTAL_FORMS': '1', 'purchaseorderitem_set-INITIAL_FORMS': '1',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0', 'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            'purchaseorderitem_set-0-id': item.id, 'purchaseorderitem_set-0-po': po.id,
            'purchaseorderitem_set-0-item': self.req_item.id,
            'purchaseorderitem_set-0-quantity': '5.0000', 'purchaseorderitem_set-0-unit': self.unit.id,
            'purchaseorderitem_set-0-unit_price': '20.0000', 'purchaseorderitem_set-0-price': '100.00',
            'distributor': self.distributor.id, 'credit': self.credit.id, 'shipping': 'EMS',
            'vat_type': self.vat_type.id, 'address_company': self.address.id,
            'approver_user': self.approver.id, 'due_receive_update': '2026-08-25',
            'po_type': self.po_type.id,
            'price_rate': 5, 'quantity_rate': 5, 'service_rate': 5, 'safety_rate': 5, 'counsel': 'ok',
            'save_draft': '1' if save_draft else '',
        }
        data.update(self._price_data())
        data.update(override)
        return self.client.post(url, data)

    def _in_approver_queue(self, po):
        return PurchaseOrder.objects.filter(
            id=po.id, approver_status=1, amount__gt=0, is_draft=False, approver_user=self.approver,
        ).exists()

    # ---------- createPOItemFromComparisonPrice ----------
    def test_po_from_cp_save_draft_does_not_auto_approve(self):
        po, _ = self._create_po(cp=self.cp)
        po = self._post_create_from_cp(po, save_draft=True)
        self.assertTrue(po.is_draft)
        self.assertEqual(po.approver_status_id, 1)
        self.assertFalse(self._in_approver_queue(po))

    def test_po_from_cp_save_and_send_auto_approves(self):
        po, _ = self._create_po(cp=self.cp)
        po = self._post_create_from_cp(po, save_draft=False)
        self.assertFalse(po.is_draft)
        self.assertEqual(po.approver_status_id, 2)

    # ---------- editPOItem ----------
    def test_edit_save_draft_hides_po_from_approver(self):
        po, item = self._create_po(with_item=True)
        response = self._post_edit(po, item, save_draft=True)
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertTrue(po.is_draft)
        self.assertFalse(self._in_approver_queue(po))

    def test_edit_save_draft_allows_empty_optional_fields(self):
        po, item = self._create_po(with_item=True)
        response = self._post_edit(
            po, item, save_draft=True, due_receive_update='', shipping='', credit='',
            price_rate='', quantity_rate='', service_rate='', safety_rate='',
        )
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertTrue(po.is_draft)

    def test_edit_save_and_send_puts_po_in_approver_queue(self):
        po, item = self._create_po(with_item=True, is_draft=True)
        response = self._post_edit(po, item, save_draft=False)
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)
        self.assertTrue(self._in_approver_queue(po))

    def test_edit_send_draft_po_from_approved_cp_auto_approves(self):
        po, item = self._create_po(
            cp=self.cp, with_item=True, is_draft=True, total_price=Decimal('100.00'),
            total_after_discount=Decimal('100.00'), vat=Decimal('7.00'), amount=Decimal('107.00'),
        )
        response = self._post_edit(po, item, save_draft=False)
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)
        self.assertEqual(po.approver_status_id, 2)

    def test_approved_po_ignores_save_draft(self):
        po, item = self._create_po(with_item=True, approver_status_id=2)
        response = self._post_edit(po, item, save_draft=True)
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)

    def test_view_po_approve_excludes_draft(self):
        self._create_po(with_item=True, is_draft=True, amount=Decimal('107.00'))
        response = self.client.get(reverse('viewPOApprove'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'PO-DRAFT-001')

    # ---------- แท็ปหน้า /purchaseOrder/ ----------
    def _listed_ids(self, response):
        return {po.id for po in response.context['pos']}

    def test_view_po_process_tab_lists_only_non_draft(self):
        po, _ = self._create_po()
        draft, _ = self._create_po(ref_no="PO-DRAFT-002", is_draft=True)
        response = self.client.get(reverse('viewPO'))
        self.assertEqual(response.context['tab'], 'process')
        self.assertEqual(self._listed_ids(response), {po.id})
        self.assertEqual(response.context['count_process'], 1)
        self.assertEqual(response.context['count_draft'], 1)
        self.assertContains(response, 'cp-tab-header')

    def test_view_po_draft_tab_lists_only_draft(self):
        self._create_po()
        draft, _ = self._create_po(ref_no="PO-DRAFT-002", is_draft=True)
        response = self.client.get(reverse('viewPO'), {'tab': 'draft'})
        self.assertEqual(response.context['tab'], 'draft')
        self.assertEqual(self._listed_ids(response), {draft.id})

    # ---------- ฉบับแก้ไข (ขอเปลี่ยนแปลงรายละเอียดรายการ) ----------
    def _open_re_approve(self, po):
        """กดปุ่ม ขอเปลี่ยนแปลงรายละเอียดรายการ (POST) แล้วเปิดหน้าแก้ไข"""
        from django.contrib.auth.models import Group
        purchasing, _ = Group.objects.get_or_create(name='จัดซื้อ')
        self.user.groups.add(purchasing)
        response = self.client.post(reverse('requestPOReApprove', kwargs={'po_id': po.id}))
        self.assertRedirects(
            response,
            reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'True'}),
        )
        po.refresh_from_db()
        return po

    def _approved_po(self, **extra):
        return self._create_po(
            with_item=True, approver_status_id=2, amount=Decimal('107.00'),
            total_price=Decimal('100.00'), total_after_discount=Decimal('100.00'), vat=Decimal('7.00'), **extra
        )

    def test_re_approve_makes_po_draft_until_sent(self):
        po, item = self._approved_po()
        po = self._open_re_approve(po)
        self.assertEqual(po.approver_status_id, 1)
        self.assertTrue(po.is_re_approve)
        self.assertTrue(po.is_draft)
        #ยังเป็นแบบร่าง ผู้อนุมัติยังไม่เห็น/อนุมัติไม่ได้
        self.assertFalse(self._in_approver_queue(po))

        response = self._post_edit(po, item, save_draft=False, re_approve='True')
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)
        self.assertEqual(po.approver_status_id, 1)
        self.assertTrue(self._in_approver_queue(po))

    def test_re_approve_po_from_approved_cp_is_not_auto_approved(self):
        po, item = self._approved_po(cp=self.cp)
        po = self._open_re_approve(po)
        response = self._post_edit(po, item, save_draft=False, re_approve='True')
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        #ฉบับแก้ไขต้องให้ผู้อนุมัติอนุมัติใหม่ ไม่อนุมัติอัตโนมัติจากใบเปรียบเทียบ
        self.assertEqual(po.approver_status_id, 1)
        self.assertFalse(po.is_draft)

    def test_reopen_sent_re_approve_po_stays_sent(self):
        po, item = self._create_po(with_item=True, approver_status_id=1, is_re_approve=True, amount=Decimal('107.00'))
        po = self._open_re_approve(po)
        self.assertFalse(po.is_draft)
        self.assertTrue(self._in_approver_queue(po))

    def test_open_cancelled_po_for_re_approve_does_not_change_on_get(self):
        po, item = self._approved_po(is_cancel=True, cancel_reason='x')
        po = self._open_re_approve(po)
        self.assertTrue(po.is_cancel)
        self.assertEqual(po.approver_status_id, 2)
        self.assertFalse(po.is_draft)

    def test_re_approve_request_rejects_get(self):
        po, _ = self._approved_po()
        response = self.client.get(reverse('requestPOReApprove', kwargs={'po_id': po.id}))
        self.assertEqual(response.status_code, 405)
        po.refresh_from_db()
        self.assertEqual(po.approver_status_id, 2)
        self.assertFalse(po.is_draft)

    def test_opening_edit_page_with_get_does_not_change_po(self):
        po, _ = self._approved_po()
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'True'})
        self.assertEqual(self.client.get(url).status_code, 200)
        po.refresh_from_db()
        self.assertEqual(po.approver_status_id, 2)
        self.assertFalse(po.is_draft)

    def test_re_approve_request_requires_purchasing_group(self):
        po, _ = self._approved_po()
        response = self.client.post(reverse('requestPOReApprove', kwargs={'po_id': po.id}))
        self.assertEqual(response.status_code, 403)
        po.refresh_from_db()
        self.assertEqual(po.approver_status_id, 2)

    def test_re_approve_request_requires_same_company(self):
        from django.contrib.auth.models import Group
        other = BaseBranchCompany.objects.create(id="2", code="S9", name="Other")
        BranchCompanyBaseAdress.objects.create(branch_company=other, address=self.address)
        po, _ = self._approved_po(branch_company=other, ref_no="PO-OTHER-001")
        self.user.groups.add(Group.objects.get_or_create(name='จัดซื้อ')[0])
        response = self.client.post(reverse('requestPOReApprove', kwargs={'po_id': po.id}))
        self.assertEqual(response.status_code, 403)
        po.refresh_from_db()
        self.assertEqual(po.approver_status_id, 2)

    # ---------- ค่าเริ่มต้นเป็นแบบร่าง ----------
    def test_new_po_starts_as_draft_until_sent(self):
        po = PurchaseOrder.objects.create(
            vat_type=self.vat_type, ref_no="PO-NEW-001", distributor=self.distributor,
            stockman_user=self.user, approver_user=self.approver, branch_company=self.branch,
            address_company=self.address, approver_status_id=1,
        )
        self.assertTrue(po.is_draft)
        item = PurchaseOrderItem.objects.create(
            po=po, item=self.req_item, quantity=Decimal('5.0000'), unit=self.unit,
            unit_price=Decimal('20.0000'), price=Decimal('100.00'),
        )
        self.assertEqual(self._post_edit(po, item, save_draft=False).status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)
        self.assertTrue(self._in_approver_queue(po))
