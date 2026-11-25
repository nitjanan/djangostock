from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    RequisitionItem,
    UserProfile,
)


class ItemListFixture(TestCase):
    """ข้อมูลตั้งต้นร่วมของเทสต์ช่องรายการสินค้าในหน้ารายการเอกสาร (ไม่มีเทสต์ในคลาสนี้เอง)"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='cp_items_user', password='password')
        cls.branch = BaseBranchCompany.objects.create(code='CPI', name='CP Items Co')
        UserProfile.objects.create(user=cls.user).branch_company.add(cls.branch)
        cls.vat_type = BaseVatType.objects.create(name='Vat 7%')
        cls.address = BaseAddress.objects.create(name_th='CP Items Address', address='1 Test Rd')
        BranchCompanyBaseAdress.objects.create(branch_company=cls.branch, address=cls.address)
        cls.credit = BaseCredit.objects.create(name='Cash')
        cls.unit = BaseUnit.objects.create(name='กล่องทดสอบ')
        cls.dist_sel = Distributor.objects.create(
            id='cpi_sel', name='ร้านที่เลือกทดสอบ', credit=cls.credit, vat_type=cls.vat_type)
        cls.dist_other = Distributor.objects.create(
            id='cpi_oth', name='ร้านอื่นทดสอบ', credit=cls.credit, vat_type=cls.vat_type)
        for i, name in ((1, 'รอดำเนินการ'), (2, 'อนุมัติ'), (3, 'ไม่อนุมัติ'), (4, 'ไม่ต้องอนุมัติ')):
            BaseApproveStatus.objects.get_or_create(id=i, defaults={'name': name})

    def setUp(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'CPI'
        session.save()

    def _make_cp(self, examiner, approver, n_items, prefix):
        cp = ComparisonPrice.objects.create(
            organizer=self.user, branch_company=self.branch, address_company=self.address,
            examiner_status_id=examiner, approver_status_id=approver, is_draft=False,
            select_bidder=self.dist_sel,
        )
        sel = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.dist_sel, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('100'), amount=Decimal('107'), is_select=True)
        other = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.dist_other, credit=self.credit, vat_type=self.vat_type,
            total_price=Decimal('200'), amount=Decimal('214'))
        for i in range(1, n_items + 1):
            ri = RequisitionItem.objects.create(requisition_id=0, product_name=f'{prefix}-สินค้า{i}', quantity=i)
            ComparisonPriceItem.objects.create(item=ri, quantity=Decimal(i), unit=self.unit, bidder=sel, cp=cp.id)
            # ร้านที่ไม่ได้เลือกเสนอชื่อเดียวกัน แต่ไม่ควรแสดงซ้ำ
            ComparisonPriceItem.objects.create(item=ri, quantity=Decimal(i), unit=self.unit, bidder=other, cp=cp.id)
        return cp

    def _assert_items_shown(self, response, prefix, n_items):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'รายการสินค้า</th>')
        for i in range(1, n_items + 1):
            # ร้านที่เลือกเท่านั้น: ชื่อสินค้าขึ้นครั้งเดียว
            self.assertContains(response, f'{prefix}-สินค้า{i}<', count=1)
        self.assertContains(response, 'กล่องทดสอบ')



class CPListItemListTestCase(ItemListFixture):
    """หน้ารายการใบเปรียบเทียบราคา (ประวัติสำเร็จ / ไม่สำเร็จ / อนุมัติ) แสดงรายการสินค้าของแต่ละใบ
    โชว์ 3 รายการแรก ที่เหลือเป็นปุ่ม "และอีก N รายการ" และดึงรายการสินค้าด้วย query เดียวทั้งหน้า"""

    def test_history_page_shows_items_with_more_button(self):
        self._make_cp(2, 2, 5, 'HIS')
        response = self.client.get(reverse('viewComparePricePOHistory'))
        self._assert_items_shown(response, 'HIS', 5)
        self.assertContains(response, 'และอีก 2 รายการ')
        # รายการที่ 4-5 ซ่อนไว้จนกดขยาย
        self.assertContains(response, 'dl-item dl-extra', count=2)

    def test_history_incomplete_page_shows_items(self):
        self._make_cp(3, 1, 2, 'INC')
        response = self.client.get(reverse('viewComparePricePOHistoryIncomplete'))
        self._assert_items_shown(response, 'INC', 2)
        self.assertNotContains(response, 'class="dl-more"')

    def test_approve_page_shows_items(self):
        self._make_cp(1, 1, 3, 'APV')
        response = self.client.get(reverse('viewCPApprove'))
        self._assert_items_shown(response, 'APV', 3)
        self.assertNotContains(response, 'class="dl-more"')

    def test_cp_without_items_shows_placeholder(self):
        self._make_cp(2, 2, 0, 'NON')
        response = self.client.get(reverse('viewComparePricePOHistory'))
        self.assertContains(response, 'ไม่มีรายการ')

    def test_items_loaded_in_one_query_for_whole_page(self):
        for n in range(3):
            self._make_cp(2, 2, 2, f'Q{n}')
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('viewComparePricePOHistory'))
        self.assertEqual(response.status_code, 200)
        # query ดึงรายการสินค้า (มีคอลัมน์ brand) ต้องมีครั้งเดียว ไม่ใช่ครั้งละใบ
        item_queries = [q['sql'] for q in ctx.captured_queries if '`ComparisonPriceItem`.`brand`' in q['sql']]
        self.assertEqual(len(item_queries), 1, item_queries)


class POReportItemListTestCase(ItemListFixture):
    """หน้ารายงานใบสั่งซื้อ (report/purchaseOrder/) แสดงรายการสินค้าของแต่ละใบเหมือนหน้ารายการใบเปรียบเทียบราคา"""

    def _make_po(self, n_items, prefix):
        po = PurchaseOrder.objects.create(
            stockman_user=self.user, branch_company=self.branch, address_company=self.address,
            distributor=self.dist_sel, vat_type=self.vat_type, credit=self.credit,
            approver_status_id=2, amount=Decimal('107'),
        )
        for i in range(1, n_items + 1):
            ri = RequisitionItem.objects.create(requisition_id=0, product_name=f'{prefix}-สินค้า{i}', quantity=i)
            PurchaseOrderItem.objects.create(po=po, item=ri, quantity=Decimal(i), unit=self.unit)
        return po

    def test_po_report_shows_items_with_more_button(self):
        self._make_po(4, 'POR')
        response = self.client.get(reverse('viewPOReport'))
        self._assert_items_shown(response, 'POR', 4)
        self.assertContains(response, 'และอีก 1 รายการ')

    def test_po_report_items_loaded_in_one_query(self):
        for n in range(3):
            self._make_po(2, f'PQ{n}')
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('viewPOReport'))
        self.assertEqual(response.status_code, 200)
        item_queries = [q['sql'] for q in ctx.captured_queries
                        if 'FROM `PurchaseOrderItem`' in q['sql'] and '`PurchaseOrderItem`.`unit_price`' in q['sql']]
        self.assertEqual(len(item_queries), 1, item_queries)
