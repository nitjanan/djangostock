import datetime
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BasePOType,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    BaseDelivery,
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
    Position,
    BasePermission,
    PositionBasePermission,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class EditPOItemLockFromComparisonPriceTestCase(TestCase):
    """editPOItem: ใบสั่งซื้อที่สร้างจากใบเปรียบเทียบราคา ห้ามแก้รายการสินค้าและราคา"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester_lock', password='password')
        approver_group, _ = Group.objects.get_or_create(name='ผู้อนุมัติ')
        self.user.groups.add(approver_group)
        self.client.login(username='tester_lock', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_lock", name="Test Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(id="po_type_lock", name="Standard PO")
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        self.delivery = BaseDelivery.objects.create(name="คลังสินค้า")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")

        # สิทธิอนุมัติใบสั่งซื้อยึดจาก PositionBasePermission codename CAAPO
        self.position = Position.objects.create(name='ผู้อนุมัติใบสั่งซื้อ')
        self.permission_caapo = BasePermission.objects.create(
            name='can approve approver PO',
            codename='CAAPO',
            codename_th='อนุมัติใบสั่งซื้อ',
        )
        position_permission = PositionBasePermission.objects.create(position=self.position)
        position_permission.base_permission.add(self.permission_caapo)
        position_permission.branch_company.add(self.branch)

        self.profile = UserProfile.objects.create(user=self.user, position=self.position)
        self.profile.branch_company.add(self.branch)

        self.cp = ComparisonPrice.objects.create(
            organizer=self.user,
            select_bidder=self.distributor,
            address_company=self.address,
            branch_company=self.branch,
            approver_user=self.user,
            approver_status_id=2,
        )
        ComparisonPriceDistributor.objects.create(
            cp=self.cp,
            distributor=self.distributor,
            credit=self.credit,
            vat_type=self.vat_type,
            total_price=100.00,
            amount=107.00,
        )

        self.requisit = Requisition.objects.create(
            purchase_requisition_id=1,
            pr_ref_no="PR-LOCK-001",
            name=self.user,
            chief_approve_user_name=self.user,
            supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        PurchaseRequisition.objects.create(requisition=self.requisit, branch_company=self.branch)
        self.req_item = RequisitionItem.objects.create(
            requisition_id=1, requisit=self.requisit, product_name="Test Item 1", quantity=5, quantity_pr=5
        )

    def _create_po(self, cp):
        po = PurchaseOrder.objects.create(
            cp=cp,
            vat_type=self.vat_type,
            ref_no="PO-LOCK-001" if cp else "PO-LOCK-002",
            distributor=self.distributor,
            credit=self.credit,
            stockman_user=self.user,
            approver_user=self.user,
            branch_company=self.branch,
            address_company=self.address,
            po_type=self.po_type,
            approver_status_id=2 if cp else 1,
            total_price=Decimal('100.00'),
            discount=Decimal('0.00'),
            total_after_discount=Decimal('100.00'),
            freight=Decimal('0.00'),
            vat=Decimal('7.00'),
            amount=Decimal('107.00'),
            due_receive_update=datetime.date(2026, 7, 20),
        )
        item = PurchaseOrderItem.objects.create(
            po=po,
            item=self.req_item,
            quantity=Decimal('5.0000'),
            unit=self.unit,
            unit_price=Decimal('20.0000'),
            price=Decimal('100.00'),
        )
        return po, item

    def _post_edit(self, po, item):
        """โพสต์ค่าที่แก้ทั้งรายการสินค้าและราคา"""
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})
        post_data = {
            'purchaseorderitem_set-TOTAL_FORMS': '1',
            'purchaseorderitem_set-INITIAL_FORMS': '1',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0',
            'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            'purchaseorderitem_set-0-id': item.id,
            'purchaseorderitem_set-0-po': po.id,
            'purchaseorderitem_set-0-item': self.req_item.id,
            'purchaseorderitem_set-0-quantity': '2.0000',
            'purchaseorderitem_set-0-unit': self.unit.id,
            'purchaseorderitem_set-0-unit_price': '50.0000',
            'purchaseorderitem_set-0-discount': '',
            'purchaseorderitem_set-0-price': '999.00',
            'purchaseorderitem_set-0-description': 'changed',
            # PurchaseOrderPriceForm
            'total_price': '999.00',
            'discount': '10.00',
            'total_after_discount': '989.00',
            'freight': '50.00',
            'vat': '69.23',
            'amount': '1058.23',
            'note': 'note changed',
            'delivery': self.delivery.id,
            # PurchaseOrderForm
            'distributor': self.distributor.id,
            'credit': self.credit.id,
            'shipping': 'EMS',
            'vat_type': self.vat_type.id,
            'address_company': self.address.id,
            'approver_user': self.user.id,
            'due_receive_update': '2026-08-25',
            'po_type': self.po_type.id,
            # RateDistributorForm
            'price_rate': 5,
            'quantity_rate': 5,
            'service_rate': 5,
            'safety_rate': 5,
            'counsel': 'ok',
        }
        response = self.client.post(url, data=post_data)
        if response.status_code != 302 and response.context:
            for key in ('formset', 'price_form', 'form', 'form_rate'):
                ctx = response.context.get(key)
                if ctx is not None:
                    print(key, str(ctx.errors).encode('ascii', 'backslashreplace').decode('ascii'))
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        item.refresh_from_db()
        return po, item

    # ---------- PO จากใบเปรียบเทียบราคา: ต้องล็อก ----------

    def test_po_from_cp_keeps_item_values(self):
        po, item = self._create_po(self.cp)
        po, item = self._post_edit(po, item)
        self.assertEqual(item.quantity, Decimal('5.0000'))
        self.assertEqual(item.unit_price, Decimal('20.0000'))
        self.assertEqual(item.price, Decimal('100.00'))

    def test_po_from_cp_keeps_price_values(self):
        po, item = self._create_po(self.cp)
        po, item = self._post_edit(po, item)
        self.assertEqual(po.total_price, Decimal('100.00'))
        self.assertEqual(po.discount, '0.00')
        self.assertEqual(po.total_after_discount, Decimal('100.00'))
        self.assertEqual(po.freight, Decimal('0.00'))
        self.assertEqual(po.vat, Decimal('7.00'))
        self.assertEqual(po.amount, Decimal('107.00'))

    def test_po_from_cp_cannot_delete_item(self):
        po, item = self._create_po(self.cp)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})
        post_data = {
            'purchaseorderitem_set-TOTAL_FORMS': '1',
            'purchaseorderitem_set-INITIAL_FORMS': '1',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0',
            'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            'purchaseorderitem_set-0-id': item.id,
            'purchaseorderitem_set-0-po': po.id,
            'purchaseorderitem_set-0-item': self.req_item.id,
            'purchaseorderitem_set-0-quantity': '5.0000',
            'purchaseorderitem_set-0-unit': self.unit.id,
            'purchaseorderitem_set-0-unit_price': '20.0000',
            'purchaseorderitem_set-0-price': '100.00',
            'purchaseorderitem_set-0-DELETE': 'on',
            'total_price': '100.00',
            'discount': '0.00',
            'total_after_discount': '100.00',
            'freight': '0.00',
            'vat': '7.00',
            'amount': '107.00',
            'note': '',
            'delivery': '',
            'distributor': self.distributor.id,
            'credit': self.credit.id,
            'shipping': 'EMS',
            'vat_type': self.vat_type.id,
            'address_company': self.address.id,
            'approver_user': self.user.id,
            'due_receive_update': '2026-08-25',
            'po_type': self.po_type.id,
            'price_rate': 5,
            'quantity_rate': 5,
            'service_rate': 5,
            'safety_rate': 5,
            'counsel': 'ok',
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PurchaseOrderItem.objects.filter(id=item.id).exists())

    def test_po_from_cp_still_saves_header_fields(self):
        """ล็อกเฉพาะรายการสินค้าและราคา ข้อมูลส่วนหัวยังแก้ได้"""
        po, item = self._create_po(self.cp)
        po, item = self._post_edit(po, item)
        self.assertEqual(po.shipping, 'EMS')
        self.assertEqual(po.due_receive_update, datetime.date(2026, 8, 25))
        self.assertEqual(po.note, 'note changed')
        self.assertEqual(po.delivery, self.delivery)

    def test_lock_flag_true_in_context_for_po_from_cp(self):
        po, item = self._create_po(self.cp)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['isLockPOItem'])

    # ---------- PO ที่ไม่ได้มาจากใบเปรียบเทียบราคา: เหมือนเดิม ----------

    def test_po_without_cp_still_editable(self):
        po, item = self._create_po(None)
        po, item = self._post_edit(po, item)
        self.assertEqual(item.quantity, Decimal('2.0000'))
        self.assertEqual(item.unit_price, Decimal('50.0000'))
        self.assertEqual(item.price, Decimal('999.00'))
        self.assertEqual(po.total_price, Decimal('999.00'))
        self.assertEqual(po.freight, Decimal('50.00'))
        self.assertEqual(po.amount, Decimal('1058.23'))

    def test_lock_flag_false_in_context_for_po_without_cp(self):
        po, item = self._create_po(None)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['isLockPOItem'])

    def test_price_and_item_widgets_render_readonly_for_po_from_cp(self):
        po, item = self._create_po(self.cp)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})
        response = self.client.get(url)
        price_form = response.context['price_form']
        for field in ('total_price', 'discount', 'total_after_discount', 'freight', 'vat', 'amount'):
            self.assertEqual(price_form.fields[field].widget.attrs.get('readonly'), 'readonly')
        for item_form in response.context['formset'].forms:
            for name in ('quantity', 'unit', 'unit_price', 'price', 'description'):
                self.assertEqual(item_form.fields[name].widget.attrs.get('readonly'), 'readonly', name)

    def test_widgets_not_readonly_for_po_without_cp(self):
        po, item = self._create_po(None)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'False'})
        response = self.client.get(url)
        price_form = response.context['price_form']
        self.assertIsNone(price_form.fields['total_price'].widget.attrs.get('readonly'))
        for item_form in response.context['formset'].forms:
            self.assertIsNone(item_form.fields['quantity'].widget.attrs.get('readonly'))

    def test_create_po_item_from_cp_page_renders_readonly(self):
        """หน้าใส่รายการสินค้าจากใบเปรียบเทียบราคา ต้อง readonly ทุกช่องของรายการและราคา"""
        po, item = self._create_po(self.cp)
        url = reverse('createPOItemFromComparisonPrice', kwargs={'po_id': po.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        price_form = response.context['price_form']
        for field in ('total_price', 'discount', 'total_after_discount', 'freight', 'vat', 'amount'):
            self.assertEqual(price_form.fields[field].widget.attrs.get('readonly'), 'readonly', field)
        #หมายเหตุ และสถานที่จัดส่ง ยังแก้ได้
        self.assertIsNone(price_form.fields['note'].widget.attrs.get('readonly'))
        self.assertIsNone(price_form.fields['delivery'].widget.attrs.get('readonly'))

        for item_form in response.context['formset'].forms:
            for name in ('item', 'quantity', 'unit', 'unit_price', 'discount', 'price', 'description'):
                self.assertEqual(item_form.fields[name].widget.attrs.get('readonly'), 'readonly', name)

    def test_express_input_is_readonly_on_create_po_item_from_cp(self):
        po, item = self._create_po(self.cp)
        url = reverse('createPOItemFromComparisonPrice', kwargs={'po_id': po.id})
        html = self.client.get(url).content.decode('utf-8')
        self.assertIn('id="id_form-0-express"', html)
        express_tag = html[html.index('id="id_form-0-express"'):]
        express_tag = express_tag[:express_tag.index('>')]
        self.assertIn('readonly', express_tag)
        self.assertIn('lock-po-item', express_tag)

    def test_express_input_readonly_only_when_locked_on_edit_po_item(self):
        po_cp, item_cp = self._create_po(self.cp)
        html_locked = self.client.get(reverse(
            'editPOItem', kwargs={'po_id': po_cp.id, 'isFromPR': 'False', 'isReApprove': 'False'}
        )).content.decode('utf-8')
        tag_locked = html_locked[html_locked.index('id="id_purchaseorderitem_set-0-express"'):]
        tag_locked = tag_locked[:tag_locked.index('>')]
        self.assertIn('readonly', tag_locked)

        po_pr, item_pr = self._create_po(None)
        html_open = self.client.get(reverse(
            'editPOItem', kwargs={'po_id': po_pr.id, 'isFromPR': 'False', 'isReApprove': 'False'}
        )).content.decode('utf-8')
        tag_open = html_open[html_open.index('id="id_purchaseorderitem_set-0-express"'):]
        tag_open = tag_open[:tag_open.index('>')]
        self.assertNotIn('readonly', tag_open)

    # ---------- ขอเปลี่ยนแปลงรายละเอียดรายการ (re approve): ไม่ล็อก ----------

    def test_re_approve_does_not_lock(self):
        po, item = self._create_po(self.cp)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'True'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['isLockPOItem'])
        self.assertIsNone(response.context['price_form'].fields['total_price'].widget.attrs.get('readonly'))
        for item_form in response.context['formset'].forms:
            self.assertIsNone(item_form.fields['quantity'].widget.attrs.get('readonly'))

    def test_re_approve_saves_item_and_price_changes(self):
        po, item = self._create_po(self.cp)
        url = reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'False', 'isReApprove': 'True'})
        post_data = {
            'purchaseorderitem_set-TOTAL_FORMS': '1',
            'purchaseorderitem_set-INITIAL_FORMS': '1',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0',
            'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            'purchaseorderitem_set-0-id': item.id,
            'purchaseorderitem_set-0-po': po.id,
            'purchaseorderitem_set-0-item': self.req_item.id,
            'purchaseorderitem_set-0-quantity': '2.0000',
            'purchaseorderitem_set-0-unit': self.unit.id,
            'purchaseorderitem_set-0-unit_price': '50.0000',
            'purchaseorderitem_set-0-price': '999.00',
            'total_price': '999.00',
            'discount': '0.00',
            'total_after_discount': '999.00',
            'freight': '50.00',
            'vat': '0.00',
            'amount': '1049.00',
            'note': '',
            'delivery': self.delivery.id,
            'distributor': self.distributor.id,
            'credit': self.credit.id,
            'shipping': 'EMS',
            'vat_type': self.vat_type.id,
            'address_company': self.address.id,
            'approver_user': self.user.id,
            'due_receive_update': '2026-08-25',
            'po_type': self.po_type.id,
            'price_rate': 5,
            'quantity_rate': 5,
            'service_rate': 5,
            'safety_rate': 5,
            'counsel': 'ok',
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        po.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(item.quantity, Decimal('2.0000'))
        self.assertEqual(item.price, Decimal('999.00'))
        self.assertEqual(po.total_price, Decimal('999.00'))
        self.assertEqual(po.amount, Decimal('1049.00'))
        #re approve ต้องกลับไปรออนุมัติใหม่
        self.assertEqual(po.approver_status_id, 1)
        self.assertTrue(po.is_re_approve)
