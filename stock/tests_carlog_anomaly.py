import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from stock.carlog_anomaly import detect_carlog_anomalies
from stock.models import (
    UserProfile, BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress, CarLogbook,
    BaseCar,
)


def t(hhmm):
    h, m = hhmm.split(":")
    return datetime.time(int(h), int(m))


class CarLogAnomalyTestCase(TestCase):
    """ตรวจจับการคีย์บันทึกการใช้รถที่ผิดปกติ (ไมล์ในใบ, ไมล์ต่อจากใบก่อนหน้า, เวลางาน)"""

    @classmethod
    def setUpTestData(cls):
        cls.ho = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.ho, address=address)
        cls.car = BaseCar.objects.create(code="C1", name="Truck1")
        cls.car2 = BaseCar.objects.create(code="C2", name="Truck2")

    def _cl(self, day=1, car=None, **kwargs):
        return CarLogbook.objects.create(
            branch_company=self.ho,
            car=car or self.car,
            created=datetime.date(2026, 9, day),
            **kwargs,
        )

    def _issues(self, cl):
        result = detect_carlog_anomalies(CarLogbook.objects.filter(id=cl.id))
        return [i["text"] for i in result[0]["issues"]] if result else []

    # ---------- ไมล์ผิดในใบเดียว ----------
    def test_normal_record_has_no_issue(self):
        cl = self._cl(mile_start=100, mile_end=200,
                      mile_start_job1=100, mile_end_job1=150,
                      mile_start_job2=150, mile_end_job2=200,
                      start_job1=t("08:00"), end_job1=t("10:00"),
                      start_job2=t("10:30"), end_job2=t("12:00"))
        self.assertEqual(self._issues(cl), [])

    def test_mile_end_less_than_start(self):
        cl = self._cl(mile_start=200, mile_end=100)
        self.assertTrue(any("ไมล์สิ้นสุด" in i for i in self._issues(cl)))

    def test_daily_distance_over_limit(self):
        cl = self._cl(mile_start=100, mile_end=701)
        self.assertTrue(any("500" in i for i in self._issues(cl)))

    def test_daily_distance_at_limit_ok(self):
        cl = self._cl(mile_start=100, mile_end=600)
        self.assertEqual(self._issues(cl), [])

    def test_job_mile_backwards(self):
        cl = self._cl(mile_start=100, mile_end=200, mile_start_job3=180, mile_end_job3=170)
        self.assertTrue(any("งานที่ 3" in i for i in self._issues(cl)))

    def test_jobs_mile_not_continuous(self):
        cl = self._cl(mile_start=100, mile_end=200,
                      mile_start_job1=100, mile_end_job1=160,
                      mile_start_job2=150, mile_end_job2=200)
        self.assertTrue(any("งานที่ 2" in i for i in self._issues(cl)))

    # ---------- ไมล์ไม่ต่อกับใบก่อนหน้า ----------
    def test_mile_backwards_from_previous_record(self):
        self._cl(day=1, mile_start=100, mile_end=200)
        cl = self._cl(day=2, mile_start=190, mile_end=250)
        self.assertTrue(any("ใบก่อนหน้า" in i for i in self._issues(cl)))

    def test_previous_issue_identifies_previous_record(self):
        self._cl(day=1, mile_start=100, mile_end=150, ref_no="CL-OLDER")
        prev = self._cl(day=2, mile_start=150, mile_end=200, ref_no="CL-PREV")
        cl = self._cl(day=3, mile_start=300, mile_end=350)
        result = detect_carlog_anomalies(CarLogbook.objects.filter(id=cl.id))
        prev_issues = [i for i in result[0]["issues"] if i["prev"]]
        self.assertEqual(len(prev_issues), 1)
        self.assertEqual(prev_issues[0]["prev"].id, prev.id)
        self.assertEqual(prev_issues[0]["prev"].ref_no, "CL-PREV")

    def test_mile_jump_from_previous_record(self):
        self._cl(day=1, mile_start=100, mile_end=200)
        cl = self._cl(day=2, mile_start=251, mile_end=300)
        self.assertTrue(any("ใบก่อนหน้า" in i for i in self._issues(cl)))

    def test_mile_small_gap_from_previous_ok(self):
        self._cl(day=1, mile_start=100, mile_end=200)
        cl = self._cl(day=2, mile_start=250, mile_end=300)
        self.assertEqual(self._issues(cl), [])

    def test_previous_record_is_same_car_only(self):
        self._cl(day=1, car=self.car2, mile_start=1000, mile_end=2000)
        cl = self._cl(day=2, mile_start=100, mile_end=200)
        self.assertEqual(self._issues(cl), [])

    def test_previous_cancelled_record_ignored(self):
        self._cl(day=1, mile_start=100, mile_end=200)
        self._cl(day=2, mile_start=900, mile_end=999, is_cancel=True)
        cl = self._cl(day=3, mile_start=200, mile_end=300)
        self.assertEqual(self._issues(cl), [])

    def test_previous_record_limited_to_visible_companies(self):
        other = BaseBranchCompany.objects.create(id="2", code="OT", name="Other")
        address = BaseAddress.objects.create(name_th="Other Co", address="2 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=other, address=address)
        hidden = CarLogbook.objects.create(branch_company=other, car=self.car,
                                           created=datetime.date(2026, 9, 1), mile_start=100, mile_end=900)
        cl = self._cl(day=2, mile_start=100, mile_end=200)
        visible = CarLogbook.objects.filter(branch_company=self.ho)
        result = detect_carlog_anomalies(CarLogbook.objects.filter(id=cl.id), visible)
        self.assertEqual(result, [])
        # ถ้าไม่จำกัด จะเจอใบของบริษัทอื่น
        entry = detect_carlog_anomalies(CarLogbook.objects.filter(id=cl.id))[0]
        self.assertEqual(entry["prev"].id, hidden.id)

    def test_previous_record_same_day_uses_id_order(self):
        self._cl(day=1, mile_start=100, mile_end=200)
        cl = self._cl(day=1, mile_start=200, mile_end=300)
        self.assertEqual(self._issues(cl), [])

    # ---------- เวลางานผิด ----------
    def test_overnight_job_is_ok(self):
        cl = self._cl(start_job1=t("22:00"), end_job1=t("02:00"))
        self.assertEqual(self._issues(cl), [])

    def test_job_too_long(self):
        # 10:00 -> 08:00 ถูกนับเป็นข้ามวัน = 22 ชม. น่าจะคีย์ผิด
        cl = self._cl(start_job2=t("10:00"), end_job2=t("08:00"))
        self.assertTrue(any("งานที่ 2" in i for i in self._issues(cl)))

    def test_job_times_overlap(self):
        cl = self._cl(start_job1=t("08:00"), end_job1=t("11:00"),
                      start_job2=t("10:00"), end_job2=t("12:00"))
        self.assertTrue(any("ซ้อนทับ" in i for i in self._issues(cl)))

    # ---------- ข้อมูลสำหรับ chain-panel ----------
    def _entry(self, cl):
        return detect_carlog_anomalies(CarLogbook.objects.filter(id=cl.id))[0]

    def test_bad_fields_for_mile_in_record(self):
        cl = self._cl(mile_start=200, mile_end=100)
        self.assertEqual(self._entry(cl)["bad_fields"], {"mile_start", "mile_end"})

    def test_bad_fields_for_previous_record(self):
        prev = self._cl(day=1, mile_start=100, mile_end=200)
        cl = self._cl(day=2, mile_start=300, mile_end=350)
        entry = self._entry(cl)
        self.assertEqual(entry["prev"].id, prev.id)
        self.assertEqual(entry["bad_fields"], {"mile_start"})
        self.assertEqual(entry["prev_bad_fields"], {"mile_end"})

    def test_job_rows_mark_bad_jobs(self):
        cl = self._cl(mile_start_job1=100, mile_end_job1=160,
                      mile_start_job2=150, mile_end_job2=200,
                      start_job1=t("08:00"), end_job1=t("11:00"),
                      start_job2=t("10:00"), end_job2=t("12:00"))
        jobs = self._entry(cl)["jobs"]
        self.assertEqual([j["n"] for j in jobs], [1, 2])
        self.assertTrue(jobs[0]["bad_mile_end"])
        self.assertTrue(jobs[1]["bad_mile_start"])
        self.assertTrue(jobs[0]["bad_time"] and jobs[1]["bad_time"])
        self.assertFalse(jobs[0]["bad_mile_start"])

    def test_prev_shown_even_without_prev_issue(self):
        prev = self._cl(day=1, mile_start=100, mile_end=200)
        cl = self._cl(day=2, mile_start=200, mile_end=100)
        entry = self._entry(cl)
        self.assertEqual(entry["prev"].id, prev.id)
        self.assertEqual(entry["prev_bad_fields"], set())

    def test_clean_records_not_returned(self):
        cl = self._cl(mile_start=100, mile_end=200)
        self.assertEqual(detect_carlog_anomalies(CarLogbook.objects.filter(id=cl.id)), [])


class CarLogAnomalyPanelTestCase(TestCase):
    """หน้า /carLogBook/ ต้องแสดงแผงรายการที่อาจคีย์ผิดปกติ"""

    @classmethod
    def setUpTestData(cls):
        cls.all_tab = BaseBranchCompany.objects.create(id="0", code="ALL", name="All")
        cls.ho = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.ho, address=address)
        cls.user = User.objects.create_user(username="cl_anomaly", password="pw")
        profile = UserProfile.objects.create(user=cls.user)
        profile.branch_company.add(cls.all_tab, cls.ho)
        car = BaseCar.objects.create(code="C1", name="Truck1")
        today = datetime.date.today()
        cls.bad = CarLogbook.objects.create(branch_company=cls.ho, car=car, created=today,
                                            ref_no="CL-BAD", mile_start=200, mile_end=100)
        cls.old_bad = CarLogbook.objects.create(branch_company=cls.ho, car=car,
                                                created=today - datetime.timedelta(days=60),
                                                ref_no="CL-OLD", mile_start=200, mile_end=100)

    def _get(self, params=None, company_code="HO"):
        client = Client()
        client.login(username="cl_anomaly", password="pw")
        session = client.session
        session["company_code"] = company_code
        session.save()
        return client.get(reverse("viewCL"), params or {})

    def test_all_tab_panel_links_to_records(self):
        # แท็ป ALL กดรหัสเข้าไปดูได้ (หน้า edit เป็นแบบดูอย่างเดียว)
        response = self._get(company_code="ALL")
        self.assertEqual(response.status_code, 200)
        # ตรวจเฉพาะ html ของแผงผิดปกติ (ตารางหลักก็มีลิงก์เหมือนกัน)
        html = response.content.decode()
        panel = html[html.index('id="anomaly-panel"'):html.index('<div class="card div-shadow">')]
        self.assertIn(f'href="{reverse("editCL", args=[self.bad.id])}"', panel)
        self.assertIn(f'href="{reverse("editCL", args=[self.old_bad.id])}"', panel)

    def test_panel_shows_recent_anomalies_by_default(self):
        response = self._get()
        self.assertEqual(response.status_code, 200)
        ids = {a["cl"].id for a in response.context["anomalies"]}
        self.assertEqual(ids, {self.bad.id})
        self.assertContains(response, "รายการที่อาจคีย์ผิดปกติ")
        # CL-BAD ไมล์ไม่ต่อจาก CL-OLD ต้องมีลิงก์ไปใบก่อนหน้า
        self.assertContains(response, reverse("editCL", args=[self.old_bad.id]))
        # chain-panel ใบก่อนหน้า -> ใบนี้
        self.assertContains(response, "chain-toggle")
        self.assertContains(response, "chain-panel--prev")
        self.assertContains(response, "chain-panel--cur")
        self.assertContains(response, "chain-bad")
        # comment ใน template ต้องไม่หลุดมาแสดงบนหน้า
        self.assertNotContains(response, "{#")

    def test_panel_follows_date_filter(self):
        old = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        response = self._get({"start_created": old})
        ids = {a["cl"].id for a in response.context["anomalies"]}
        self.assertEqual(ids, {self.bad.id, self.old_bad.id})
