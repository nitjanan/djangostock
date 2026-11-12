from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PRRejectTabReApproveTestCase(TestCase):
    """หน้ารายการใบขอซื้อ แท็ปไม่อนุมัติ (/purchaseRequisition/?tab=reject): ปุ่มขอเปลี่ยนแปลงรายละเอียด"""

    def setUp(self):
        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")
        BaseApproveStatus.objects.create(id=3, name="ไม่อนุมัติ")

        #ขอเปลี่ยนแปลงได้เฉพาะกลุ่มพัสดุ ที่อยู่บริษัทของใบขอซื้อ
        self.user = User.objects.create_user(username='pr_reject_supplies', password='password')
        self.user.groups.add(Group.objects.create(name='พัสดุ'))
        UserProfile.objects.create(user=self.user).branch_company.add(self.branch)
        self.other = User.objects.create_user(username='pr_reject_other', password='password')
        UserProfile.objects.create(user=self.other).branch_company.add(self.branch)

        self.requisit = Requisition.objects.create(
            pr_ref_no="PR-REJ-001", name=self.user,
            chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        self.item = RequisitionItem.objects.create(
            requisition_id=self.requisit.id, requisit=self.requisit, product_name="Test Item",
            quantity=5, quantity_pr=5, is_used=True,
        )

    def _create_pr(self, approver_status_id=3, purchase_status_id=2):
        return PurchaseRequisition.objects.create(
            requisition=self.requisit, branch_company=self.branch, address_company=self.address,
            approver_status_id=approver_status_id, purchase_status_id=purchase_status_id,
            reject_reason='ราคาสูงไป',
        )

    def _login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

    def _reject_tab(self):
        response = self.client.get(reverse('viewPR') + '?tab=reject')
        self.assertEqual(response.status_code, 200)
        return response

    def test_reject_tab_shows_button_for_supplies(self):
        pr = self._create_pr()
        self._login(self.user)
        response = self._reject_tab()
        self.assertTrue(response.context['prs'][0].can_re_approve)
        self.assertContains(response, reverse('requestPRReApprove', args=(pr.id,)))

    def test_reject_tab_hides_button_for_non_supplies(self):
        pr = self._create_pr()
        self._login(self.other)
        response = self._reject_tab()
        self.assertNotContains(response, reverse('requestPRReApprove', args=(pr.id,)))

    def test_reject_tab_hides_button_when_item_in_po(self):
        pr = self._create_pr()
        po = PurchaseOrder.objects.create(
            branch_company=self.branch, approver_status_id=1,
            vat_type=BaseVatType.objects.create(id="1", name="Vat 7%"),
        )
        PurchaseOrderItem.objects.create(po=po, item=self.item, quantity=1)
        self._login(self.user)
        response = self._reject_tab()
        self.assertNotContains(response, reverse('requestPRReApprove', args=(pr.id,)))

    def test_reject_tab_hides_button_when_item_in_cp(self):
        pr = self._create_pr()
        cp = ComparisonPrice.objects.create(
            ref_no='CM-REJ-001', organizer=self.user, branch_company=self.branch, address_company=self.address,
        )
        ComparisonPriceItem.objects.create(item=self.item, cp=cp.id, quantity=5)
        self._login(self.user)
        response = self._reject_tab()
        self.assertFalse(response.context['prs'][0].can_re_approve)
        self.assertNotContains(response, reverse('requestPRReApprove', args=(pr.id,)))

    def test_reject_tab_shows_button_when_cp_cancelled(self):
        #ใบเปรียบเทียบราคาที่ยกเลิกแล้วไม่นับ
        pr = self._create_pr()
        cp = ComparisonPrice.objects.create(
            ref_no='CM-REJ-002', organizer=self.user, branch_company=self.branch, address_company=self.address,
            is_cancel=True,
        )
        ComparisonPriceItem.objects.create(item=self.item, cp=cp.id, quantity=5)
        self._login(self.user)
        self.assertContains(self._reject_tab(), reverse('requestPRReApprove', args=(pr.id,)))

    def test_request_blocked_when_item_in_cp(self):
        pr = self._create_pr()
        cp = ComparisonPrice.objects.create(
            ref_no='CM-REJ-003', organizer=self.user, branch_company=self.branch, address_company=self.address,
        )
        ComparisonPriceItem.objects.create(item=self.item, cp=cp.id, quantity=5)
        self._login(self.user)
        response = self.client.post(reverse('requestPRReApprove', args=(pr.id,)))
        self.assertRedirects(response, reverse('showPR', args=(pr.id, 1)), fetch_redirect_response=False)
        pr.refresh_from_db()
        self.assertEqual(pr.approver_status_id, 3)

    def test_request_on_approver_rejected_pr_makes_draft(self):
        pr = self._create_pr(approver_status_id=3)
        self._login(self.user)
        response = self.client.post(reverse('requestPRReApprove', args=(pr.id,)))
        self.assertRedirects(response, reverse('reApprovePR', args=(pr.id,)), fetch_redirect_response=False)
        pr.refresh_from_db()
        self.assertEqual(pr.approver_status_id, 1)
        self.assertTrue(pr.is_draft)
        self.assertTrue(pr.is_re_approve)
        self.assertIsNone(pr.reject_reason)

    def test_request_on_purchase_user_rejected_pr_resets_purchase_status(self):
        #ผู้ขอซื้อไม่อนุมัติ (approver ยังรอดำเนินการ): ต้องออกจากแท็ปไม่อนุมัติด้วย
        pr = self._create_pr(approver_status_id=1, purchase_status_id=3)
        self._login(self.user)
        response = self.client.post(reverse('requestPRReApprove', args=(pr.id,)))
        self.assertRedirects(response, reverse('reApprovePR', args=(pr.id,)), fetch_redirect_response=False)
        pr.refresh_from_db()
        self.assertEqual(pr.purchase_status_id, 2)
        self.assertEqual(pr.approver_status_id, 1)
        self.assertTrue(pr.is_draft)
        self.assertNotContains(self._reject_tab(), reverse('requestPRReApprove', args=(pr.id,)))

    def test_request_blocked_by_non_supplies(self):
        pr = self._create_pr()
        self._login(self.other)
        response = self.client.post(reverse('requestPRReApprove', args=(pr.id,)))
        self.assertEqual(response.status_code, 403)
        pr.refresh_from_db()
        self.assertEqual(pr.approver_status_id, 3)
