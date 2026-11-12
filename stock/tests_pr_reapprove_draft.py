from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BasePermission,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceItem,
    Position,
    PositionBasePermission,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ReApprovePRSaveDraftTestCase(TestCase):
    """ใบขอซื้อ: ปุ่ม ขอเปลี่ยนแปลงรายละเอียดรายการ (requestPRReApprove) ทำให้เป็นแบบร่างก่อน
    แล้วหน้า reApprovePR มีปุ่ม บันทึกแบบร่าง และ บันทึกและส่งอนุมัติ"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reapprove_pr_user', password='password')
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")

        #ผู้จัดทำ = กลุ่มจัดซื้อ, ผู้อนุมัติ = ตำแหน่งที่มีสิทธิ CAAPR ของบริษัทนี้
        position = Position.objects.create(name="ผู้อนุมัติ PR")
        perm = BasePermission.objects.create(name="อนุมัติ PR", codename="CAAPR", codename_th="อนุมัติ PR")
        pbp = PositionBasePermission.objects.create(position=position)
        pbp.base_permission.add(perm)
        pbp.branch_company.add(self.branch)
        profile = UserProfile.objects.create(user=self.user, position=position)
        profile.branch_company.add(self.branch)
        #ขอเปลี่ยนแปลงได้เฉพาะกลุ่มพัสดุ (เหมือนเงื่อนไขปุ่มในหน้า showPR)
        for name in ('พัสดุ',):
            self.user.groups.add(Group.objects.create(name=name))
        #ผู้จัดทำ (เจ้าหน้าที่จัดซื้อ) เป็นคนละคน: กลุ่มจัดซื้อไม่เห็นแท็ปแบบร่าง
        self.purchaser = User.objects.create_user(username='reapprove_pr_purchaser', password='password')
        self.purchaser.groups.add(Group.objects.create(name='จัดซื้อ'))
        UserProfile.objects.create(user=self.purchaser).branch_company.add(self.branch)

        self.requisit = Requisition.objects.create(
            pr_ref_no="PR-REAP-001", name=self.user,
            chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        #ใบที่อนุมัติแล้ว
        self.pr = PurchaseRequisition.objects.create(
            requisition=self.requisit, branch_company=self.branch, address_company=self.address,
            approver_status_id=2, approver_user=self.user, organizer=self.purchaser, note='C#ปิดรายการ',
        )
        self.item = RequisitionItem.objects.create(
            requisition_id=self.requisit.id, requisit=self.requisit, product_name="Test Item",
            quantity=5, quantity_pr=5, is_used=True,
        )
        self.request_url = reverse('requestPRReApprove', args=(self.pr.id,))
        self.url = reverse('reApprovePR', args=(self.pr.id,))

    def _post(self, save_draft):
        return self.client.post(self.url, {
            'organizer': self.purchaser.id,
            'approver_user': self.user.id,
            'note': 'แก้ไขรายการ',
            'branch_company': self.branch.id,
            'save_draft': save_draft,
        })

    def test_request_re_approve_makes_pr_draft_first(self):
        response = self.client.post(self.request_url)
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.pr.refresh_from_db()
        self.item.refresh_from_db()
        self.assertTrue(self.pr.is_draft)
        self.assertTrue(self.pr.is_re_approve)
        self.assertEqual(self.pr.approver_status_id, 1)
        self.assertEqual(self.pr.note, 'ปิดรายการ')
        self.assertFalse(self.item.is_used)

    def test_request_re_approve_requires_post_and_permission(self):
        self.assertEqual(self.client.get(self.request_url).status_code, 405)
        self.user.groups.remove(Group.objects.get(name='พัสดุ'))
        self.assertEqual(self.client.post(self.request_url).status_code, 403)
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.approver_status_id, 2)
        self.assertFalse(self.pr.is_draft)

    def test_opening_edit_page_does_not_change_approved_pr(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('showPR', args=(self.pr.id, 1)), fetch_redirect_response=False)
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.approver_status_id, 2)
        self.assertFalse(self.pr.is_re_approve)

    def test_page_shows_both_buttons(self):
        self.client.post(self.request_url)
        html = self.client.get(self.url).content.decode('utf-8')
        self.assertIn('บันทึกแบบร่าง', html)
        self.assertIn('บันทึกและส่งอนุมัติ', html)
        self.assertIn('name="save_draft"', html)

    def test_save_draft_keeps_pr_as_draft(self):
        self.client.post(self.request_url)
        response = self._post('1')
        self.pr.refresh_from_db()
        self.assertTrue(self.pr.is_draft)
        self.assertEqual(self.pr.approver_status_id, 1)
        self.assertRedirects(response, reverse('viewPR') + '?tab=draft&focus=' + str(self.pr.id),
                             fetch_redirect_response=False)
        #ยังเป็นแบบร่าง: หน้ารายการแท็ปแบบร่างมีปุ่มแก้ไขกลับไปหน้า reApprovePR
        html = self.client.get(reverse('viewPR') + '?tab=draft').content.decode('utf-8')
        self.assertIn(self.url, html)

    def test_save_and_send_clears_draft(self):
        self.client.post(self.request_url)
        response = self._post('')
        self.pr.refresh_from_db()
        self.assertFalse(self.pr.is_draft)
        self.assertEqual(self.pr.approver_status_id, 1)
        self.assertEqual(self.pr.note, 'แก้ไขรายการ')
        self.assertRedirects(response, reverse('viewPR') + '?tab=process&focus=' + str(self.pr.id),
                             fetch_redirect_response=False)

    def test_request_again_after_send_does_not_pull_back_to_draft(self):
        self.client.post(self.request_url)
        self._post('')
        self.client.post(self.request_url)
        self.pr.refresh_from_db()
        self.assertFalse(self.pr.is_draft)

    #---- สินค้าถูกดึงไปออกใบเปรียบเทียบราคา / ใบสั่งซื้อแล้ว: ห้ามขอเปลี่ยนแปลงรายละเอียด ----
    def _create_po(self, is_cancel=False):
        po = PurchaseOrder.objects.create(
            ref_no='PO-REAP-001', branch_company=self.branch, address_company=self.address, is_cancel=is_cancel,
            vat_type=BaseVatType.objects.get_or_create(id='1', defaults={'name': 'Vat 7%'})[0],
        )
        PurchaseOrderItem.objects.create(po=po, item=self.item, quantity=5)
        return po

    def _create_cp(self):
        cp = ComparisonPrice.objects.create(
            ref_no='CM-REAP-001', organizer=self.user, branch_company=self.branch, address_company=self.address,
        )
        ComparisonPriceItem.objects.create(item=self.item, cp=cp.id, quantity=5)
        return cp

    def _show_html(self):
        return self.client.get(reverse('showPR', args=(self.pr.id, 1))).content.decode('utf-8')

    def test_button_shown_when_items_not_used(self):
        self.assertIn(self.request_url, self._show_html())

    def test_item_in_po_hides_button_and_blocks_request(self):
        self._create_po()
        self.assertNotIn(self.request_url, self._show_html())
        response = self.client.post(self.request_url)
        self.assertRedirects(response, reverse('showPR', args=(self.pr.id, 1)), fetch_redirect_response=False)
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.approver_status_id, 2)
        self.assertFalse(self.pr.is_draft)

    def test_item_in_cp_hides_button_and_blocks_request(self):
        self._create_cp()
        self.assertNotIn(self.request_url, self._show_html())
        self.client.post(self.request_url)
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.approver_status_id, 2)

    def test_cancelled_po_does_not_block_request(self):
        self._create_po(is_cancel=True)
        self.assertIn(self.request_url, self._show_html())
        self.client.post(self.request_url)
        self.pr.refresh_from_db()
        self.assertTrue(self.pr.is_draft)

    def test_supplies_without_edit_pr_group_can_request(self):
        #ไม่ต้องอยู่กลุ่ม EditPR แล้ว แค่กลุ่มพัสดุก็ขอเปลี่ยนแปลงได้
        self.assertFalse(self.user.groups.filter(name='EditPR').exists())
        self.assertIn(self.request_url, self._show_html())
        self.client.post(self.request_url)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_non_supplies_user_cannot_see_or_request(self):
        #superuser หรือคนที่ไม่ใช่พัสดุ ไม่เห็นปุ่มและขอเปลี่ยนแปลงไม่ได้
        self.user.groups.remove(Group.objects.get(name='พัสดุ'))
        self.user.is_superuser = True
        self.user.save()
        self.assertNotIn(self.request_url, self._show_html())
        self.assertEqual(self.client.post(self.request_url).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_send_shows_alert_on_pr_list(self):
        #หลังบันทึกและส่งอนุมัติ หน้ารายการใบขอซื้อแสดง alert แจ้งผล
        self.client.post(self.request_url)
        response = self._post('')
        html = self.client.get(response.url).content.decode('utf-8')
        self.assertIn('alert-info', html)
        self.assertIn('ส่งอนุมัติใบขอซื้อ ' + str(self.pr.ref_no) + ' ใหม่เรียบร้อยแล้ว', html)
