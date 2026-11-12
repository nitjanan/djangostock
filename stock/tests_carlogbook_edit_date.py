import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from stock.models import (
    UserProfile, BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress, CarLogbook,
    BaseCar, BaseJobCarDep, BaseCarDepartment, BaseOrigSta,
)


class CarLogbookEditDateTestCase(TestCase):
    """/carLogBook/edit/<id> ต้องแก้ไขวันที่ (created) ของบันทึกการใช้รถได้
    ส่วนแท็ป ALL ยังดูได้อย่างเดียว เปลี่ยนวันที่ไม่ได้"""

    OLD_DATE = datetime.date(2026, 9, 1)
    NEW_DATE = datetime.date(2026, 9, 15)

    @classmethod
    def setUpTestData(cls):
        cls.all_tab = BaseBranchCompany.objects.create(id="0", code="ALL", name="All")
        cls.ho = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.ho, address=address)

        cls.user = User.objects.create_user(username="cl_date", password="pw")
        profile = UserProfile.objects.create(user=cls.user)
        profile.branch_company.add(cls.all_tab, cls.ho)

        cls.car = BaseCar.objects.create(code="C1", name="Truck1")
        cls.job = BaseJobCarDep.objects.create(name="ขนหิน")

        cls.cl = CarLogbook.objects.create(
            branch_company=cls.ho, car=cls.car, name=cls.user, ref_no="CL-DATE-1",
            created=cls.OLD_DATE, mile_start=100, mile_end=150,
            job1_id=cls.job.id, job1=cls.job.name,
            start_job1=datetime.time(8, 0), end_job1=datetime.time(12, 0),
        )

    def _client(self, company_code):
        client = Client()
        client.force_login(self.user)
        session = client.session
        session["company_code"] = company_code
        session.save()
        return client

    def _post_data(self, created):
        return {
            "created": created,
            "name": self.user.id,
            "branch_company": self.ho.id,
            "car": self.car.id,
            "mile_start": "100",
            "mile_end": "150",
            "job1_id": self.job.id,
            "job1": self.job.id,
            "start_job1": "08:00",
            "end_job1": "12:00",
        }

    def test_edit_page_shows_editable_date_input(self):
        response = self._client("HO").get(reverse("editCL", args=[self.cl.id]))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('type="date"', html)
        self.assertIn('name="created"', html)
        self.assertIn('value="2026-09-01"', html)
        # ไม่ซ่อนช่องวันที่อีกต่อไป
        self.assertNotIn("d-none", html[html.index('name="created"') - 200:html.index('name="created"') + 200])

    def test_post_changed_date_is_saved(self):
        response = self._client("HO").post(
            reverse("editCL", args=[self.cl.id]), self._post_data("2026-09-15"))
        self.assertRedirects(response, reverse("viewCL"), fetch_redirect_response=False)
        self.cl.refresh_from_db()
        self.assertEqual(self.cl.created, self.NEW_DATE)
        # ข้อมูลอื่นยังเหมือนเดิม
        self.assertEqual(self.cl.ref_no, "CL-DATE-1")
        self.assertEqual(self.cl.mile_end, 150)
        self.assertEqual(self.cl.job1, self.job.name)

    def test_all_tab_cannot_change_date(self):
        response = self._client("ALL").post(
            reverse("editCL", args=[self.cl.id]), self._post_data("2026-09-15"))
        self.assertRedirects(response, reverse("viewCL"), fetch_redirect_response=False)
        self.cl.refresh_from_db()
        self.assertEqual(self.cl.created, self.OLD_DATE)


class RoiCarLogbookEditDateTestCase(TestCase):
    """/carLogBook/roi/edit/<id> (editCLRoi) ต้องแก้ไขวันที่ได้เหมือน editCL"""

    OLD_DATE = datetime.date(2026, 9, 1)
    NEW_DATE = datetime.date(2026, 9, 20)

    @classmethod
    def setUpTestData(cls):
        cls.all_tab = BaseBranchCompany.objects.create(id="0", code="ALL", name="All")
        cls.ho = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.ho, address=address)

        cls.user = User.objects.create_user(username="cl_roi_date", password="pw")
        profile = UserProfile.objects.create(user=cls.user)
        profile.branch_company.add(cls.all_tab, cls.ho)

        cls.car = BaseCar.objects.create(code="R1", name="RoiTruck")
        # RoiCarLogbookForm กรองสถานที่จัดส่งด้วย car_dep = 4
        car_dep = BaseCarDepartment.objects.create(id=4, name="ร้อยเกาะ")
        cls.job = BaseJobCarDep.objects.create(name="ส่งของร้อยเกาะ", car_dep=car_dep)
        cls.orig = BaseOrigSta.objects.create(name="ต้นทาง A")

        cls.cl = CarLogbook.objects.create(
            branch_company=cls.ho, car=cls.car, name=cls.user, ref_no="CL-ROI-DATE-1",
            created=cls.OLD_DATE, orig1=cls.orig, job1_id=cls.job.id, job1=cls.job.name,
            mile_start_job1=100, mile_end_job1=150,
        )

    def _client(self, company_code):
        client = Client()
        client.force_login(self.user)
        session = client.session
        session["company_code"] = company_code
        session.save()
        return client

    def _post_data(self, created):
        return {
            "created": created,
            "name": self.user.id,
            "branch_company": self.ho.id,
            "car": self.car.id,
            "mile_start": "100",
            "mile_end": "150",
            "orig1": self.orig.id,
            "mile_start_job1": "100",
            "mile_end_job1": "150",
            "job1_id": self.job.id,
            "job1": self.job.id,
        }

    def test_edit_page_shows_editable_date_input(self):
        response = self._client("HO").get(reverse("editCLRoi", args=[self.cl.id]))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('type="date"', html)
        self.assertIn('value="2026-09-01"', html)
        i = html.index('name="created"')
        self.assertNotIn("d-none", html[i - 200:i + 200])

    def test_post_changed_date_is_saved(self):
        response = self._client("HO").post(
            reverse("editCLRoi", args=[self.cl.id]), self._post_data("2026-09-20"))
        self.assertRedirects(response, reverse("viewCL"), fetch_redirect_response=False)
        self.cl.refresh_from_db()
        self.assertEqual(self.cl.created, self.NEW_DATE)
        self.assertEqual(self.cl.ref_no, "CL-ROI-DATE-1")
        self.assertEqual(self.cl.mile_end_job1, 150)

    def test_all_tab_cannot_change_date(self):
        response = self._client("ALL").post(
            reverse("editCLRoi", args=[self.cl.id]), self._post_data("2026-09-20"))
        self.assertRedirects(response, reverse("viewCL"), fetch_redirect_response=False)
        self.cl.refresh_from_db()
        self.assertEqual(self.cl.created, self.OLD_DATE)
