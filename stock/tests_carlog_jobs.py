import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from stock.carlog_jobs import collect_carlog_jobs
from stock.models import (
    BaseAddress,
    BaseBranchCompany,
    BaseCar,
    BaseExpenseDepartment,
    BranchCompanyBaseAdress,
    CarLogbook,
)

START, END = "2026-01-01", "2026-11-30"


class CollectCarlogJobsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.company, address=address)
        cls.car = BaseCar.objects.create(code="S20", name="รถจีน9")
        cls.crusher = BaseExpenseDepartment.objects.create(id="E01", name="โรงโม่ 2")

    def log(self, day, **jobs):
        return CarLogbook.objects.create(
            branch_company=self.company,
            car=self.car,
            created=datetime.date(2026, 11, day),
            **jobs,
        )

    def test_sums_hours_km_and_trips_per_job_and_expense_department(self):
        common = dict(job1="หินใหญ่-เข้าโม่", exd_job1=self.crusher)
        self.log(
            18, **common,
            start_job1=datetime.time(7, 0), end_job1=datetime.time(20, 30),
            mile_start_job1=Decimal("72954"), mile_end_job1=Decimal("72980"),
        )  # fmt: skip
        self.log(
            19, **common,
            start_job1=datetime.time(8, 0), end_job1=datetime.time(10, 0),
            mile_start_job1=Decimal("72980"), mile_end_job1=Decimal("73000"),
            job2="วางบิล", mile_start_job2=Decimal("73000"), mile_end_job2=Decimal("73010"),
        )  # fmt: skip

        rows = {(r["expense_dept_id"], r["job"]): r for r in collect_carlog_jobs(START, END)}

        crusher = rows[("E01", "หินใหญ่-เข้าโม่")]
        self.assertEqual(crusher["hours"], 15.5)
        self.assertEqual(crusher["km"], 46)
        self.assertEqual((crusher["trips"], crusher["days"]), (2, 2))
        self.assertEqual(crusher["expense_dept_name"], "โรงโม่ 2")
        self.assertEqual((crusher["year"], crusher["month"]), (2026, 11))

        # งานที่ไม่มีเวลา/แผนกค่าใช้จ่าย ยังนับระยะทางและเที่ยว
        bill = rows[(None, "วางบิล")]
        self.assertEqual((bill["hours"], bill["km"], bill["trips"]), (0, 10, 1))

    def test_skips_cancelled_and_empty_jobs(self):
        cancelled = self.log(18, job1="ยกเลิก", start_job1=datetime.time(7), end_job1=datetime.time(9))
        cancelled.is_cancel = True
        cancelled.save()
        self.log(19)  # ไม่ได้กรอกงาน

        self.assertEqual(collect_carlog_jobs(START, END), [])


class CarlogJobsApiTestCase(TestCase):
    def test_requires_login_and_returns_list(self):
        url = reverse("getapiCarlogJobsAll", args=[START, END])
        client = APIClient()
        self.assertIn(client.get(url).status_code, (401, 403))

        client.force_authenticate(User.objects.create_user("api", password="pw"))
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
