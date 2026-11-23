from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from stock.models import BaseCar


class ApiExpBaseCarTestCase(TestCase):
    """API ทะเบียนรถที่ fleet-dashboard ดึงไป ต้องมีปีที่เริ่มใช้งาน / ยี่ห้อ / รุ่น"""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user("api", password="x"))

    def test_returns_start_year_brand_and_model(self):
        BaseCar.objects.create(
            code="S20", name="รถจีน9", start_year=2019, brand="SANY", car_model="SY215C"
        )
        BaseCar.objects.create(code="S21", name="รถจีน10")

        res = self.client.get(reverse("apiExpBaseCar"))

        self.assertEqual(res.status_code, 200)
        rows = {r["code"]: r for r in res.json()["results"]}
        self.assertEqual(rows["S20"]["start_year"], 2019)
        self.assertEqual(rows["S20"]["brand"], "SANY")
        self.assertEqual(rows["S20"]["car_model"], "SY215C")
        self.assertIsNone(rows["S21"]["start_year"])
        self.assertIsNone(rows["S21"]["brand"])
        self.assertIsNone(rows["S21"]["car_model"])
