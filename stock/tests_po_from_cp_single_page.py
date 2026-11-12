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
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PurchaseOrderFromCPSinglePageTestCase(TestCase):
    """สร้างใบสั่งซื้อจากใบเปรียบเทียบราคา: กดสร้างแล้วดึงผู้จำหน่าย ราคา รายการสินค้ามาให้
    แล้วกรอกข้อมูลที่เหลือในหน้าเดียว (editPOItem) แทนการผ่าน 2 หน้า
    (createPOFromComparisonPrice -> createPOItemFromComparisonPrice)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='po_from_cp_user', password='password')
        self.approver = User.objects.create_user(username='po_from_cp_appr', password='password')
        self.special_approver = User.objects.create_user(username='po_from_cp_sp', password='password')
        self.client.login(username='po_from_cp_user', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_from_cp", name="Selected Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.other_distributor = Distributor.objects.create(
            id="dist_from_cp_other", name="Other Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")

        profile = UserProfile.objects.create(user=self.user)
        profile.branch_company.add(self.branch)

        self.cp = ComparisonPrice.objects.create(
            organizer=self.user, select_bidder=self.distributor, address_company=self.address,
            branch_company=self.branch, approver_user=self.approver, special_approver_user=self.special_approver,
            examiner_status_id=2, approver_status_id=2, is_draft=False,
        )
        ComparisonPrice.objects.filter(id=self.cp.id).update(
            created=datetime.date(2026, 6, 15), select_bidder_update=datetime.date(2026, 6, 20),
        )
        self.cp.refresh_from_db()

        self.cpd = ComparisonPriceDistributor.objects.create(
            cp=self.cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('150.00'), discount='10.00', total_after_discount=Decimal('140.00'),
            freight=Decimal('5.00'), vat=Decimal('10.15'), amount=Decimal('155.15'),
        )
        other_cpd = ComparisonPriceDistributor.objects.create(
            cp=self.cp, distributor=self.other_distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('999.00'), amount=Decimal('999.00'),
        )

        requisit = Requisition.objects.create(
            purchase_requisition_id=1, pr_ref_no="PR-FROM-CP-001", name=self.user,
            chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        PurchaseRequisition.objects.create(requisition=requisit, branch_company=self.branch)
        self.req_item_1 = RequisitionItem.objects.create(
            requisition_id=1, requisit=requisit, product_name="Item 1", quantity=5, quantity_pr=5
        )
        self.req_item_2 = RequisitionItem.objects.create(
            requisition_id=1, requisit=requisit, product_name="Item 2", quantity=2, quantity_pr=2
        )
        #รายการของร้านที่เลือก
        ComparisonPriceItem.objects.create(
            cp=self.cp.id, bidder=self.cpd, item=self.req_item_1, quantity=Decimal('5.0000'), unit=self.unit,
            unit_price=Decimal('20.0000'), discount='0', price=Decimal('100.00'), description='สีแดง',
        )
        ComparisonPriceItem.objects.create(
            cp=self.cp.id, bidder=self.cpd, item=self.req_item_2, quantity=Decimal('2.0000'), unit=self.unit,
            unit_price=Decimal('25.0000'), price=Decimal('50.00'),
        )
        #รายการของร้านที่ไม่ได้เลือก ต้องไม่ถูกดึงมา
        ComparisonPriceItem.objects.create(
            cp=self.cp.id, bidder=other_cpd, item=self.req_item_1, quantity=Decimal('5.0000'), unit=self.unit,
            unit_price=Decimal('99.0000'), price=Decimal('495.00'),
        )

    def _create_url(self):
        return reverse('createPOFromComparisonPrice', kwargs={'cp_id': self.cp.id})

    def _edit_url(self, po):
        return reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})

    def test_create_po_goes_straight_to_edit_page(self):
        response = self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        self.assertRedirects(response, self._edit_url(po), fetch_redirect_response=False)

    def test_create_po_copies_header_from_cp(self):
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        self.assertEqual(po.distributor, self.distributor)
        self.assertEqual(po.credit, self.credit)
        self.assertEqual(po.vat_type, self.vat_type)
        self.assertEqual(po.stockman_user, self.user)
        self.assertEqual(po.approver_user, self.approver)
        self.assertEqual(po.address_company, self.address)
        self.assertEqual(po.branch_company, self.branch)
        self.assertEqual(po.created, datetime.date(2026, 6, 20))
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.po_ref_no, po.ref_no)

    def test_special_cp_uses_special_approver(self):
        ComparisonPrice.objects.filter(id=self.cp.id).update(is_special_approve_cm=True, special_approver_status_id=2)
        self.client.post(self._create_url())
        self.assertEqual(PurchaseOrder.objects.get(cp=self.cp).approver_user, self.special_approver)

    def test_create_po_copies_price_and_items_of_selected_bidder(self):
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        self.assertEqual(po.total_price, Decimal('150.00'))
        self.assertEqual(po.discount, '10.00')
        self.assertEqual(po.total_after_discount, Decimal('140.00'))
        self.assertEqual(po.freight, Decimal('5.00'))
        self.assertEqual(po.vat, Decimal('10.15'))
        self.assertEqual(po.amount, Decimal('155.15'))

        items = list(PurchaseOrderItem.objects.filter(po=po).order_by('id'))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].item, self.req_item_1)
        self.assertEqual(items[0].quantity, Decimal('5.0000'))
        self.assertEqual(items[0].unit, self.unit)
        self.assertEqual(items[0].unit_price, Decimal('20.0000'))
        self.assertEqual(items[0].price, Decimal('100.00'))
        self.assertEqual(items[0].description, 'สีแดง')
        self.assertEqual(items[1].item, self.req_item_2)
        self.assertEqual(items[1].price, Decimal('50.00'))

    def test_create_po_is_pending_draft(self):
        #อนุมัติอัตโนมัติตอนกดบันทึกและส่งอนุมัติในหน้า editPOItem เท่านั้น
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        self.assertTrue(po.is_draft)
        self.assertEqual(po.approver_status_id, 1)

    def test_edit_page_shows_copied_items_locked(self):
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        response = self.client.get(self._edit_url(po))
        self.assertEqual(response.status_code, 200)
        forms = response.context['formset'].forms
        self.assertEqual(len(forms), 2)
        for item_form in forms:
            self.assertEqual(item_form.fields['price'].widget.attrs.get('readonly'), 'readonly')
        self.assertEqual(response.context['price_form'].fields['amount'].widget.attrs.get('readonly'), 'readonly')

    def test_vat_type_is_locked_on_edit_page(self):
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        response = self.client.get(self._edit_url(po))
        self.assertTrue(response.context['form'].fields['vat_type'].disabled)
        self.assertContains(response, 'name="vat_type"')
        self.assertRegex(response.content.decode(), r'<select[^>]*name="vat_type"[^>]*disabled')

    def test_vat_type_posted_change_is_ignored(self):
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        other_vat = BaseVatType.objects.create(id="2", name="No Vat")
        form = self.client.get(self._edit_url(po)).context['form']
        data = {k: ('' if v is None else v) for k, v in form.initial.items() if k in form.fields}
        data.update({
            'vat_type': other_vat.id, 'save_draft': '1',
            'purchaseorderitem_set-TOTAL_FORMS': '0', 'purchaseorderitem_set-INITIAL_FORMS': '0',
        })
        data.pop('quotation_pdf', None)
        self.client.post(self._edit_url(po), data)
        po.refresh_from_db()
        self.assertEqual(po.vat_type, self.vat_type)

    def test_get_does_not_create_po(self):
        response = self.client.get(self._create_url())
        self.assertRedirects(response, reverse('viewComparePricePO'), fetch_redirect_response=False)
        self.assertFalse(PurchaseOrder.objects.filter(cp=self.cp).exists())

    def test_create_twice_goes_to_existing_po(self):
        self.client.post(self._create_url())
        po = PurchaseOrder.objects.get(cp=self.cp)
        response = self.client.post(self._create_url())
        self.assertRedirects(response, self._edit_url(po), fetch_redirect_response=False)
        self.assertEqual(PurchaseOrder.objects.filter(cp=self.cp).count(), 1)
        self.assertEqual(PurchaseOrderItem.objects.filter(po=po).count(), 2)

    def test_cp_without_selected_bidder_price_does_not_create_po(self):
        ComparisonPrice.objects.filter(id=self.cp.id).update(select_bidder=None)
        response = self.client.post(self._create_url())
        self.assertRedirects(response, reverse('viewComparePricePO'), fetch_redirect_response=False)
        self.assertFalse(PurchaseOrder.objects.filter(cp=self.cp).exists())

    def test_other_user_cannot_create_po(self):
        other = User.objects.create_user(username='po_from_cp_other', password='password')
        UserProfile.objects.create(user=other).branch_company.add(self.branch)
        self.client.force_login(other)
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()
        response = self.client.post(self._create_url())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PurchaseOrder.objects.filter(cp=self.cp).exists())

    def test_unapproved_cp_cannot_create_po(self):
        ComparisonPrice.objects.filter(id=self.cp.id).update(approver_status_id=1)
        response = self.client.post(self._create_url())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PurchaseOrder.objects.filter(cp=self.cp).exists())

    def test_special_cp_waiting_special_approver_cannot_create_po(self):
        ComparisonPrice.objects.filter(id=self.cp.id).update(is_special_approve_cm=True, special_approver_status_id=1)
        response = self.client.post(self._create_url())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PurchaseOrder.objects.filter(cp=self.cp).exists())

    def test_old_step_two_url_fills_items_of_po_without_items(self):
        #ใบที่สร้างจากขั้นที่ 1 เดิมแต่ยังไม่ได้ใส่รายการ: เข้า URL เดิมแล้วดึงรายการให้ และไปหน้า editPOItem
        po = PurchaseOrder.objects.create(
            cp=self.cp, distributor=self.distributor, stockman_user=self.user, branch_company=self.branch,
            address_company=self.address, vat_type=self.vat_type, approver_status_id=1,
        )
        response = self.client.get(reverse('createPOItemFromComparisonPrice', kwargs={'po_id': po.id}))
        self.assertRedirects(response, self._edit_url(po), fetch_redirect_response=False)
        self.assertEqual(PurchaseOrderItem.objects.filter(po=po).count(), 2)
        po.refresh_from_db()
        self.assertEqual(po.amount, Decimal('155.15'))
