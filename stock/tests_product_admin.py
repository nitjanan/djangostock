"""หน้า admin สินค้า (/admin/stock/product/): ช่องรหัสสินค้าพิมพ์ได้แค่ภาษาอังกฤษตัวพิมพ์ใหญ่"""
import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from stock.models import BaseUnit, Product

MEDIA_ROOT = tempfile.mkdtemp()  # ไฟล์ QR code ที่สร้างตอนเทสต์ ไม่ปนกับ media จริง

ID_INPUT_ATTRS = (
    'pattern="[A-Z0-9\\-]+"',
    "oninput=\"this.value = this.value.toUpperCase().replace(/[^A-Z0-9-]/g, &#x27;&#x27;)\"",
)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ProductAdminIdInputTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        admin = User.objects.create_superuser(username="admin", password="password")
        # RequireCompanyCodeMiddleware logout ทุกคนที่ session ไม่มี company_code
        self.client.force_login(admin)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    def test_add_and_change_pages_force_uppercase_english(self):
        Product.objects.create(id="EL-G0-999", name="สายไฟทดสอบ", slug="ELIG0I999", unit=self.unit)
        for url in (reverse("admin:stock_product_add"), reverse("admin:stock_product_change", args=["EL-G0-999"])):
            response = self.client.get(url)
            for attr in ID_INPUT_ATTRS:
                self.assertContains(response, attr, count=1, html=False, msg_prefix=url)

    def test_server_still_rejects_lowercase_or_thai(self):
        for bad in ("el-g0-998", "EL-ก0-998"):
            response = self.client.post(reverse("admin:stock_product_add"), {
                "id": bad, "name": "สินค้า " + bad, "unit": self.unit.pk, "slug": "test-slug",
            })
            self.assertEqual(response.status_code, 200, bad)  # กลับมาหน้าฟอร์มพร้อม error ไม่ได้บันทึก
            self.assertContains(response, "รหัสสินค้าผิด", msg_prefix=bad)
        self.assertFalse(Product.objects.filter(name__startswith="สินค้า ").exists())

        response = self.client.post(reverse("admin:stock_product_add"), {
            "id": "EL-G0-998", "name": "สินค้าใหม่", "unit": self.unit.pk, "slug": "ELIG0I998",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(id="EL-G0-998").exists())
