from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BasePermission,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Distributor,
)


class ComparisonPriceSaveDraftTestCase(TestCase):
    """ใบเปรียบเทียบราคา: ปุ่มบันทึกแบบร่าง (ไม่ส่งไปหาผู้อนุมัติ) และปุ่มบันทึกและส่งอนุมัติ"""

    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username='cp_draft_org', password='password')
        self.examiner = User.objects.create_user(username='cp_draft_exam', password='password')
        self.approver = User.objects.create_user(username='cp_draft_appr', password='password')
        self.client.login(username='cp_draft_org', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_cp_draft", name="Test Distributor", credit=self.credit, vat_type=self.vat_type,
        )
        for i, name in ((1, "รอดำเนินการ"), (2, "อนุมัติ"), (3, "ไม่อนุมัติ"), (4, "ไม่ต้องอนุมัติ")):
            BaseApproveStatus.objects.create(id=i, name=name)
        BasePermission.objects.create(
            codename='CASCP', name='special', ap_amount_min=Decimal('200000'), ap_amount_max=Decimal('99999999'),
        )

        self.cp = ComparisonPrice.objects.create(
            organizer=self.organizer, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1, is_draft=False,
        )
        ComparisonPriceDistributor.objects.create(
            cp=self.cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('1000.00'), amount=Decimal('1070.00'),
        )
        self.url = reverse('printComparePricePO', args=(self.cp.id,))

    def _post_data(self, **extra):
        data = {
            'select_bidder': self.distributor.id,
            'address_company': self.address.id,
            'examiner_user': self.examiner.id,
            'approver_user': self.approver.id,
            'amount_diff': '0.00',
            'note': '',
        }
        data.update(extra)
        return data

    def test_save_draft_marks_cp_as_draft_and_hides_from_examiner(self):
        data = self._post_data()
        data['btnSaveDraft'] = ''
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('viewComparePricePO'), fetch_redirect_response=False)

        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_draft)
        self.assertEqual(self.cp.examiner_user, self.examiner)
        # ยังไม่ส่ง จึงไม่เก็บวันที่เลือกร้าน
        self.assertIsNone(self.cp.select_bidder_update)
        self.assertFalse(
            ComparisonPrice.objects.filter(
                examiner_status=1, is_draft=False, examiner_user=self.examiner,
            ).exists()
        )

    def test_save_draft_allows_empty_bidder_and_approvers(self):
        data = {'btnSaveDraft': '', 'address_company': self.address.id}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_draft)
        self.assertIsNone(self.cp.select_bidder)
        self.assertIsNone(self.cp.examiner_user)

    def test_save_and_send_clears_draft(self):
        self.cp.is_draft = True
        self.cp.save()

        data = self._post_data()
        data['btnSaveAndSend'] = ''
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)
        self.assertIsNotNone(self.cp.select_bidder_update)
        self.assertTrue(
            ComparisonPriceDistributor.objects.get(cp=self.cp, distributor=self.distributor).is_select
        )

    def test_save_and_send_still_requires_examiner_and_approver(self):
        data = self._post_data(examiner_user='', approver_user='')
        data['btnSaveAndSend'] = ''
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)
        self.assertIsNone(self.cp.examiner_user)

    # ---------- แท็ปหน้า /comparePricePO/ ----------
    def _make_list_cp(self, is_draft):
        return ComparisonPrice.objects.create(
            organizer=self.organizer, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1, is_draft=is_draft,
        )

    def _listed_ids(self, response):
        return {cp.id for cp in response.context['cps']}

    def test_view_process_tab_lists_only_non_draft(self):
        draft = self._make_list_cp(is_draft=True)
        response = self.client.get(reverse('viewComparePricePO'))
        self.assertEqual(response.context['tab'], 'process')
        ids = self._listed_ids(response)
        self.assertIn(self.cp.id, ids)
        self.assertNotIn(draft.id, ids)
        self.assertEqual(response.context['count_process'], 1)
        self.assertEqual(response.context['count_draft'], 1)

    def test_view_draft_tab_lists_only_draft(self):
        draft = self._make_list_cp(is_draft=True)
        response = self.client.get(reverse('viewComparePricePO'), {'tab': 'draft'})
        self.assertEqual(response.context['tab'], 'draft')
        self.assertEqual(self._listed_ids(response), {draft.id})

    def test_view_tab_links_keep_filter_but_drop_page(self):
        response = self.client.get(reverse('viewComparePricePO'), {'tab': 'draft', 'ref_no': 'CM', 'page': '2'})
        self.assertEqual(response.context['tab_qs'], 'ref_no=CM')

    # ---------- ฉบับแก้ไข (ขอเปลี่ยนแปลงรายละเอียดรายการ) ----------
    def _approved_cp(self):
        self.cp.select_bidder = self.distributor
        self.cp.examiner_user = self.examiner
        self.cp.approver_user = self.approver
        self.cp.examiner_status_id = 2
        self.cp.approver_status_id = 2
        self.cp.special_approver_status_id = 4
        self.cp.save()
        ComparisonPriceDistributor.objects.filter(cp=self.cp).update(is_select=True)

    def _examiner_can_approve(self):
        client = Client()
        client.force_login(self.examiner)
        session = client.session
        session['company_code'] = 'HO'
        session.save()
        response = client.get(reverse('printCPApprove', args=(self.cp.id, 'False')))
        self.assertEqual(response.status_code, 200)
        return response.context['isExaminer']

    def _make_purchasing(self, user):
        from django.contrib.auth.models import Group
        from stock.models import UserProfile
        user.groups.add(Group.objects.get_or_create(name='จัดซื้อ')[0])
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.branch_company.add(self.branch)

    def test_re_approve_makes_cp_draft_until_sent(self):
        self._approved_cp()
        self._make_purchasing(self.organizer)
        response = self.client.post(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.assertRedirects(
            response, reverse('createComparePricePOItem', args=(self.cp.id, 'False')),
            fetch_redirect_response=False,
        )

        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_re_approve)
        self.assertTrue(self.cp.is_draft)
        self.assertEqual(self.cp.examiner_status_id, 1)
        #ยังเป็นแบบร่าง ผู้ตรวจสอบยังอนุมัติไม่ได้
        self.assertFalse(self._examiner_can_approve())

        data = self._post_data()
        data['btnSaveAndSend'] = ''
        self.assertEqual(self.client.post(self.url, data).status_code, 302)

        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)
        #ส่งอนุมัติแล้ว ผู้ตรวจสอบอนุมัติได้
        self.assertTrue(self._examiner_can_approve())

    def test_normal_edit_does_not_make_cp_draft(self):
        self.client.get(reverse('createComparePricePOItem', args=(self.cp.id, 'False')))
        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)

    # ---------- ค่าเริ่มต้นเป็นแบบร่าง ----------
    def test_new_cp_starts_as_draft_until_sent(self):
        cp = ComparisonPrice.objects.create(
            organizer=self.organizer, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1,
        )
        self.assertTrue(cp.is_draft)
        ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('1000.00'), amount=Decimal('1070.00'),
        )
        data = self._post_data()
        data['btnSaveAndSend'] = ''
        response = self.client.post(reverse('printComparePricePO', args=(cp.id,)), data)
        self.assertEqual(response.status_code, 302)
        cp.refresh_from_db()
        self.assertFalse(cp.is_draft)

    # ---------- ความปลอดภัย: ขอเปลี่ยนแปลงรายละเอียดรายการ ----------
    def test_get_create_item_page_with_re_approve_flag_does_not_change_cp(self):
        self._approved_cp()
        response = self.client.get(reverse('createComparePricePOItem', args=(self.cp.id, 'True')))
        #ใบที่ตรวจสอบแล้วเปิดหน้าแก้ไขไม่ได้ ต้องขอเปลี่ยนแปลงรายละเอียดรายการก่อน
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.examiner_status_id, 2)
        self.assertFalse(self.cp.is_draft)

    def test_request_cp_re_approve_rejects_get(self):
        self._approved_cp()
        self._make_purchasing(self.organizer)
        response = self.client.get(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.assertEqual(response.status_code, 405)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.approver_status_id, 2)

    def test_request_cp_re_approve_requires_purchasing_in_company(self):
        self._approved_cp()
        #ไม่ใช่จัดซื้อ
        response = self.client.post(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.assertEqual(response.status_code, 403)
        #จัดซื้อ แต่ไม่อยู่บริษัทของใบ
        from django.contrib.auth.models import Group
        self.organizer.groups.add(Group.objects.get_or_create(name='จัดซื้อ')[0])
        response = self.client.post(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.approver_status_id, 2)
        self.assertFalse(self.cp.is_draft)

    def test_save_draft_rejected_on_examined_cp(self):
        self._approved_cp()
        data = self._post_data()
        data['btnSaveDraft'] = ''
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)
        self.assertEqual(self.cp.approver_status_id, 2)

    def test_draft_cp_never_auto_approves_po(self):
        from stock.views import auto_approve_po_from_cp
        from stock.models import PurchaseOrder
        self._approved_cp()
        self.cp.is_draft = True
        po = PurchaseOrder(amount=Decimal('100.00'), approver_status_id=1)
        self.assertFalse(auto_approve_po_from_cp(po, self.cp))
        self.assertEqual(po.approver_status_id, 1)
