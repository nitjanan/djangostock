import datetime
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from stock.views import auto_approve_po_from_cp
from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BasePOType,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Distributor,
    PurchaseOrder,
    UserProfile,
    Position,
    BasePermission,
    PositionBasePermission,
)


class CreatePOFromComparisonPriceAutoApproveTestCase(TestCase):
    """สร้าง PO จากใบเปรียบเทียบราคา: ตอนสร้างยังไม่มียอดเงิน จึงต้องเป็นรอดำเนินการเสมอ"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester_auto_ap', password='password')

        approver_group, _ = Group.objects.get_or_create(name='ผู้อนุมัติ')
        self.user.groups.add(approver_group)
        self.client.login(username='tester_auto_ap', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_auto_ap",
            name="Test Distributor",
            credit=self.credit,
            vat_type=self.vat_type,
        )
        self.po_type = BasePOType.objects.create(id="po_type_auto_ap", name="Standard PO")

        # สถานะการอนุมัติ 1 = รอดำเนินการ, 2 = อนุมัติ, 3 = ไม่อนุมัติ
        self.status_pending = BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        self.status_approved = BaseApproveStatus.objects.create(id=2, name="อนุมัติ")
        self.status_rejected = BaseApproveStatus.objects.create(id=3, name="ไม่อนุมัติ")

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
            special_approver_user=self.user,
        )
        ComparisonPrice.objects.filter(id=self.cp.id).update(
            created=datetime.date(2026, 6, 15),
            select_bidder_update=datetime.date(2026, 6, 20),
        )
        self.cp.refresh_from_db()

        ComparisonPriceDistributor.objects.create(
            cp=self.cp,
            distributor=self.distributor,
            credit=self.credit,
            vat_type=self.vat_type,
            total_price=100.00,
            amount=107.00,
        )

    def _post_create_po(self):
        url = reverse('createPOFromComparisonPrice', kwargs={'cp_id': self.cp.id})
        post_data = {
            'cp': self.cp.id,
            'shipping': 'EMS',
            'address_company': self.address.id,
            'approver_user': self.user.id,
            'due_receive_update': '2026-07-20',
            'po_type': self.po_type.id,
            # RateDistributorForm
            'distributor': self.distributor.id,
            'price_rate': 5,
            'quantity_rate': 5,
            'service_rate': 5,
            'safety_rate': 5,
            'counsel': 'Excellent service',
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        return PurchaseOrder.objects.get(cp=self.cp)

    def _set_cp(self, **kwargs):
        ComparisonPrice.objects.filter(id=self.cp.id).update(**kwargs)
        self.cp.refresh_from_db()

    # ---------- CP ปกติ (ไม่ใช่ยอดเกิน 200,000) ----------

    def test_normal_cp_approved_stays_pending_without_amount(self):
        #ตอนสร้างใบสั่งซื้อยังไม่ได้ใส่รายการ/ราคา amount จึงยังว่าง ต้องไม่อนุมัติอัตโนมัติ
        self._set_cp(is_special_approve_cm=False, approver_status_id=2, special_approver_status_id=None)
        po = self._post_create_po()
        self.assertIsNone(po.amount)
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_normal_cp_pending_keeps_po_pending(self):
        self._set_cp(is_special_approve_cm=False, approver_status_id=1, special_approver_status_id=None)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_normal_cp_rejected_keeps_po_pending(self):
        self._set_cp(is_special_approve_cm=False, approver_status_id=3, special_approver_status_id=None)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_normal_cp_without_status_keeps_po_pending(self):
        self._set_cp(is_special_approve_cm=False, approver_status_id=None, special_approver_status_id=None)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_normal_cp_ignores_special_approver_status(self):
        # ไม่ใช่ใบพิเศษ: ต้องดูเฉพาะ approver_status
        self._set_cp(is_special_approve_cm=False, approver_status_id=1, special_approver_status_id=2)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    # ---------- CP ยอดเกิน 200,000 (ต้องมีผู้อนุมัติพิเศษ) ----------

    def test_special_cp_special_approved_stays_pending_without_amount(self):
        self._set_cp(is_special_approve_cm=True, approver_status_id=2, special_approver_status_id=2)
        po = self._post_create_po()
        self.assertIsNone(po.amount)
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_special_cp_special_pending_keeps_po_pending(self):
        # ผู้อนุมัติปกติอนุมัติแล้ว แต่ผู้อนุมัติพิเศษยังไม่อนุมัติ
        self._set_cp(is_special_approve_cm=True, approver_status_id=2, special_approver_status_id=1)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_special_cp_special_rejected_keeps_po_pending(self):
        self._set_cp(is_special_approve_cm=True, approver_status_id=2, special_approver_status_id=3)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_special_cp_without_special_status_keeps_po_pending(self):
        self._set_cp(is_special_approve_cm=True, approver_status_id=2, special_approver_status_id=None)
        po = self._post_create_po()
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)


class AutoApprovePOFromCPHelperTestCase(TestCase):
    """auto_approve_po_from_cp: อนุมัติอัตโนมัติเมื่อ CP อนุมัติแล้ว และ amount > 0 เท่านั้น"""

    def _cp(self, is_special, approver_status_id, special_approver_status_id):
        cp = ComparisonPrice()
        cp.is_special_approve_cm = is_special
        cp.approver_status_id = approver_status_id
        cp.special_approver_status_id = special_approver_status_id
        return cp

    def _po(self, amount):
        po = PurchaseOrder()
        po.amount = amount
        po.approver_status_id = 1
        return po

    def test_approved_cp_with_positive_amount_is_approved(self):
        po = self._po(Decimal('107.00'))
        self.assertTrue(auto_approve_po_from_cp(po, self._cp(False, 2, None)))
        self.assertEqual(po.approver_status_id, 2)
        self.assertIsNotNone(po.approver_update)

    def test_approved_cp_with_zero_amount_is_not_approved(self):
        po = self._po(Decimal('0.00'))
        self.assertFalse(auto_approve_po_from_cp(po, self._cp(False, 2, None)))
        self.assertEqual(po.approver_status_id, 1)
        self.assertIsNone(po.approver_update)

    def test_approved_cp_with_null_amount_is_not_approved(self):
        po = self._po(None)
        self.assertFalse(auto_approve_po_from_cp(po, self._cp(False, 2, None)))
        self.assertEqual(po.approver_status_id, 1)

    def test_approved_cp_with_negative_amount_is_not_approved(self):
        po = self._po(Decimal('-10.00'))
        self.assertFalse(auto_approve_po_from_cp(po, self._cp(False, 2, None)))
        self.assertEqual(po.approver_status_id, 1)

    def test_pending_cp_with_positive_amount_is_not_approved(self):
        po = self._po(Decimal('107.00'))
        self.assertFalse(auto_approve_po_from_cp(po, self._cp(False, 1, None)))
        self.assertEqual(po.approver_status_id, 1)

    def test_special_cp_uses_special_status(self):
        po = self._po(Decimal('107.00'))
        self.assertTrue(auto_approve_po_from_cp(po, self._cp(True, 1, 2)))
        self.assertEqual(po.approver_status_id, 2)

    def test_special_cp_special_pending_is_not_approved(self):
        po = self._po(Decimal('107.00'))
        self.assertFalse(auto_approve_po_from_cp(po, self._cp(True, 2, 1)))
        self.assertEqual(po.approver_status_id, 1)

    def test_special_cp_special_approved_but_zero_amount_is_not_approved(self):
        po = self._po(Decimal('0.00'))
        self.assertFalse(auto_approve_po_from_cp(po, self._cp(True, 2, 2)))
        self.assertEqual(po.approver_status_id, 1)
