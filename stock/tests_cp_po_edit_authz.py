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
    BaseDelivery,
    BasePermission,
    BasePOType,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


class EditAuthzBase(TestCase):
    """ผู้ใช้สำหรับทดสอบสิทธิหน้าแก้ไข: ผู้จัดทำ (จัดซื้อ), จัดซื้อคนอื่นในบริษัทเดียวกัน, superuser"""

    def setUp(self):
        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_authz_1", name="Distributor 1", credit=self.credit, vat_type=self.vat_type,
        )
        self.distributor2 = Distributor.objects.create(
            id="dist_authz_2", name="Distributor 2", credit=self.credit, vat_type=self.vat_type,
        )
        for i, name in ((1, "รอดำเนินการ"), (2, "อนุมัติ"), (3, "ไม่อนุมัติ"), (4, "ไม่ต้องอนุมัติ")):
            BaseApproveStatus.objects.create(id=i, name=name)

        purchasing, _ = Group.objects.get_or_create(name='จัดซื้อ')
        self.owner = self._user('authz_owner', purchasing)
        self.colleague = self._user('authz_colleague', purchasing)
        self.superuser = self._user('authz_super')
        self.superuser.is_superuser = True
        self.superuser.save()

    def _user(self, username, group=None):
        user = User.objects.create_user(username=username, password='password')
        if group:
            user.groups.add(group)
        profile = UserProfile.objects.create(user=user)
        profile.branch_company.add(self.branch)
        return user

    def _client(self, user=None):
        client = Client()
        if user:
            client.force_login(user)
        session = client.session
        session['company_code'] = 'HO'
        session.save()
        return client

    def assertRedirectsToSignIn(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('signIn'), response['Location'])


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ComparisonPriceEditAuthzTestCase(EditAuthzBase):
    """หน้าแก้ไขใบเปรียบเทียบราคา: แก้ได้เฉพาะผู้จัดทำ/superuser และเฉพาะใบที่ยังรอตรวจสอบ"""

    def setUp(self):
        super().setUp()
        self.examiner = User.objects.create_user(username='authz_exam', password='password')
        self.approver = User.objects.create_user(username='authz_appr', password='password')
        BasePermission.objects.create(
            codename='CASCP', name='special', ap_amount_min=Decimal('200000'), ap_amount_max=Decimal('99999999'),
        )
        self.cp = ComparisonPrice.objects.create(
            organizer=self.owner, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1, is_draft=False,
        )
        self.cpd = self._cpd(self.cp, self.distributor)
        self.cpd2 = self._cpd(self.cp, self.distributor2)

        self.other_cp = ComparisonPrice.objects.create(
            organizer=self.colleague, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1,
        )
        self.other_cpd = self._cpd(self.other_cp, self.distributor)

    def _cpd(self, cp, distributor):
        return ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('1000.00'), amount=Decimal('1070.00'),
        )

    def _approve(self):
        self.cp.select_bidder = self.distributor
        self.cp.examiner_user = self.examiner
        self.cp.approver_user = self.approver
        self.cp.examiner_status_id = 2
        self.cp.approver_status_id = 2
        self.cp.special_approver_status_id = 4
        self.cp.save()

    # ---------- printComparePricePO (เลือกร้านค้า / ส่งอนุมัติ) ----------
    def _print_url(self):
        return reverse('printComparePricePO', args=(self.cp.id,))

    def _select_bidder_data(self, distributor):
        return {
            'select_bidder': distributor.id, 'address_company': self.address.id,
            'examiner_user': self.examiner.id, 'approver_user': self.approver.id,
            'amount_diff': '0.00', 'note': '', 'btnSaveAndSend': '',
        }

    def test_print_requires_login(self):
        self.assertRedirectsToSignIn(self._client().get(self._print_url()))

    def test_print_owner_sends_pending_cp(self):
        response = self._client(self.owner).post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.select_bidder, self.distributor2)

    def test_print_superuser_sends_pending_cp(self):
        response = self._client(self.superuser).post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 302)

    def test_print_colleague_forbidden(self):
        client = self._client(self.colleague)
        self.assertEqual(client.get(self._print_url()).status_code, 403)
        response = client.post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertIsNone(self.cp.select_bidder)

    def test_print_owner_cannot_change_bidder_of_approved_cp(self):
        self._approve()
        response = self._client(self.owner).post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.select_bidder, self.distributor)
        self.assertEqual(self.cp.approver_status_id, 2)

    def test_print_superuser_cannot_change_bidder_of_approved_cp(self):
        self._approve()
        response = self._client(self.superuser).post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.select_bidder, self.distributor)

    def test_print_allowed_after_re_approve_request(self):
        self._approve()
        client = self._client(self.owner)
        client.post(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.examiner_status_id, 1)
        response = client.post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.select_bidder, self.distributor2)
        self.assertEqual(self.cp.approver_status_id, 1)

    def _cancel_and_re_approve(self):
        self._approve()
        ComparisonPrice.objects.filter(id=self.cp.id).update(is_cancel=True, cancel_reason='x')
        client = self._client(self.owner)
        self.assertEqual(client.post(reverse('requestCPReApprove', args=(self.cp.id,))).status_code, 302)
        self.cp.refresh_from_db()
        return client

    def test_cancelled_cp_stays_cancelled_until_sent(self):
        client = self._cancel_and_re_approve()
        self.assertTrue(self.cp.is_cancel)
        self.assertTrue(self.cp.is_draft)
        self.assertEqual(self.cp.examiner_status_id, 1)

        data = self._select_bidder_data(self.distributor2)
        del data['btnSaveAndSend']
        data['btnSaveDraft'] = ''
        self.assertEqual(client.post(self._print_url(), data).status_code, 302)
        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_cancel)

    def test_cancelled_cp_uncancelled_when_sent_after_re_approve(self):
        client = self._cancel_and_re_approve()
        response = client.post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_cancel)
        self.assertIsNone(self.cp.cancel_reason)
        self.assertFalse(self.cp.is_draft)
        self.assertEqual(self.cp.approver_status_id, 1)
        #กลับมาแสดงในหน้ารายการใบเปรียบเทียบราคา
        listed = {cp.id for cp in client.get(reverse('viewComparePricePO')).context['cps']}
        self.assertIn(self.cp.id, listed)

    def test_send_without_re_approve_keeps_cancel(self):
        #ใบรอตรวจสอบที่ยกเลิกแล้ว แต่ไม่ได้อยู่ในฉบับแก้ไข ส่งอนุมัติก็ไม่ปลดสถานะยกเลิก
        ComparisonPrice.objects.filter(id=self.cp.id).update(is_cancel=True, cancel_reason='x')
        response = self._client(self.owner).post(self._print_url(), self._select_bidder_data(self.distributor2))
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_cancel)

    # ---------- createComparePricePOItem (เพิ่มร้านค้า) ----------
    def _create_url(self, cp=None):
        return reverse('createComparePricePOItem', args=((cp or self.cp).id, 'False'))

    def _bidder_data(self, cp_id):
        return {
            'distributor': self.distributor2.id, 'cp': cp_id, 'total_price': '500.00', 'discount': '',
            'total_after_discount': '500.00', 'vat': '35.00', 'amount': '535.00',
            'credit': self.credit.id, 'vat_type': self.vat_type.id, 'freight': '',
            'form-TOTAL_FORMS': '0', 'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
        }

    def test_create_item_requires_login(self):
        self.assertRedirectsToSignIn(self._client().get(self._create_url()))

    def test_create_item_owner_and_superuser_open_pending_cp(self):
        self.assertEqual(self._client(self.owner).get(self._create_url()).status_code, 200)
        self.assertEqual(self._client(self.superuser).get(self._create_url()).status_code, 200)

    def test_create_item_colleague_forbidden(self):
        client = self._client(self.colleague)
        self.assertEqual(client.get(self._create_url()).status_code, 403)
        response = client.post(self._create_url(), self._bidder_data(self.cp.id))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ComparisonPriceDistributor.objects.filter(cp=self.cp).count(), 2)

    def test_create_item_approved_cp_forbidden_even_for_superuser(self):
        self._approve()
        self.assertEqual(self._client(self.owner).get(self._create_url()).status_code, 403)
        response = self._client(self.superuser).post(self._create_url(), self._bidder_data(self.cp.id))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ComparisonPriceDistributor.objects.filter(cp=self.cp).count(), 2)

    def test_create_item_ignores_cp_id_posted_in_form(self):
        #ส่ง cp ของใบอื่นใน hidden input ต้องผูกกับใบตาม URL
        response = self._client(self.owner).post(self._create_url(), self._bidder_data(self.other_cp.id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ComparisonPriceDistributor.objects.filter(cp=self.cp).count(), 3)
        self.assertEqual(ComparisonPriceDistributor.objects.filter(cp=self.other_cp).count(), 1)

    # ---------- editComparePricePOItem / editComparePricePOItemFromPR ----------
    def _edit_data(self, cp_id):
        data = self._bidder_data(cp_id)
        for key in ('form-TOTAL_FORMS', 'form-INITIAL_FORMS', 'form-MIN_NUM_FORMS', 'form-MAX_NUM_FORMS'):
            data.pop(key)
        data.update({
            'distributor': self.distributor.id,
            'comparisonpriceitem_set-TOTAL_FORMS': '0', 'comparisonpriceitem_set-INITIAL_FORMS': '0',
            'comparisonpriceitem_set-MIN_NUM_FORMS': '0', 'comparisonpriceitem_set-MAX_NUM_FORMS': '1000',
        })
        return data

    def _check_edit_view(self, name):
        url = reverse(name, args=(self.cp.id, self.cpd.id))
        self.assertRedirectsToSignIn(self._client().get(url))
        self.assertEqual(self._client(self.owner).get(url).status_code, 200)
        self.assertEqual(self._client(self.superuser).get(url).status_code, 200)

        response = self._client(self.colleague).post(url, self._edit_data(self.cp.id))
        self.assertEqual(response.status_code, 403)
        self.cpd.refresh_from_db()
        self.assertEqual(self.cpd.amount, Decimal('1070.00'))

        #ร้านค้าของใบอื่น ใส่ cp_id ของใบตัวเองใน URL
        url_mismatch = reverse(name, args=(self.cp.id, self.other_cpd.id))
        self.assertEqual(self._client(self.owner).get(url_mismatch).status_code, 404)

        #ส่ง cp ของใบอื่นใน hidden input ต้องไม่ย้ายร้านค้าไปใบอื่น
        response = self._client(self.owner).post(url, self._edit_data(self.other_cp.id))
        self.assertEqual(response.status_code, 302)
        self.cpd.refresh_from_db()
        self.assertEqual(self.cpd.cp_id, self.cp.id)
        self.assertEqual(self.cpd.amount, Decimal('535.00'))

        self._approve()
        self.assertEqual(self._client(self.owner).get(url).status_code, 403)
        self.assertEqual(self._client(self.superuser).post(url, self._edit_data(self.cp.id)).status_code, 403)

    def test_edit_item_permissions(self):
        self._check_edit_view('editComparePricePOItem')

    def test_edit_item_from_pr_permissions(self):
        self._check_edit_view('editComparePricePOItemFromPR')

    # ---------- removeComparePriceDistributor ----------
    def _remove_url(self, cpd=None):
        cpd = cpd or self.cpd2
        return reverse('removeComparePriceDistributor', args=(self.cp.id, cpd.id))

    def test_remove_requires_login(self):
        self.assertRedirectsToSignIn(self._client().post(self._remove_url()))
        self.assertTrue(ComparisonPriceDistributor.objects.filter(id=self.cpd2.id).exists())

    def test_remove_owner_on_pending_cp(self):
        self.assertEqual(self._client(self.owner).post(self._remove_url()).status_code, 302)
        self.assertFalse(ComparisonPriceDistributor.objects.filter(id=self.cpd2.id).exists())

    def test_remove_superuser_on_pending_cp(self):
        self.assertEqual(self._client(self.superuser).post(self._remove_url()).status_code, 302)
        self.assertFalse(ComparisonPriceDistributor.objects.filter(id=self.cpd2.id).exists())

    def test_remove_colleague_forbidden(self):
        self.assertEqual(self._client(self.colleague).post(self._remove_url()).status_code, 403)
        self.assertTrue(ComparisonPriceDistributor.objects.filter(id=self.cpd2.id).exists())

    def test_remove_approved_cp_forbidden(self):
        self._approve()
        self.assertEqual(self._client(self.superuser).post(self._remove_url()).status_code, 403)
        self.assertTrue(ComparisonPriceDistributor.objects.filter(id=self.cpd2.id).exists())

    def test_remove_rejects_get(self):
        #ลบด้วย GET (ลิงก์/รูปภาพจากเว็บอื่น) ไม่ได้ ต้องเป็น POST ที่มี CSRF
        self.assertEqual(self._client(self.owner).get(self._remove_url()).status_code, 405)
        self.assertTrue(ComparisonPriceDistributor.objects.filter(id=self.cpd2.id).exists())

    def test_remove_buttons_are_post_forms(self):
        for name, args in (('createComparePricePOItem', (self.cp.id, 'False')),
                           ('editComparePricePOItem', (self.cp.id, self.cpd.id))):
            html = self._client(self.owner).get(reverse(name, args=args)).content.decode('utf-8')
            self.assertIn(f'<form method="post" action="{self._remove_url()}"', html, name)
            self.assertNotIn(f'href="{self._remove_url()}"', html, name)

    def test_remove_distributor_of_other_cp_not_found(self):
        self.assertEqual(self._client(self.owner).post(self._remove_url(self.other_cpd)).status_code, 404)
        self.assertTrue(ComparisonPriceDistributor.objects.filter(id=self.other_cpd.id).exists())

    # ---------- requestCPReApprove ----------
    def test_re_approve_request_colleague_forbidden(self):
        self._approve()
        response = self._client(self.colleague).post(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.assertEqual(response.status_code, 403)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.examiner_status_id, 2)

    def test_re_approve_request_superuser_without_purchasing_group(self):
        self._approve()
        response = self._client(self.superuser).post(reverse('requestCPReApprove', args=(self.cp.id,)))
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertEqual(self.cp.examiner_status_id, 1)
        self.assertTrue(self.cp.is_re_approve)

    def test_show_cp_re_approve_button_only_for_owner(self):
        self._approve()
        url = reverse('showComparePricePO', kwargs={'cp_id': self.cp.id, 'mode': 1})
        self.assertTrue(self._client(self.owner).get(url).context['canRequestReApprove'])
        self.assertFalse(self._client(self.colleague).get(url).context['canRequestReApprove'])


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PurchaseOrderEditAuthzTestCase(EditAuthzBase):
    """editPOItem: แก้ได้เฉพาะผู้จัดทำ/superuser เฉพาะใบที่รออนุมัติ และตัดสินฉบับแก้ไขจากฐานข้อมูล ไม่ใช่ URL"""

    def setUp(self):
        super().setUp()
        self.po_type = BasePOType.objects.create(id="po_type_authz", name="Standard PO")
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        self.delivery = BaseDelivery.objects.create(name="คลังสินค้า")
        self.approver = User.objects.create_user(username='authz_po_appr', password='password')
        self.requisit = Requisition.objects.create(
            purchase_requisition_id=1, pr_ref_no="PR-AUTHZ-001", name=self.owner,
            chief_approve_user_name=self.owner, supplies_approve_user_name=self.owner,
            branch_company=self.branch,
        )
        PurchaseRequisition.objects.create(requisition=self.requisit, branch_company=self.branch)
        self.req_item = RequisitionItem.objects.create(
            requisition_id=1, requisit=self.requisit, product_name="Test Item 1", quantity=5, quantity_pr=5
        )
        self.po = PurchaseOrder.objects.create(
            vat_type=self.vat_type, ref_no="PO-AUTHZ-001", distributor=self.distributor,
            credit=self.credit, stockman_user=self.owner, approver_user=self.approver,
            branch_company=self.branch, address_company=self.address, po_type=self.po_type,
            approver_status_id=1, due_receive_update=datetime.date(2026, 7, 20), is_draft=False,
            total_price=Decimal('100.00'), total_after_discount=Decimal('100.00'),
            vat=Decimal('7.00'), amount=Decimal('107.00'),
        )
        self.item = PurchaseOrderItem.objects.create(
            po=self.po, item=self.req_item, quantity=Decimal('5.0000'), unit=self.unit,
            unit_price=Decimal('20.0000'), price=Decimal('100.00'),
        )

    def _url(self, re_approve='False'):
        return reverse('editPOItem', kwargs={'po_id': self.po.id, 'isFromPR': 'False', 'isReApprove': re_approve})

    def _post_data(self, note='changed'):
        return {
            'purchaseorderitem_set-TOTAL_FORMS': '1', 'purchaseorderitem_set-INITIAL_FORMS': '1',
            'purchaseorderitem_set-MIN_NUM_FORMS': '0', 'purchaseorderitem_set-MAX_NUM_FORMS': '1000',
            'purchaseorderitem_set-0-id': self.item.id, 'purchaseorderitem_set-0-po': self.po.id,
            'purchaseorderitem_set-0-item': self.req_item.id,
            'purchaseorderitem_set-0-quantity': '5.0000', 'purchaseorderitem_set-0-unit': self.unit.id,
            'purchaseorderitem_set-0-unit_price': '20.0000', 'purchaseorderitem_set-0-price': '100.00',
            'distributor': self.distributor.id, 'credit': self.credit.id, 'shipping': 'EMS',
            'vat_type': self.vat_type.id, 'address_company': self.address.id,
            'approver_user': self.approver.id, 'due_receive_update': '2026-08-25',
            'po_type': self.po_type.id,
            'total_price': '100.00', 'discount': '0.00', 'total_after_discount': '100.00',
            'freight': '0.00', 'vat': '7.00', 'amount': '107.00', 'note': note,
            'delivery': self.delivery.id,
        }

    def _set(self, **fields):
        PurchaseOrder.objects.filter(id=self.po.id).update(**fields)
        self.po.refresh_from_db()

    def test_requires_login(self):
        self.assertRedirectsToSignIn(self._client().get(self._url()))

    def test_owner_and_superuser_edit_pending_po(self):
        self.assertEqual(self._client(self.owner).get(self._url()).status_code, 200)
        response = self._client(self.superuser).post(self._url(), self._post_data())
        self.assertEqual(response.status_code, 302)
        self.po.refresh_from_db()
        self.assertEqual(self.po.note, 'changed')

    def test_colleague_forbidden(self):
        client = self._client(self.colleague)
        self.assertEqual(client.get(self._url()).status_code, 403)
        self.assertEqual(client.post(self._url(), self._post_data()).status_code, 403)
        self.po.refresh_from_db()
        self.assertNotEqual(self.po.note, 'changed')

    def test_approved_po_forbidden_even_with_re_approve_url(self):
        self._set(approver_status_id=2)
        for user in (self.owner, self.superuser):
            for flag in ('False', 'True'):
                response = self._client(user).post(self._url(flag), self._post_data())
                self.assertEqual(response.status_code, 403, (user.username, flag))
        self.po.refresh_from_db()
        self.assertEqual(self.po.approver_status_id, 2)
        self.assertNotEqual(self.po.note, 'changed')

    def test_cancelled_po_cannot_be_uncancelled_via_url(self):
        #เดิม isReApprove=True ใน URL เปลี่ยน is_cancel = False ได้เลย
        self._set(is_cancel=True, cancel_reason='x')
        response = self._client(self.owner).post(self._url('True'), self._post_data())
        self.assertEqual(response.status_code, 403)
        self.po.refresh_from_db()
        self.assertTrue(self.po.is_cancel)

    def test_re_approve_url_flag_does_not_mark_po_as_re_approve(self):
        response = self._client(self.owner).post(self._url('True'), self._post_data())
        self.assertEqual(response.status_code, 302)
        self.po.refresh_from_db()
        self.assertFalse(self.po.is_re_approve)

    def test_cancelled_po_enters_revision_via_re_approve_request(self):
        self._set(is_cancel=True, cancel_reason='x', approver_status_id=2)
        client = self._client(self.owner)
        response = client.post(reverse('requestPOReApprove', kwargs={'po_id': self.po.id}))
        self.assertRedirects(response, self._url('True'), fetch_redirect_response=False)
        self.assertEqual(client.get(self._url('False')).status_code, 200)

        response = client.post(self._url('False'), self._post_data())
        self.assertEqual(response.status_code, 302)
        self.po.refresh_from_db()
        self.assertFalse(self.po.is_cancel)
        self.assertIsNone(self.po.cancel_reason)
        self.assertEqual(self.po.approver_status_id, 1)
        self.assertTrue(self.po.is_re_approve)
        self.assertFalse(self.po.is_draft)

    def test_re_approve_request_colleague_forbidden(self):
        self._set(approver_status_id=2)
        response = self._client(self.colleague).post(reverse('requestPOReApprove', kwargs={'po_id': self.po.id}))
        self.assertEqual(response.status_code, 403)
        self.po.refresh_from_db()
        self.assertEqual(self.po.approver_status_id, 2)

    def test_re_approve_request_superuser_without_purchasing_group(self):
        self._set(approver_status_id=2)
        response = self._client(self.superuser).post(reverse('requestPOReApprove', kwargs={'po_id': self.po.id}))
        self.assertEqual(response.status_code, 302)
        self.po.refresh_from_db()
        self.assertEqual(self.po.approver_status_id, 1)
        self.assertTrue(self.po.is_re_approve)

    def test_show_po_re_approve_button_only_for_owner(self):
        self._set(approver_status_id=2)
        url = reverse('showPO', kwargs={'po_id': self.po.id, 'mode': 1})
        owner_html = self._client(self.owner).get(url).content.decode('utf-8')
        colleague_html = self._client(self.colleague).get(url).content.decode('utf-8')
        action = reverse('requestPOReApprove', kwargs={'po_id': self.po.id})
        self.assertIn(action, owner_html)
        self.assertNotIn(action, colleague_html)

    def test_show_cancelled_po_re_approve_is_post_form(self):
        self._set(is_cancel=True, cancel_reason='x', approver_status_id=2)
        html = self._client(self.owner).get(reverse('showPO', kwargs={'po_id': self.po.id, 'mode': 1})).content.decode('utf-8')
        self.assertIn(reverse('requestPOReApprove', kwargs={'po_id': self.po.id}), html)
        self.assertNotIn(f'href="{self._url("True")}"', html)

    # ---------- editPOFromPR (หน้าข้อมูลหัวใบสั่งซื้อจากใบขอซื้อ ก่อนเข้า editPOItem) ----------
    def _from_pr_url(self):
        return reverse('editPOFromPR', args=(self.po.id,))

    def _from_pr_data(self):
        return {
            'distributor': self.distributor.id, 'credit': self.credit.id, 'shipping': 'KERRY',
            'vat_type': self.vat_type.id, 'address_company': self.address.id,
            'approver_user': '', 'due_receive_update': '2026-08-25', 'po_type': self.po_type.id,
        }

    def test_from_pr_requires_login(self):
        self.assertRedirectsToSignIn(self._client().get(self._from_pr_url()))

    def test_from_pr_owner_and_superuser_edit_pending_po(self):
        self.assertEqual(self._client(self.superuser).get(self._from_pr_url()).status_code, 200)
        response = self._client(self.owner).post(self._from_pr_url(), self._from_pr_data())
        self.assertRedirects(
            response,
            reverse('editPOItem', kwargs={'po_id': self.po.id, 'isFromPR': 'True', 'isReApprove': 'False'}),
            fetch_redirect_response=False,
        )
        self.po.refresh_from_db()
        self.assertEqual(self.po.shipping, 'KERRY')

    def test_from_pr_colleague_forbidden(self):
        client = self._client(self.colleague)
        self.assertEqual(client.get(self._from_pr_url()).status_code, 403)
        self.assertEqual(client.post(self._from_pr_url(), self._from_pr_data()).status_code, 403)
        self.po.refresh_from_db()
        self.assertNotEqual(self.po.shipping, 'KERRY')

    def test_from_pr_approved_or_cancelled_po_forbidden_even_for_superuser(self):
        for fields in ({'approver_status_id': 2}, {'approver_status_id': 1, 'is_cancel': True, 'cancel_reason': 'x'}):
            self._set(**fields)
            for user in (self.owner, self.superuser):
                response = self._client(user).post(self._from_pr_url(), self._from_pr_data())
                self.assertEqual(response.status_code, 403, (fields, user.username))
        self.po.refresh_from_db()
        self.assertNotEqual(self.po.shipping, 'KERRY')
