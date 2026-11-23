"""หารถของใบจ่ายใน Express: เลขใบแจ้งซ่อมใน note3 ก่อน แล้วค่อย remark (stock/exp_car.py)"""
import datetime
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from stock.car_match import build_car_maps
from stock.exp_car import maintenance_cars, resolve_exp_car
from stock.models import (
    BaseAddress,
    BaseBranchCompany,
    BaseCar,
    BranchCompanyBaseAdress,
    Maintenance,
)
from stock.unmatched_cars import collect_unmatched


def exp_row(remark, note3, amount, note2="01", month="10"):
    """แถวจาก query_exp_repair_all"""
    return {
        "year": "2026", "month": month, "car_code": remark, "note3": note3,
        "note2": note2, "sum_amount": amount,
    }


class ExpCarTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.branch, address=address)
        cls.car_a = BaseCar.objects.create(id="1", name="ภบ-2100", code="T1")
        cls.car_b = BaseCar.objects.create(id="2", name="ผข-8465", code="T2")

        def ma(ref_no, car, **kwargs):
            return Maintenance.objects.create(
                branch_company=cls.branch, car=car, created=datetime.datetime(2026, 10, 1, 8),
                ref_no=ref_no, **kwargs,
            )

        ma("MR16910001", cls.car_a)
        ma("MR16910002", None)  # ใบแจ้งซ่อมยังไม่ระบุรถ
        ma("MR16910003", cls.car_a, is_cancel=True)
        cls.maps = build_car_maps(BaseCar.objects.values("id", "name", "code", "car_dep"))
        cls.user = User.objects.create_user(username="dashboard_api", password="pw")

    def resolve(self, remark, note3):
        ma_cars = maintenance_cars([note3])
        car = resolve_exp_car(remark, note3, ma_cars, *self.maps)
        return car and str(car["id"])

    def test_note3_wins_over_wrong_remark(self):
        # remark คีย์เป็นทะเบียนคันอื่น แต่ note3 ชี้ใบแจ้งซ่อมของคัน A
        self.assertEqual(self.resolve("ผข-8465", "MR16910001"), "1")
        # remark ผิดจนจับคู่ไม่ได้ ก็ยังลงคัน A
        self.assertEqual(self.resolve("พิมพ์ผิด", " mr16910001 "), "1")

    def test_falls_back_to_remark(self):
        self.assertEqual(self.resolve("ผข8465", None), "2")  # ไม่มี note3
        self.assertEqual(self.resolve("ผข8465", "MR19999999"), "2")  # หาใบแจ้งซ่อมไม่เจอ
        self.assertEqual(self.resolve("ผข8465", "MR16910002"), "2")  # ใบแจ้งซ่อมไม่มีรถ
        self.assertEqual(self.resolve("ผข8465", "MR16910003"), "2")  # ใบแจ้งซ่อมถูกยกเลิก

    def test_unmatched_when_neither_matches(self):
        self.assertIsNone(self.resolve("พิมพ์ผิด", "MR19999999"))

    def _rows(self):
        return [
            exp_row("ภบ2100", None, "100"),
            exp_row("ผข-8465", "MR16910001", "50"),  # remark ผิด -> ลงคัน A รวมกับแถวบน
            exp_row("ผิด", "MR16910001", "25"),
            exp_row("ผิดทั้งคู่", None, "7"),
        ]

    def test_repair_api_merges_rows_per_car(self):
        client = APIClient()
        client.force_authenticate(self.user)
        url = reverse("getapiExpRepairAll", args=["2026-01-01", "2026-12-31"])
        with mock.patch("stock.views.query_exp_repair_all", return_value=self._rows()):
            rows = client.get(url).json()
        self.assertEqual([(str(r["car_id"]), r["amount"]) for r in rows], [("1", 175.0)])

    def test_unmatched_uses_same_rule(self):
        with mock.patch("stock.views.query_exp_repair_all", return_value=self._rows()), \
                mock.patch("stock.views.query_exp_oil_by_month_all", return_value=[]):
            rows = collect_unmatched("2026-01-01", "2026-12-31")
        self.assertEqual([(r["remark"], r["repair_amount"]) for r in rows], [("ผิดทั้งคู่", 7.0)])
