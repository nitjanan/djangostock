from decimal import Decimal

from django.contrib.auth.models import Group, User
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
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    RateDistributor,
    Requisition,
    RequisitionItem,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PurchaseOrderFromPRSinglePageTestCase(TestCase):
    """สร้างใบสั่งซื้อจากหน้า createCMorPO: กรอกข้อมูลผู้จำหน่าย ประเมินร้านค้า และรายการสินค้า
    ในหน้าเดียว (editPOItem) แทนการผ่านหน้า editPOFromPR ก่อน"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='po_from_pr_user', password='password')
        self.client.login(username='po_from_pr_user', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        BaseVatType.objects.create(id="0", name="-")  #ใบสั่งซื้อที่สร้างจาก createCMorPO เริ่มที่ชนิดภาษี 0
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_from_pr", name="Test Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(id="po_type_from_pr", name="Standard PO")
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        self.delivery = BaseDelivery.objects.create(name="คลังสินค้า")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")

        profile = UserProfile.objects.create(user=self.user)
        profile.branch_company.add(self.branch)

        self.requisit = Requisition.objects.create(
            purchase_requisition_id=1, pr_ref_no="PR-SINGLE-001", name=self.user,
            chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        self.pr = PurchaseRequisition.objects.create(
            requisition=self.requisit, branch_company=self.branch, address_company=self.address
        )
        self.req_item = RequisitionItem.objects.create(
            requisition_id=self.requisit.id, requisit=self.requisit, product_name="Test Item 1",
            quantity=5, quantity_pr=5,
        )

    def _create_po_from_pr(self):
        response = self.client.post(
            reverse('createCMorPO', args=(self.pr.id,)),
            {'btnformPO': '1', 'choices': [self.req_item.id]},
        )
        po = PurchaseOrder.objects.get(pr=self.pr)
        return response, po

    def _edit_url(self, po):
        return reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'True', 'isReApprove': 'False'})

    def test_create_po_goes_straight_to_edit_page(self):
        response, po = self._create_po_from_pr()
        self.assertRedirects(response, self._edit_url(po), fetch_redirect_response=False)

    def test_edit_page_from_pr_shows_distributor_and_rate_sections(self):
        _, po = self._create_po_from_pr()
        html = self.client.get(self._edit_url(po)).content.decode('utf-8')
        self.assertIn('id="id-form-distributor"', html)
        self.assertIn('id="id_vat_type"', html)
        self.assertIn('name="rate-price"', html)
        self.assertIn('name="price_rate"', html)
        #ส่วนข้อมูลผู้จำหน่าย/ประเมินร้านค้าต้องไม่ถูกซ่อน
        self.assertNotIn('<div class="row hidden-print d-none">', html)

    def test_distributor_lookup_returns_header_details(self):
        #ใช้เปลี่ยนผู้จำหน่ายที่หัวเอกสารเมื่อเลือกผู้จำหน่ายใหม่
        self.distributor.address = '1 ถนนทดสอบ'
        self.distributor.tel = '02-000-0000'
        self.distributor.save()
        data = self.client.get(reverse('searchDataDistributor'), {'id_distributor': self.distributor.id}).json()
        self.assertEqual(data['credit'], self.credit.id)
        self.assertEqual(data['vat_type'], self.vat_type.id)
        self.assertEqual(
            (data['id'], data['name'], data['address'], data['tel']),
            (self.distributor.id, 'Test Distributor', '1 ถนนทดสอบ', '02-000-0000'),
        )

    def test_edit_page_embeds_address_company_details(self):
        _, po = self._create_po_from_pr()
        html = self.client.get(self._edit_url(po)).content.decode('utf-8')
        self.assertIn('id="address-company-info"', html)
        self.assertIn('123 Test St', html)

    def _edit_data(self, po, item, **override):
        data = {
            'purchaseorderitem_set-TOTAL_FORMS': '1', 'purchaseorderitem_set-INITIAL_FORMS': '1',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0', 'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            'purchaseorderitem_set-0-id': item.id, 'purchaseorderitem_set-0-po': po.id,
            'purchaseorderitem_set-0-item': self.req_item.id,
            'purchaseorderitem_set-0-quantity': '5.0000', 'purchaseorderitem_set-0-unit': self.unit.id,
            'purchaseorderitem_set-0-unit_price': '20.0000', 'purchaseorderitem_set-0-price': '100.00',
            'distributor': self.distributor.id, 'credit': self.credit.id, 'shipping': 'EMS',
            'vat_type': self.vat_type.id, 'address_company': self.address.id,
            'approver_user': '', 'due_receive_update': '2026-08-25', 'po_type': self.po_type.id,
            'price_rate': 4, 'quantity_rate': 3, 'service_rate': 4, 'safety_rate': 3, 'counsel': 'ok',
            'total_price': '100.00', 'discount': '0.00', 'total_after_discount': '100.00',
            'freight': '0.00', 'vat': '7.00', 'amount': '107.00', 'note': '',
            'delivery': self.delivery.id, 'save_draft': '',
        }
        data.update(override)
        return data

    def test_save_once_stores_distributor_rate_and_items(self):
        _, po = self._create_po_from_pr()
        item = PurchaseOrderItem.objects.get(po=po)
        response = self.client.post(self._edit_url(po), self._edit_data(po, item))
        self.assertRedirects(response, reverse('viewPO'), fetch_redirect_response=False)

        po.refresh_from_db()
        self.assertEqual(po.distributor_id, self.distributor.id)
        self.assertEqual(po.vat_type_id, self.vat_type.id)
        self.assertEqual(po.shipping, 'EMS')
        self.assertEqual(po.amount, Decimal('107.00'))
        self.assertFalse(po.is_draft)

        item.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal('20.0000'))

        rate = RateDistributor.objects.get(po=po)
        self.assertEqual((rate.price_rate, rate.quantity_rate, rate.service_rate, rate.safety_rate), (4, 3, 4, 3))
        self.assertEqual(rate.organizer_user, self.user)

    # ---------- ผู้อนุมัติใบสั่งซื้อ required สำหรับผู้ที่เลือกผู้อนุมัติได้ ----------
    def _po_for_approver_chooser(self):
        #กลุ่มจัดซื้อเลือกผู้อนุมัติใบที่ออกจากใบขอซื้อได้ (can_edit_approver_user_po)
        self.user.groups.add(Group.objects.get_or_create(name='จัดซื้อ')[0])
        approver = User.objects.create_user(username='po_from_pr_appr', password='password')
        _, po = self._create_po_from_pr()
        po.approver_user = approver  #ให้อยู่ในตัวเลือก dropdown (include_user)
        po.save()
        return po, PurchaseOrderItem.objects.get(po=po), approver

    def test_approver_required_when_sending(self):
        po, item, _ = self._po_for_approver_chooser()
        response = self.client.post(self._edit_url(po), self._edit_data(po, item, approver_user=''))
        self.assertEqual(response.status_code, 200)
        self.assertIn('approver_user', response.context['form'].errors)
        po.refresh_from_db()
        self.assertNotEqual(po.shipping, 'EMS')

    def test_approver_can_be_blank_when_saving_draft(self):
        po, item, _ = self._po_for_approver_chooser()
        response = self.client.post(self._edit_url(po), self._edit_data(po, item, approver_user='', save_draft='1'))
        self.assertRedirects(response, reverse('viewPO'), fetch_redirect_response=False)
        po.refresh_from_db()
        self.assertTrue(po.is_draft)
        self.assertIsNone(po.approver_user)

    def test_approver_selected_saves(self):
        po, item, approver = self._po_for_approver_chooser()
        response = self.client.post(self._edit_url(po), self._edit_data(po, item, approver_user=approver.id))
        self.assertRedirects(response, reverse('viewPO'), fetch_redirect_response=False)
        po.refresh_from_db()
        self.assertEqual(po.approver_user, approver)

    def test_approver_field_marked_required_on_page(self):
        po, _, _ = self._po_for_approver_chooser()
        form = self.client.get(self._edit_url(po)).context['form']
        self.assertTrue(form.fields['approver_user'].required)

    def test_approver_not_required_for_user_who_cannot_choose(self):
        #ผู้ใช้ที่ไม่มีสิทธิเลือกผู้อนุมัติ ช่องนี้ถูกซ่อน จึงไม่บังคับ
        _, po = self._create_po_from_pr()
        form = self.client.get(self._edit_url(po)).context['form']
        self.assertFalse(form.fields['approver_user'].required)

    # ---------- ปุ่มปริ้นหน้าแก้ไข โหลดหน้า showPO ใน iframe ----------
    def test_show_po_can_be_framed_by_same_site_only(self):
        _, po = self._create_po_from_pr()
        response = self.client.get(reverse('showPO', kwargs={'po_id': po.id, 'mode': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')
