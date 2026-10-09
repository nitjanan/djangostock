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
    BasePOType,
    BaseVatType,
    BranchCompanyBaseAdress,
    Distributor,
    PurchaseOrder,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ViewPOEditLinkTestCase(TestCase):
    """viewPO: ปุ่มแก้ไข ถ้า is_re_approve = True และรออนุมัติ ต้องลิงก์ไป /False/True"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester_edit_link', password='password')
        self.client.login(username='tester_edit_link', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_edit_link", name="Test Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(id="po_type_edit_link", name="Standard PO")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")

        profile = UserProfile.objects.create(user=self.user)
        profile.branch_company.add(self.branch)

    def _create_po(self, is_re_approve, approver_status_id=1):
        return PurchaseOrder.objects.create(
            vat_type=self.vat_type,
            ref_no="PO-EDIT-LINK",
            distributor=self.distributor,
            credit=self.credit,
            stockman_user=self.user,
            approver_user=self.user,
            branch_company=self.branch,
            address_company=self.address,
            po_type=self.po_type,
            approver_status_id=approver_status_id,
            is_re_approve=is_re_approve,
            total_price=Decimal('100.00'),
            amount=Decimal('107.00'),
            due_receive_update=datetime.date(2026, 7, 20),
        )

    def _edit_url(self, po, is_re_approve):
        return reverse('editPOItem', kwargs={
            'po_id': po.id, 'isFromPR': 'False', 'isReApprove': str(is_re_approve),
        })

    def _get_html(self):
        response = self.client.get(reverse('viewPO'))
        self.assertEqual(response.status_code, 200)
        return response.content.decode('utf-8')

    def test_re_approve_waiting_links_to_re_approve(self):
        po = self._create_po(is_re_approve=True)
        html = self._get_html()
        self.assertIn(f'href="{self._edit_url(po, True)}"', html)
        self.assertNotIn(f'href="{self._edit_url(po, False)}"', html)

    def test_normal_waiting_links_to_normal_edit(self):
        po = self._create_po(is_re_approve=False)
        html = self._get_html()
        self.assertIn(f'href="{self._edit_url(po, False)}"', html)
        self.assertNotIn(f'href="{self._edit_url(po, True)}"', html)

    def test_superuser_re_approve_waiting_links_to_re_approve(self):
        self.user.is_superuser = True
        self.user.save()
        # ไม่ใช่ผู้สร้างใบ เพื่อให้เข้าเงื่อนไข superuser
        other = User.objects.create_user(username='other_stockman', password='password')
        po = self._create_po(is_re_approve=True)
        po.stockman_user = other
        po.save()
        html = self._get_html()
        self.assertIn(f'href="{self._edit_url(po, True)}"', html)

    def test_superuser_re_approve_approved_links_to_normal_edit(self):
        self.user.is_superuser = True
        self.user.save()
        other = User.objects.create_user(username='other_stockman', password='password')
        po = self._create_po(is_re_approve=True, approver_status_id=2)
        po.stockman_user = other
        po.save()
        html = self._get_html()
        self.assertIn(f'href="{self._edit_url(po, False)}"', html)
        self.assertNotIn(f'href="{self._edit_url(po, True)}"', html)
