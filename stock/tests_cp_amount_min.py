from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCMType,
    BaseCredit,
    BasePermission,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    Distributor,
)
from stock.views import cp_amount_min_for_approve


class CPAmountMinTestCase(TestCase):
    """หน้าเลือกร้านค้า (/comparePricePO/print): ยอดของร้านที่เลือกไม่ถึงเกณฑ์สิทธิอนุมัติใบเปรียบเทียบ
    แจ้งเตือนและห้ามบันทึกและส่งอนุมัติ (บันทึกแบบร่างได้)"""

    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(username='cp_min_org', password='password')
        self.examiner = User.objects.create_user(username='cp_min_exam', password='password')
        self.approver = User.objects.create_user(username='cp_min_appr', password='password')
        self.client.force_login(self.organizer)
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_cp_min", name="Test Distributor", credit=self.credit, vat_type=self.vat_type,
        )
        for i, name in ((1, "รอดำเนินการ"), (2, "อนุมัติ"), (3, "ไม่อนุมัติ"), (4, "ไม่ต้องอนุมัติ")):
            BaseApproveStatus.objects.create(id=i, name=name)
        BasePermission.objects.create(
            codename='CASCP', name='special', codename_th='CASCP', ap_amount_min=Decimal('500001'), ap_amount_max=Decimal('99999999'),
        )
        #ช่วงยอดเงินสิทธิตรวจสอบ/อนุมัติ: ต่ำสุด 5,001
        for code, lo, hi in (('CAECP1', '5001', '10000'), ('CAACP1', '5001', '10000'),
                             ('CAECP2', '10001', '100000'), ('CAACP2', '10001', '100000'),
                             ('CAECPD', '0', '99999999'), ('CAACPD', '0', '99999999')):
            #codename_th เป็น unique ต้องไม่ซ้ำกัน
            BasePermission.objects.create(codename=code, name=code, codename_th=code, ap_amount_min=Decimal(lo), ap_amount_max=Decimal(hi))
        self.diesel = BaseCMType.objects.create(id='1', name='น้ำมันดีเซล')

        self.cp = ComparisonPrice.objects.create(
            organizer=self.organizer, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1, is_draft=True,
        )
        self.bidder = ComparisonPriceDistributor.objects.create(
            cp=self.cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('4000.00'), amount=Decimal('4280.00'),
        )
        self.url = reverse('printComparePricePO', args=(self.cp.id,))

    def _post(self, button='btnSaveAndSend', **extra):
        data = {
            'select_bidder': self.distributor.id,
            'address_company': self.address.id,
            'examiner_user': self.examiner.id,
            'approver_user': self.approver.id,
            'amount_diff': '0.00',
            'note': '',
            button: '',
        }
        data.update(extra)
        return self.client.post(self.url, data)

    def _set_amount(self, amount):
        self.bidder.amount = Decimal(amount)
        self.bidder.save()

    def test_min_is_lowest_cp_amount_permission(self):
        #CAECPD/CAACPD (ไม่ขึ้นกับยอดเงิน) และ CASCP ไม่นับ
        self.assertEqual(cp_amount_min_for_approve(), Decimal('5001.00'))

    def test_send_under_min_is_blocked(self):
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ยอดเงินของร้านที่เลือก 4,280 บาท ไม่ถึงเกณฑ์สิทธิอนุมัติใบเปรียบเทียบราคา (ตั้งแต่ 5,001 บาทขึ้นไป)')
        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_draft)
        self.assertIsNone(self.cp.select_bidder)

    def test_send_at_min_is_saved(self):
        self._set_amount('5001.00')
        response = self._post()
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)

    def test_save_draft_under_min_is_allowed(self):
        response = self._post(button='btnSaveDraft')
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertTrue(self.cp.is_draft)
        self.assertEqual(self.cp.select_bidder, self.distributor)

    def test_send_under_min_with_cm_type_is_allowed(self):
        #ใบเปรียบเทียบน้ำมันดีเซล ใช้สิทธิ CAECPD/CAACPD ที่ไม่ขึ้นกับยอดเงิน
        response = self._post(cm_type=self.diesel.id)
        self.assertEqual(response.status_code, 302)
        self.cp.refresh_from_db()
        self.assertFalse(self.cp.is_draft)

    def test_send_without_amount_permission_set_is_allowed(self):
        BasePermission.objects.filter(codename__in=['CAECP1', 'CAACP1', 'CAECP2', 'CAACP2']).delete()
        self.assertEqual(self._post().status_code, 302)

    def test_page_renders_min_and_warning_elements(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cp_approve_min'], '5001.00')
        self.assertContains(response, '<script id="cp-approve-min" type="application/json">"5001.00"</script>', html=False)
        self.assertContains(response, 'id="cp-amount-under-min"')
        self.assertContains(response, 'id="cp-amount-summary"')
        self.assertContains(response, 'function cpAmountUnderMinMessage')
