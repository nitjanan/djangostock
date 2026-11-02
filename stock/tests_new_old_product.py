"""ปุ่ม New โอน รหัสสินค้า ในหน้าหลัก: เปลี่ยนรหัสสินค้า + ย้ายรายการในใบขอเบิกไปรหัสใหม่"""
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from stock.models import BaseVisible, Product, RequisitionItem, UserProfile
from stock.views import newOld

MEDIA_ROOT = tempfile.mkdtemp()  # ไฟล์ QR code ที่สร้างตอนเทสต์ ไม่ปนกับ media จริง


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class NewOldProductTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.product = Product.objects.create(id="nt-g0-151", name="น็อตทดสอบ", slug="ntIg0I151")
        self.item = RequisitionItem.objects.create(requisition_id=1, product=self.product, quantity=1)

    def login(self, user):
        # RequireCompanyCodeMiddleware logout ทุกคนที่ session ไม่มี company_code
        self.client.force_login(user)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    def ids(self):
        # เทียบแบบ binary: DB มอง "nt-g0-151" กับ "NT-G0-151" เป็นค่าเดียวกัน
        return sorted(Product.objects.values_list("id", flat=True))

    def test_lowercase_to_uppercase_same_code(self):
        alert_type, text = newOld("nt-g0-151", "NT-G0-151")
        self.assertIn("สำเร็จ", text)
        self.assertEqual(self.ids(), ["NT-G0-151"])
        product = Product.objects.get(id="NT-G0-151")
        self.assertEqual((product.name, product.slug), ("น็อตทดสอบ", "NTIG0I151"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.product_id, "NT-G0-151")
        # Windows ไม่สนตัวเล็ก/ใหญ่ของชื่อไฟล์ ถ้ามี qr_code_nt-g0-151.png อยู่แล้ว Django ต่อท้ายชื่อให้
        self.assertTrue(product.qr_code.name.startswith("pd_qr_codes/qr_code_NT-G0-151"), product.qr_code.name)

    def test_new_code_is_always_uppercased(self):
        _, text = newOld("nt-g0-151", " nt-g1-200 ")
        self.assertIn("เป็น 'NT-G1-200' สำเร็จ", text)
        self.assertEqual(self.ids(), ["NT-G1-200"])
        self.item.refresh_from_db()
        self.assertEqual(self.item.product_id, "NT-G1-200")

    def test_new_code_only_english_letters_digits_hyphen(self):
        for bad in ("NT-ก0-151", "NT G0 151", "NT_G0_151", "NT-G0-151/2", "ＮＴ-G0-151"):
            _, text = newOld("nt-g0-151", bad)
            self.assertIn("ใช้ได้เฉพาะตัวอักษรภาษาอังกฤษ A-Z ตัวเลข 0-9 และขีด -", text, bad)
        _, text = newOld("nt-g0-151", "   ")
        self.assertEqual(text, "กรุณากรอกรหัสสินค้าใหม่")
        self.assertEqual(self.ids(), ["nt-g0-151"])  # ไม่มีอะไรเปลี่ยน

    def test_xo_check_also_catches_lowercase(self):
        _, text = newOld("nt-g0-151", "nt-go-151")
        self.assertIn("XX-X0-001", text)
        self.assertEqual(self.ids(), ["nt-g0-151"])

    def test_already_uppercase_or_taken(self):
        Product.objects.create(id="AB-C0-001", name="อีกตัว", slug="ABIC0I001")
        _, text = newOld("nt-g0-151", "ab-c0-001")
        self.assertIn("มีรหัสสินค้าใหม่อยู่แล้ว 'AB-C0-001'", text)
        _, text = newOld("AB-C0-001", "AB-C0-001")
        self.assertIn("เป็นตัวพิมพ์ใหญ่อยู่แล้ว", text)
        # พิมพ์รหัสเก่าเป็นตัวเล็ก แต่ในระบบเก็บเป็นตัวใหญ่อยู่แล้ว (ระบบเดิมขึ้นว่า "มีรหัสสินค้าใหม่อยู่แล้ว")
        _, text = newOld("ab-c0-001", "AB-C0-001")
        self.assertEqual(text, "รหัสสินค้า 'AB-C0-001' เป็นตัวพิมพ์ใหญ่อยู่แล้ว ไม่ต้อง new โอน")
        _, text = newOld("XX-00-000", "XX-00-001")
        self.assertIn("ไม่มีรหัสสินค้าเก่าในระบบ", text)
        self.assertEqual(self.ids(), ["AB-C0-001", "nt-g0-151"])

    def test_post_requires_new_old_group(self):
        outsider = User.objects.create_user(username="outsider", password="password")
        self.login(outsider)
        response = self.client.post(reverse("home"), {"btnformNewOld": "", "old_product_id": "nt-g0-151", "new_product_id": "NT-G0-151"})
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertIn("ไม่มีสิทธิ์ new โอน รหัสสินค้า", " ".join(str(m) for m in get_messages(response.wsgi_request)))
        self.assertEqual(self.ids(), ["nt-g0-151"])

        member = User.objects.create_user(username="member", password="password")
        member.groups.add(Group.objects.get_or_create(name="NewOld")[0])
        self.login(member)
        self.client.post(reverse("home"), {"btnformNewOld": "", "old_product_id": "nt-g0-151", "new_product_id": "nt-g0-151"})
        self.assertEqual(self.ids(), ["NT-G0-151"])

    def test_other_transfer_buttons_also_check_group(self):
        outsider = User.objects.create_user(username="outsider", password="password")
        self.login(outsider)
        self.client.post(reverse("home"), {"btnformChangeExist": "", "ce_old_product_id": "nt-g0-151", "ce_new_product_id": "x"})
        response = self.client.post(reverse("home"), {"btnformNewOldDistributor": "", "old_distributor_id": "a", "new_distributor_id": "b"})
        text = " ".join(str(m) for m in get_messages(response.wsgi_request))
        self.assertIn("ไม่มีสิทธิ์ Change Exist", text)
        self.assertIn("ไม่มีสิทธิ์ new โอน รหัสผู้จัดจำหน่าย", text)
        self.assertEqual(self.ids(), ["nt-g0-151"])

    def test_modal_input_forces_uppercase_english(self):
        member = User.objects.create_user(username="member", password="password")
        # หน้ารายการสินค้า (ที่มีปุ่ม New โอน) แสดงเฉพาะคนที่มีแท็บ Category
        UserProfile.objects.create(user=member).visible.add(BaseVisible.objects.get_or_create(name="Category")[0])
        member.groups.add(Group.objects.get_or_create(name="NewOld")[0])
        self.login(member)
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'pattern="[A-Z0-9\\-]+"', html=False)
        self.assertContains(response, "this.value.toUpperCase().replace(/[^A-Z0-9-]/g, '')", html=False)
