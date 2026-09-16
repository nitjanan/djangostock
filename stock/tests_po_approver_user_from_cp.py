import datetime

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BasePOType,
    BasePermission,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Distributor,
    Position,
    PositionBasePermission,
    PurchaseOrder,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CreatePOFromComparisonPriceApproverUserTestCase(TestCase):
    """ผู้อนุมัติของใบสั่งซื้อที่ออกจาก CP ต้องถูกดึงมาจากใบ CP เสมอ"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester_ap_from_cp', password='password')
        purchasing_group, _ = Group.objects.get_or_create(name='จัดซื้อ')
        self.user.groups.add(purchasing_group)
        self.client.login(username='tester_ap_from_cp', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_ap_from_cp",
            name="Test Distributor",
            credit=self.credit,
            vat_type=self.vat_type,
        )
        self.po_type = BasePOType.objects.create(id="po_type_ap_from_cp", name="Standard PO")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")
        BaseApproveStatus.objects.create(id=3, name="ไม่อนุมัติ")

        #ผู้อนุมัติใบสั่งซื้อปกติ มีสิทธิ CAAPO
        self.position = Position.objects.create(name='ผู้อนุมัติใบสั่งซื้อ')
        permission_caapo = BasePermission.objects.create(
            name='can approve approver PO',
            codename='CAAPO',
            codename_th='อนุมัติใบสั่งซื้อ',
        )
        position_permission = PositionBasePermission.objects.create(position=self.position)
        position_permission.base_permission.add(permission_caapo)
        position_permission.branch_company.add(self.branch)

        UserProfile.objects.create(user=self.user, position=self.position).branch_company.add(self.branch)

        self.cp_approver = User.objects.create_user(username='cp_approver', password='password')
        UserProfile.objects.create(user=self.cp_approver, position=self.position).branch_company.add(self.branch)

        #ผู้อนุมัติพิเศษของใบ CP ไม่ได้ถือสิทธิ CAAPO จึงไม่อยู่ใน dropdown ของใบสั่งซื้อ
        self.cp_special_approver = User.objects.create_user(username='cp_special_approver', password='password')
        UserProfile.objects.create(user=self.cp_special_approver).branch_company.add(self.branch)

        self.cp = ComparisonPrice.objects.create(
            organizer=self.user,
            select_bidder=self.distributor,
            address_company=self.address,
            branch_company=self.branch,
            approver_user=self.cp_approver,
            special_approver_user=self.cp_special_approver,
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

    def _set_cp(self, **kwargs):
        ComparisonPrice.objects.filter(id=self.cp.id).update(**kwargs)
        self.cp.refresh_from_db()

    def _post_create_po(self):
        url = reverse('createPOFromComparisonPrice', kwargs={'cp_id': self.cp.id})
        #ช่องผู้อนุมัติถูกซ่อน (readonly) จึงไม่มีค่าส่งมาจากฟอร์ม
        post_data = {
            'cp': self.cp.id,
            'shipping': 'EMS',
            'address_company': self.address.id,
            'due_receive_update': '2026-07-20',
            'po_type': self.po_type.id,
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

    def test_special_cp_uses_special_approver_user(self):
        self._set_cp(is_special_approve_cm=True)
        po = self._post_create_po()
        self.assertEqual(po.approver_user, self.cp_special_approver)

    def test_normal_cp_uses_approver_user(self):
        self._set_cp(is_special_approve_cm=False)
        po = self._post_create_po()
        self.assertEqual(po.approver_user, self.cp_approver)

    def test_special_approver_user_is_shown_on_the_form(self):
        self._set_cp(is_special_approve_cm=True)
        url = reverse('createPOFromComparisonPrice', kwargs={'cp_id': self.cp.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn(self.cp_special_approver, form.fields['approver_user'].queryset)
        self.assertEqual(form.initial['approver_user'], self.cp_special_approver)
