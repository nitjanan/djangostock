from decimal import Decimal

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse

from stock.models import (
    BaseBranchCompany,
    BasePermission,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Position,
    PositionBasePermission,
    UserProfile,
)
from stock.tests_cp_po_edit_authz import EditAuthzBase
from stock.views import cp_special_approver_users


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ComparisonPricePrintApprover2TestCase(EditAuthzBase):
    """หน้าเลือกร้านค้า (printComparePricePO): ช่องผู้อนุมัติ 2 (CASCP) และรายชื่อผู้มีสิทธิอนุมัติ"""

    def setUp(self):
        super().setUp()
        self.cascp = BasePermission.objects.create(
            codename='CASCP', name='special', ap_amount_min=Decimal('500001'), ap_amount_max=Decimal('99999999'),
        )
        self.cp = ComparisonPrice.objects.create(
            organizer=self.owner, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1, is_draft=False,
        )
        ComparisonPriceDistributor.objects.create(
            cp=self.cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('600000.00'), amount=Decimal('642000.00'),
        )

        #ตำแหน่งที่มีสิทธิ CASCP ของบริษัท HO
        self.position = Position.objects.create(name='ผู้อนุมัติ 2')
        pbp = PositionBasePermission.objects.create(position=self.position)
        pbp.base_permission.add(self.cascp)
        pbp.branch_company.add(self.branch)

    def _profile_user(self, username, first_name, position=None, branch=None):
        user = User.objects.create_user(username=username, password='password', first_name=first_name)
        profile = UserProfile.objects.create(user=user, position=position)
        profile.branch_company.add(branch or self.branch)
        return user

    def _print(self):
        return self._client(self.owner).get(reverse('printComparePricePO', args=(self.cp.id,)))

    def test_special_approver_users_follow_cascp_position_and_company(self):
        allowed = self._profile_user('appr2_ok', 'สมชาย', self.position)
        other_branch = BaseBranchCompany.objects.create(id="2", code="BR", name="Branch")
        self._profile_user('appr2_other_branch', 'สมหญิง', self.position, other_branch)
        self._profile_user('appr2_no_position', 'สมศักดิ์')
        self.assertEqual(list(cp_special_approver_users(self.cp)), [allowed])

    def test_print_page_has_approver2_box_and_cascp_range(self):
        self._profile_user('appr2_ok', 'สมชาย', self.position)
        response = self._print()
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('id="cp-sign-approver2"', html)
        self.assertIn('สมชาย', html)
        self.assertEqual(response.context['cascp_info'], {'min': '500001.00', 'max': '99999999.00'})
        self.assertIn('id="cascp-info"', html)
        self.assertIn('ยอดเกิน 500,001', html)

    def test_print_page_warns_when_no_special_approver(self):
        html = self._print().content.decode('utf-8')
        self.assertIn('ยังไม่มีผู้มีสิทธิอนุมัติ 2', html)

    # ---------- ปุ่มปริ้นหน้าเลือกร้านค้า โหลดหน้า showComparePricePO ใน iframe ----------
    def test_show_cp_can_be_framed_by_same_site_only(self):
        response = self._client(self.owner).get(reverse('showComparePricePO', kwargs={'cp_id': self.cp.id, 'mode': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')

    def test_print_button_uses_show_page(self):
        html = self._print().content.decode('utf-8')
        self.assertIn('printCPFromShowPage()', html)
        self.assertIn(reverse('showComparePricePO', kwargs={'cp_id': self.cp.id, 'mode': 1}), html)

    # ---------- หน้าอนุมัติ (printCPApprove) หลังปรับ layout ----------
    def _pending_cp_for_examiner(self):
        examiner = User.objects.create_user(username='appr_page_exam', password='password')
        UserProfile.objects.create(user=examiner).branch_company.add(self.branch)
        self.cp.select_bidder = self.distributor
        self.cp.examiner_user = examiner
        self.cp.approver_user = self.owner
        self.cp.save()
        ComparisonPriceDistributor.objects.filter(cp=self.cp).update(is_select=True)
        return examiner

    def test_approve_page_shows_buttons_in_highlighted_box_for_examiner(self):
        examiner = self._pending_cp_for_examiner()
        response = self._client(examiner).get(reverse('printCPApprove', args=(self.cp.id, 'False')))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['isExaminer'])
        html = response.content.decode('utf-8')
        self.assertIn('class="cp-sign cp-sign-action"', html)
        self.assertIn("name = 'status' value = 'อนุมัติ'", html)
        self.assertIn("name = 'status' value = 'ไม่อนุมัติ'", html)
        self.assertIn('class="cp-doc-head"', html)
        self.assertIn('cp-compare-table', html)

    def test_approve_page_hides_buttons_for_other_users(self):
        self._pending_cp_for_examiner()
        html = self._client(self.owner).get(reverse('printCPApprove', args=(self.cp.id, 'False'))).content.decode('utf-8')
        self.assertNotIn("name = 'status' value = 'อนุมัติ'", html)
        self.assertNotIn('class="cp-sign cp-sign-action"', html)
