import shutil
import tempfile
from io import BytesIO
from unittest import mock

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from stock.image_utils import compress_image, to_rgb
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

    def test_broken_exif_does_not_crash_save(self):
        # รูปมือถือบางรุ่นมี EXIF เสีย ทำให้ exif_transpose โยน TypeError จาก TiffImagePlugin.tobytes
        upload = make_upload()
        original_size = upload.size
        with mock.patch("stock.image_utils.ImageOps.exif_transpose",
                        side_effect=TypeError("object of type 'int' has no len()")):
            cl = CarLogbook.objects.create(branch_company=self.ho, ref_no="CL-2", image_mile=upload)
        self.assert_compressed(cl.image_mile, original_size)

    def test_unexpected_error_keeps_original_file(self):
        upload = make_upload()
        with mock.patch("stock.image_utils.Image.Image.save", side_effect=TypeError("boom")):
            self.assertIsNone(compress_image(upload))

    def test_truncated_upload_keeps_original_file(self):
        # เน็ตมือถือหลุดระหว่างอัพโหลด ไฟล์ขาดท้าย ต้องไม่ล้มและเก็บไฟล์เดิมไว้
        full = make_upload(name="cut.jpg", fmt="JPEG", quality=95)
        data = full.read()
        upload = SimpleUploadedFile("cut.jpg", data[: len(data) // 2], content_type="image/jpeg")
        with self.assertLogs("stock.image_utils", level="WARNING"):
            self.assertIsNone(compress_image(upload))
        self.assertEqual(upload.tell(), 0)

    def test_decompression_bomb_keeps_original_file(self):
        # รูปความละเอียดสูงมาก (เช่นกล้อง 200MP) Pillow จะโยน DecompressionBombError ตอนเปิดไฟล์
        upload = make_upload()
        with mock.patch("stock.image_utils.Image.open",
                        side_effect=Image.DecompressionBombError("too big")):
            self.assertIsNone(compress_image(upload))

    def test_transparent_png_gets_white_background(self):
        # ภาพหน้าจอ/สติกเกอร์ที่มีพื้นโปร่งใส ต้องได้พื้นขาว ไม่ใช่พื้นดำ
        palette = Image.new("P", (20, 20), 0)
        palette.info["transparency"] = 0  # แบบ GIF/PNG-8 โปร่งใส
        for img in (Image.new("RGBA", (20, 20), (0, 0, 0, 0)),
                    Image.new("LA", (20, 20), (0, 0)),
                    palette):
            self.assertEqual(to_rgb(img).getpixel((10, 10)), (255, 255, 255), img.mode)

    def test_16bit_png_is_converted(self):
        img = Image.effect_noise((2000, 2000), 64).convert("I")
        buf = BytesIO()
        img.save(buf, format="PNG")  # mode I บันทึกเป็น PNG 16 บิต
        upload = SimpleUploadedFile("deep.png", buf.getvalue(), content_type="image/png")
        result = compress_image(upload)
        self.assertIsNotNone(result)
        with Image.open(BytesIO(result.read())) as out:
            self.assertEqual(out.mode, "RGB")

    def test_large_jpeg_is_downscaled(self):
        upload = make_upload(name="big.jpg", size=(8000, 6000), fmt="JPEG", quality=95)
        result = compress_image(upload)
        with Image.open(BytesIO(result.read())) as out:
            self.assertEqual(max(out.size), 1600)

    def test_non_image_returns_none(self):
        upload = SimpleUploadedFile("note.txt", b"not an image", content_type="text/plain")
        self.assertIsNone(compress_image(upload))
