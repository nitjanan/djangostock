from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


class _PRBase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pr_fix_user', password='password')
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        for i, name in ((1, "รอดำเนินการ"), (2, "อนุมัติ"), (3, "ไม่อนุมัติ")):
            BaseApproveStatus.objects.create(id=i, name=name)
        UserProfile.objects.create(user=self.user).branch_company.add(self.branch)
        self.supplies = Group.objects.create(name='พัสดุ')
        self.purchasing = Group.objects.create(name='จัดซื้อ')
        self.user.groups.add(self.supplies)

    def _pr(self, ref, approver_status=1, is_draft=False, machines=('M1',), **kwargs):
        rq = Requisition.objects.create(
            name=self.user, chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        pr = PurchaseRequisition.objects.create(
            ref_no=ref, requisition=rq, branch_company=self.branch, address_company=self.address,
            purchase_status_id=2, approver_status_id=approver_status, is_draft=is_draft, **kwargs,
        )
        for m in machines:
            RequisitionItem.objects.create(
                requisition_id=rq.id, requisit=rq, product_name='สินค้า ' + m, machine=m,
                quantity=1, quantity_pr=1,
            )
        return pr


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PRFilterNoDuplicateRowsTestCase(_PRBase):
    """กรองใบขอซื้อด้วยช่องของรายการสินค้า: ใบที่มีหลายรายการตรงคำค้นต้องขึ้นแถวเดียว"""

    def test_item_machine_filter_does_not_duplicate_rows(self):
        pr = self._pr('PR-DUP-001', machines=('M1', 'M1-B'))
        self._pr('PR-DUP-002', machines=('X9',))
        response = self.client.get(reverse('viewPR'), {'item_machine': 'M1'})
        html = response.content.decode('utf-8')
        self.assertEqual(html.count('id="row-%d"' % pr.id), 1)
        self.assertNotIn('PR-DUP-002', html)
        self.assertEqual(response.context['count_process'], 1)

    def test_item_product_name_filter_does_not_duplicate_rows(self):
        pr = self._pr('PR-DUP-003', machines=('A', 'B'))
        html = self.client.get(reverse('viewPR'), {'item_product_name': 'สินค้า'}).content.decode('utf-8')
        self.assertEqual(html.count('id="row-%d"' % pr.id), 1)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PRListPurchasingAndSuppliesTestCase(_PRBase):
    """คนที่อยู่ทั้งกลุ่มจัดซื้อและพัสดุ: ยังเห็นแท็ปแบบร่าง (เช่น ใบที่ขอเปลี่ยนแปลงรายละเอียดไว้)"""

    def setUp(self):
        super().setUp()
        self.user.groups.add(self.purchasing)

    def test_draft_tab_shows_drafts_without_create_cm_po_button(self):
        draft = self._pr('PR-BOTH-DRAFT', is_draft=True, is_re_approve=True)
        approved = self._pr('PR-BOTH-APPROVED', approver_status=2, organizer=self.user)

        response = self.client.get(reverse('viewPR'), {'tab': 'draft'})
        html = response.content.decode('utf-8')
        self.assertTrue(response.context['showDraftTabs'])
        self.assertIn('PR-BOTH-DRAFT', html)
        self.assertNotIn('PR-BOTH-APPROVED', html)
        self.assertNotIn(reverse('createCMorPO', args=(draft.id,)), html)
        self.assertIn(reverse('reApprovePR', args=(draft.id,)), html)

        html = self.client.get(reverse('viewPR')).content.decode('utf-8')
        self.assertIn(reverse('createCMorPO', args=(approved.id,)), html)
        self.assertNotIn('PR-BOTH-DRAFT', html)

    def test_purchasing_only_user_still_has_no_draft_tabs(self):
        self.user.groups.remove(self.supplies)
        self._pr('PR-PURCH-DRAFT', is_draft=True)
        response = self.client.get(reverse('viewPR'), {'tab': 'draft'})
        self.assertFalse(response.context['showDraftTabs'])
        self.assertNotIn('PR-PURCH-DRAFT', response.content.decode('utf-8'))


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ShowPRRejectedReApproveButtonTestCase(_PRBase):
    """หน้า showPR: ใบที่ไม่อนุมัติ กดขอเปลี่ยนแปลงรายละเอียดได้เหมือนแท็ปไม่อนุมัติใน viewPR"""

    def _html(self, pr):
        return self.client.get(reverse('showPR', args=(pr.id, 1))).content.decode('utf-8')

    def test_rejected_by_approver_shows_button(self):
        pr = self._pr('PR-REJ-001', approver_status=3)
        self.assertIn(reverse('requestPRReApprove', args=(pr.id,)), self._html(pr))

    def test_rejected_by_purchase_user_shows_button(self):
        pr = self._pr('PR-REJ-002', approver_status=1)
        PurchaseRequisition.objects.filter(id=pr.id).update(purchase_status_id=3)
        pr.refresh_from_db()
        self.assertIn(reverse('requestPRReApprove', args=(pr.id,)), self._html(pr))

    def test_pending_pr_has_no_button(self):
        pr = self._pr('PR-REJ-003', approver_status=1)
        self.assertNotIn(reverse('requestPRReApprove', args=(pr.id,)), self._html(pr))

    def test_rejected_item_in_po_hides_button(self):
        pr = self._pr('PR-REJ-004', approver_status=3)
        po = PurchaseOrder.objects.create(
            ref_no='PO-REJ-004', branch_company=self.branch, address_company=self.address,
            vat_type=BaseVatType.objects.get_or_create(id='1', defaults={'name': 'Vat 7%'})[0],
        )
        PurchaseOrderItem.objects.create(po=po, item=pr.requisition.requisitionitem_set.first(), quantity=1)
        self.assertNotIn(reverse('requestPRReApprove', args=(pr.id,)), self._html(pr))


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CreatePOItemFromCPWithoutBidderTestCase(_PRBase):
    """ลิงก์เดิม createPOItemFromComparisonPrice: ใบเปรียบเทียบที่ยังไม่ได้เลือกร้าน ต้องไม่ error 500"""

    def test_cp_without_selected_bidder_redirects_with_message(self):
        cp = ComparisonPrice.objects.create(
            ref_no='CM-NOBID-001', organizer=self.user, branch_company=self.branch, address_company=self.address,
        )
        po = PurchaseOrder.objects.create(
            ref_no='PO-NOBID-001', cp=cp, stockman_user=self.user, approver_status_id=1,
            branch_company=self.branch, address_company=self.address,
            vat_type=BaseVatType.objects.get_or_create(id='1', defaults={'name': 'Vat 7%'})[0],
        )
        response = self.client.get(reverse('createPOItemFromComparisonPrice', args=(po.id,)))
        self.assertRedirects(response, reverse('viewPO'), fetch_redirect_response=False)
        self.assertFalse(PurchaseOrderItem.objects.filter(po=po).exists())
