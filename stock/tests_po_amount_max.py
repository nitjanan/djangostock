import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BaseDelivery,
    BasePermission,
    BasePOType,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    Distributor,
    PurchaseOrder,
)
from stock.forms import PurchaseOrderPriceForm
from stock.views import check_po_amount_over_max, po_amount_max_without_cp


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class POAmountMaxTestCase(TestCase):
    """บันทึกและส่งอนุมัติใบสั่งซื้อ: ยอดตั้งแต่วงเงิน ap_amount_max ของสิทธิ CAAPO ขึ้นไป แจ้งเตือนและห้ามบันทึก"""

    def setUp(self):
        self.user = User.objects.create_superuser(username='tester_po_max', password='password')
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_po_max", name="Test Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(id="po_type_max", name="Standard PO")
        self.delivery = BaseDelivery.objects.create(name="คลังสินค้า")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")

        self.caapo = BasePermission.objects.create(
            name='can approve approver PO', codename='CAAPO', codename_th='อนุมัติใบสั่งซื้อ',
            ap_amount_max=Decimal('5000.00'),
        )

    def _create_po(self, cp=None, approver_status_id=1):
        return PurchaseOrder.objects.create(
            cp=cp,
            vat_type=self.vat_type,
            ref_no="PO-MAX-%s" % PurchaseOrder.objects.count(),
            distributor=self.distributor,
            credit=self.credit,
            stockman_user=self.user,
            approver_user=self.user,
            branch_company=self.branch,
            address_company=self.address,
            po_type=self.po_type,
            approver_status_id=approver_status_id,
            amount=Decimal('6000.00'),
            is_draft=True,
            due_receive_update=datetime.date(2026, 7, 20),
        )

    def _edit_url(self, po):
        return reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'True', 'isReApprove': 'False'})

    def test_helper_returns_caapo_max_for_po_without_cp(self):
        self.assertEqual(po_amount_max_without_cp(self._create_po()), '5000.00')

    def test_helper_skips_po_from_comparison_price(self):
        cp = ComparisonPrice.objects.create(organizer=self.user, branch_company=self.branch, address_company=self.address)
        self.assertIsNone(po_amount_max_without_cp(self._create_po(cp=cp)))

    def test_helper_skips_when_max_not_set(self):
        self.caapo.ap_amount_max = None
        self.caapo.save()
        self.assertIsNone(po_amount_max_without_cp(self._create_po()))

    def test_edit_page_renders_amount_max_on_submit_button(self):
        response = self.client.get(self._edit_url(self._create_po()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['poAmountMax'], '5000.00')
        self.assertContains(response, 'data-amount-max="5000.00"')
        self.assertContains(response, 'function checkPOAmountOverMax')

    def test_create_page_renders_amount_max_on_submit_button(self):
        response = self.client.get(reverse('createPOItem', kwargs={'po_id': self._create_po().id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-amount-max="5000.00"')
        self.assertContains(response, 'function checkPOAmountOverMax')

    def _price_data(self, amount, save_draft=''):
        return {
            'total_price': amount, 'discount': '0.00', 'total_after_discount': amount,
            'vat': '0.00', 'amount': amount, 'freight': '0.00', 'note': '',
            'delivery': self.delivery.id, 'save_draft': save_draft,
        }

    def test_check_adds_error_when_amount_equals_max(self):
        #ตั้งแต่ 5,000 ขึ้นไปต้องมีใบเปรียบเทียบราคา (เท่ากับวงเงินพอดีก็ห้าม)
        po = self._create_po()
        form = PurchaseOrderPriceForm(self._price_data('5000.00'), instance=po)
        self.assertTrue(form.is_valid())
        self.assertFalse(check_po_amount_over_max(form, po))
        self.assertIn('กรุณาออกใบเปรียบเทียบราคาก่อน เนื่องจากยอดเงินตั้งแต่ 5,000.00 บาทขึ้นไป', form.errors['amount'][0])

    def test_check_passes_when_amount_below_max(self):
        po = self._create_po()
        form = PurchaseOrderPriceForm(self._price_data('4999.99'), instance=po)
        self.assertTrue(form.is_valid())
        self.assertTrue(check_po_amount_over_max(form, po))

    def _post_create(self, po, amount, save_draft=''):
        data = {
            'form-TOTAL_FORMS': '0', 'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
        }
        data.update(self._price_data(amount, save_draft))
        return self.client.post(reverse('createPOItem', kwargs={'po_id': po.id}), data)

    def test_create_submit_over_max_is_blocked(self):
        po = self._create_po()
        response = self._post_create(po, '6000.00')
        self.assertEqual(response.status_code, 200)
        po.refresh_from_db()
        #ไม่ได้บันทึก: ยังเป็นแบบร่างเหมือนเดิม
        self.assertTrue(po.is_draft)
        self.assertContains(response, 'กรุณาออกใบเปรียบเทียบราคาก่อน')

    def test_create_submit_within_max_is_saved(self):
        po = self._create_po()
        response = self._post_create(po, '4999.99')
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)
        self.assertEqual(po.amount, Decimal('4999.99'))

    def test_create_save_draft_over_max_is_allowed(self):
        po = self._create_po()
        response = self._post_create(po, '6000.00', save_draft='1')
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertTrue(po.is_draft)
        self.assertEqual(po.amount, Decimal('6000.00'))

    def _post_edit(self, po, amount, save_draft=''):
        data = {
            'purchaseorderitem_set-TOTAL_FORMS': '0', 'purchaseorderitem_set-INITIAL_FORMS': '0',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0', 'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            # PurchaseOrderForm
            'distributor': self.distributor.id, 'credit': self.credit.id, 'shipping': 'EMS',
            'vat_type': self.vat_type.id, 'address_company': self.address.id,
            'approver_user': self.user.id, 'due_receive_update': '2026-08-25', 'po_type': self.po_type.id,
            # RateDistributorForm
            'price_rate': 5, 'quantity_rate': 5, 'service_rate': 5, 'safety_rate': 5, 'counsel': 'ok',
        }
        data.update(self._price_data(amount, save_draft))
        return self.client.post(self._edit_url(po), data)

    def test_edit_submit_over_max_is_blocked(self):
        po = self._create_po()
        response = self._post_edit(po, '6000.00')
        self.assertEqual(response.status_code, 200)
        po.refresh_from_db()
        self.assertTrue(po.is_draft)
        self.assertContains(response, 'กรุณาออกใบเปรียบเทียบราคาก่อน')

    def test_edit_submit_within_max_is_saved(self):
        po = self._create_po()
        response = self._post_edit(po, '4999.99')
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertFalse(po.is_draft)

    def test_edit_save_draft_over_max_is_allowed(self):
        po = self._create_po()
        response = self._post_edit(po, '6000.00', save_draft='1')
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        self.assertTrue(po.is_draft)
        self.assertEqual(po.amount, Decimal('6000.00'))

    # ---------- หน้ารายการใบสั่งซื้อ (/purchaseOrder/) ----------

    def _view_po_rows(self, tab=''):
        response = self.client.get(reverse('viewPO') + ('?tab=%s' % tab if tab else ''))
        self.assertEqual(response.status_code, 200)
        return {po.id: po for po in response.context['pos']}, response

    def test_list_marks_pending_po_over_max(self):
        po = self._create_po()
        po.amount = Decimal('5000.00')
        po.is_draft = False
        po.save()
        rows, response = self._view_po_rows()
        self.assertEqual(rows[po.id].over_amount_max, Decimal('5000.00'))
        self.assertContains(response, 'ต้องมีใบเปรียบเทียบราคา')
        self.assertContains(response, 'ยอดตั้งแต่ 5,000.00 บาทขึ้นไป')

    def test_list_does_not_mark_po_within_max_or_from_cp(self):
        within = self._create_po()
        within.amount = Decimal('4999.99')
        within.is_draft = False
        within.save()
        cp = ComparisonPrice.objects.create(organizer=self.user, branch_company=self.branch, address_company=self.address)
        from_cp = self._create_po(cp=cp)
        from_cp.is_draft = False
        from_cp.save()
        rows, response = self._view_po_rows()
        self.assertIsNone(rows[within.id].over_amount_max)
        self.assertIsNone(rows[from_cp.id].over_amount_max)
        self.assertNotContains(response, 'ต้องมีใบเปรียบเทียบราคา')

    def test_list_does_not_mark_approved_po(self):
        po = self._create_po(approver_status_id=2)
        po.is_draft = False
        po.save()
        rows, _ = self._view_po_rows()
        self.assertIsNone(rows[po.id].over_amount_max)
