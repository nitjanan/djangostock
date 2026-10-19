from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import FieldFile
from django.test import SimpleTestCase

from stock.formatChecker import (
    ContentTypeRestrictedFileField, DEFAULT_MAX_UPLOAD_SIZE, MAX_IMAGE_UPLOAD_SIZE,
    validate_image_upload_size,
)


def make_value(field, size, content_type="application/pdf"):
    value = FieldFile(None, field, "doc.pdf")
    value.file = SimpleUploadedFile("doc.pdf", b"x" * size, content_type=content_type)
    return value


class ContentTypeRestrictedFileFieldTestCase(SimpleTestCase):
    """ตรวจชนิดไฟล์และขนาดไฟล์ ถ้าไม่ได้กำหนด max_upload_size ต้องใช้ค่า default 5MB (เดิม TypeError)"""

    def test_without_max_upload_size_uses_default_limit(self):
        field = ContentTypeRestrictedFileField(upload_to="x", content_types=["application/pdf"])
        value = make_value(field, DEFAULT_MAX_UPLOAD_SIZE)
        self.assertIs(field.clean(value, None), value)
        with self.assertRaises(ValidationError):
            field.clean(make_value(field, DEFAULT_MAX_UPLOAD_SIZE + 1), None)

    def test_max_upload_size_none_accepts_any_size(self):
        field = ContentTypeRestrictedFileField(
            upload_to="x", content_types=["application/pdf"], max_upload_size=None)
        value = make_value(field, DEFAULT_MAX_UPLOAD_SIZE + 1)
        self.assertIs(field.clean(value, None), value)

    def test_file_over_limit_is_rejected(self):
        field = ContentTypeRestrictedFileField(
            upload_to="x", content_types=["application/pdf"], max_upload_size=100)
        with self.assertRaises(ValidationError):
            field.clean(make_value(field, 101), None)

    def test_file_within_limit_is_accepted(self):
        field = ContentTypeRestrictedFileField(
            upload_to="x", content_types=["application/pdf"], max_upload_size=100)
        value = make_value(field, 100)
        self.assertIs(field.clean(value, None), value)

    def test_disallowed_content_type_is_rejected(self):
        field = ContentTypeRestrictedFileField(
            upload_to="x", content_types=["application/pdf"], max_upload_size=100)
        with self.assertRaises(ValidationError):
            field.clean(make_value(field, 10, content_type="application/zip"), None)


class ValidateImageUploadSizeTestCase(SimpleTestCase):
    """รูปที่เพิ่งอัพโหลดต้องไม่เกิน 15MB ส่วนรูปที่บันทึกไว้แล้วไม่ต้องเช็ค"""

    def make_image_value(self, size, committed=False):
        field = ContentTypeRestrictedFileField(upload_to="x")
        value = make_value(field, size, content_type="image/jpeg")
        value._committed = committed
        return value

    def test_image_within_limit_passes(self):
        validate_image_upload_size(self.make_image_value(MAX_IMAGE_UPLOAD_SIZE))

    def test_image_over_limit_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_image_upload_size(self.make_image_value(MAX_IMAGE_UPLOAD_SIZE + 1))

    def test_committed_image_is_not_checked(self):
        validate_image_upload_size(self.make_image_value(MAX_IMAGE_UPLOAD_SIZE + 1, committed=True))
