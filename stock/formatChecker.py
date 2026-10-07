from django.db.models import FileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

DEFAULT_MAX_UPLOAD_SIZE = 5242880 #5MB
MAX_IMAGE_UPLOAD_SIZE = 15728640 #15MB รูปจากมือถือที่ยังไม่ย่อ (ย่อทีหลังใน save ด้วย image_utils)

#จำกัดขนาดรูปที่อัพโหลดใน ImageField เช็คเฉพาะไฟล์ที่เพิ่งอัพโหลด
def validate_image_upload_size(value):
    if value and not getattr(value, "_committed", True) and value.size > MAX_IMAGE_UPLOAD_SIZE:
        raise forms.ValidationError(_('ไม่สามารถอัพโหลดรูปภาพ เนื่องจากไฟล์มีขนาดใหญ่เกิน %s') % (filesizeformat(MAX_IMAGE_UPLOAD_SIZE)))

#เช็คไฟล์ที่อัพโหลด จำกัดนามสกุลไฟล์และจำกัดขนาดไฟล์
class ContentTypeRestrictedFileField(FileField):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload (default 5MB, None = no limit).
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 52428800
            100MB - 104857600
            250MB - 262144000
            500MB - 524288000
    """
    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types", [])
        self.max_upload_size = kwargs.pop("max_upload_size", DEFAULT_MAX_UPLOAD_SIZE)

        super(ContentTypeRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ContentTypeRestrictedFileField, self).clean(*args, **kwargs)

        file = data.file
        try:
            content_type = file.content_type
            if content_type in self.content_types:
                if self.max_upload_size is not None and file.size > self.max_upload_size:
                    raise forms.ValidationError(_('ไม่สามารถอัพโหลดไฟล์ เนื่องจากไฟล์มีขนาดใหญ่เกิน %s. กรุณาบีบอัดไฟล์ และอัพโหลดไฟล์อีกครั้ง') % (filesizeformat(self.max_upload_size)))
            else:
                raise forms.ValidationError(_('ไม่สามารถอัพโหลดชนิดไฟล์ '+ str(file.content_type)+ ' ได้'))
        except AttributeError:
            pass

        return data