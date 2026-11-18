"""หน้า admin "รายการที่ยังไม่ได้ตั้งค่ารถ" ของ BaseCar (stock/unmatched_cars.py)"""
from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import BaseBranchCompany, BaseCar
from .unmatched_cars import suggest_car, summarize_by_remark


class SuggestCarTestCase(SimpleTestCase):

    def test_split_name_and_code(self):
        self.assertEqual(suggest_car('โรงโม่1:TM1'), ('โรงโม่1', 'TM1'))
        self.assertEqual(suggest_car('SY375H(J2)'), ('SY375H', 'J2'))
        self.assertEqual(suggest_car('โรงโม่5:SM5 Terex fix 5'), ('โรงโม่5', 'SM5'))

    def test_no_code(self):
        self.assertEqual(suggest_car('ZX210LC'), ('ZX210LC', ''))
        # วงเล็บที่เป็นคำอธิบาย ไม่ใช่รหัส
        self.assertEqual(suggest_car('82-1250(รถน้ำ)'), ('82-1250', ''))
        self.assertEqual(suggest_car('งานซ่อมปากจอ\xa0โรงโม่'), ('งานซ่อมปากจอ โรงโม่', ''))


class SummarizeTestCase(SimpleTestCase):

    def test_groups_months_per_company_and_remark(self):
        rows = [
            {'branch_company': '01', 'year': '2026', 'month': '01', 'remark': 'ปุ๋ย', 'repair_amount': 300.0, 'oil_qty': 0.0},
            {'branch_company': '01', 'year': '2026', 'month': '02', 'remark': 'ปุ๋ย', 'repair_amount': 200.0, 'oil_qty': 0.0},
            {'branch_company': '02', 'year': '2026', 'month': '01', 'remark': 'ปุ๋ย', 'repair_amount': 50.0, 'oil_qty': 0.0},
            {'branch_company': '02', 'year': '2026', 'month': '01', 'remark': 'ZX210LC', 'repair_amount': 700.0, 'oil_qty': 40.0},
        ]
        result = summarize_by_remark(rows)
        self.assertEqual(
            [(r['branch_company'], r['remark'], r['repair_amount'], r['month_count']) for r in result],
            [('02', 'ZX210LC', 700.0, 1), ('01', 'ปุ๋ย', 500.0, 2), ('02', 'ปุ๋ย', 50.0, 1)],
        )


class UnmatchedAdminViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pass-1234')
        BaseBranchCompany.objects.create(id='01', code='C1', name='บริษัทหนึ่ง')
        BaseCar.objects.create(code='X1', name='ตาชั่ง')  # ไม่มีแผนก

    def setUp(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session['company_code'] = 'ALL'
        session.save()

    def test_lists_unmatched_remarks_with_add_link(self):
        rows = [{'branch_company': '01', 'year': '2026', 'month': '01',
                 'remark': 'SY375H(J2)', 'repair_amount': 1234.5, 'oil_qty': 0.0}]
        with mock.patch('stock.unmatched_cars.collect_unmatched', return_value=rows) as collect:
            res = self.client.get(reverse('admin:stock_basecar_unmatched'), {'year': 2026})

        self.assertEqual(res.status_code, 200)
        collect.assert_called_once_with('2026-01-01', '2026-12-31')
        self.assertContains(res, 'SY375H(J2)')
        self.assertContains(res, 'บริษัทหนึ่ง')
        self.assertContains(res, '1,234.50')
        self.assertContains(res, '?name=SY375H&amp;code=J2')
        self.assertContains(res, '1 คันที่ยังไม่ได้ตั้งแผนก')

    def test_shows_error_when_express_unavailable(self):
        with mock.patch('stock.unmatched_cars.collect_unmatched', side_effect=RuntimeError('no pg')):
            res = self.client.get(reverse('admin:stock_basecar_unmatched'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'ดึงข้อมูลจากโปรแกรมบัญชี Express ไม่ได้: no pg')

    def test_changelist_has_button(self):
        res = self.client.get(reverse('admin:stock_basecar_changelist'))
        self.assertContains(res, reverse('admin:stock_basecar_unmatched'))
