import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from stock.meter_hours import entry_hours
from stock.models import (
    BaseAddress,
    BaseBranchCompany,
    BaseCar,
    BaseCarDepartment,
    BranchCompanyBaseAdress,
    CarLogbook,
)


class EntryHoursTestCase(SimpleTestCase):
    def test_hours_as_typed(self):
        self.assertEqual(entry_hours(Decimal("642"), Decimal("653")), 11)
        self.assertEqual(entry_hours(Decimal("100.5"), Decimal("100.5")), 0)

    def test_typed_without_decimal_point_is_tenths(self):
        self.assertEqual(entry_hours(Decimal("6532"), Decimal("6646")), Decimal("11.4"))
        self.assertEqual(entry_hours(Decimal("226337"), Decimal("226427")), 9)

    def test_wrong_entries_are_skipped(self):
        self.assertIsNone(entry_hours(Decimal("226337"), Decimal("22797")))  # ติดลบ
        self.assertIsNone(entry_hours(Decimal("100"), Decimal("400")))  # 300: หาร 10 ก็ยังเกิน 24
        self.assertIsNone(entry_hours(None, Decimal("10")))


class WorkByMonthMeterHoursTestCase(TestCase):
    def test_api_sums_hours_per_entry_and_keeps_sum_diff_mile(self):
        company = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=company, address=address)
        dep = BaseCarDepartment.objects.create(id=3, name="เครื่องจักรกลหนัก")
        car = BaseCar.objects.create(code="C21", name="VOLVO EC360", car_dep=dep)
        for day, start, end in (
            (1, "642", "653"),  # 11
            (2, "6532", "6646"),  # 11.4 (ไม่มีจุด)
            (3, "6646", "6757"),  # 11.1
            (4, "667", "100"),  # กรอกผิด ไม่นับ
        ):
            CarLogbook.objects.create(
                branch_company=company, car=car, created=datetime.date(2026, 2, day),
                mile_start=Decimal(start), mile_end=Decimal(end),
            )  # fmt: skip

        client = APIClient()
        client.force_authenticate(User.objects.create_user("api", password="pw"))
        url = reverse("getapiExpWorkByMonthAll", args=["2026-02-01", "2026-02-28"])
        (row,) = client.get(url).json()

        self.assertEqual(row["meter_hours"], 33.5)
        self.assertEqual(row["sum_diff_mile"], -542.0)  # เดิม: เลขท้าย(100) - เลขต้น(642)
        self.assertEqual(row["count_diff_time"], 4)
        self.assertEqual(row["car_dep"], 3)
