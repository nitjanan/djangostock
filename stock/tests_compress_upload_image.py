import shutil
import tempfile
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from stock.image_utils import compress_image
from stock.models import (
    BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress, CarLogbook, Maintenance,
)

TEMP_MEDIA = tempfile.mkdtemp()


def make_upload(name="photo.png", size=(3000, 2000), fmt="PNG", mode="RGB", **save_kwargs):
    # รูป noise บีบอัดยาก ขนาดไฟล์จึงใหญ่เหมือนรูปถ่ายจริง
    img = Image.effect_noise(size, 64).convert(mode)
    buf = BytesIO()
    img.save(buf, format=fmt, **save_kwargs)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/" + fmt.lower())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CompressUploadImageTestCase(TestCase):
    """รูปที่อัพโหลดใน Maintenance / CarLogbook ต้องถูกย่อเป็น JPEG ไม่เกิน 1600px
    และต้องไม่ถูกบีบซ้ำเมื่อ save รอบถัดไป"""

    @classmethod
    def setUpTestData(cls):
        cls.ho = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=cls.ho, address=address)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def assert_compressed(self, field_file, original_size):
        self.assertTrue(field_file.name.endswith(".jpg"))
        self.assertLess(field_file.size, original_size)
        with Image.open(field_file.path) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertLessEqual(max(img.size), 1600)

    def test_maintenance_images_are_compressed(self):
        upload = make_upload()
        original_size = upload.size
        ma = Maintenance.objects.create(branch_company=self.ho, ref_no="MA-1", image1=upload)
        self.assert_compressed(ma.image1, original_size)
        self.assertFalse(ma.image2)

    def test_carlogbook_image_is_compressed(self):
        upload = make_upload()
        original_size = upload.size
        cl = CarLogbook.objects.create(branch_company=self.ho, ref_no="CL-1", image_mile=upload)
        self.assert_compressed(cl.image_mile, original_size)

    def test_resave_does_not_recompress(self):
        ma = Maintenance.objects.create(branch_company=self.ho, ref_no="MA-2", image1=make_upload())
        name, size = ma.image1.name, ma.image1.size
        ma.broke_reason = "แก้ไข"
        ma.save()
        ma.refresh_from_db()
        self.assertEqual(ma.image1.name, name)
        self.assertEqual(ma.image1.size, size)

    def test_rgba_image_is_converted(self):
        upload = make_upload(mode="RGBA")
        original_size = upload.size
        ma = Maintenance.objects.create(branch_company=self.ho, ref_no="MA-3", image1=upload)
        self.assert_compressed(ma.image1, original_size)

    def test_small_jpeg_is_kept_when_not_smaller(self):
        # JPEG คุณภาพต่ำอยู่แล้ว บีบซ้ำที่ quality 75 จะใหญ่ขึ้น จึงต้องเก็บไฟล์เดิมไว้
        upload = make_upload(name="tiny.jpg", size=(200, 200), fmt="JPEG", quality=10)
        self.assertIsNone(compress_image(upload))

    def test_non_image_returns_none(self):
        upload = SimpleUploadedFile("note.txt", b"not an image", content_type="text/plain")
        self.assertIsNone(compress_image(upload))
