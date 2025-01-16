from django.db.models import FileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

#เช็คไฟล์ที่อัพโหลด จำกัดนามสกุลไฟล์และจำกัดขนาดไฟล์
class ContentTypeRestrictedFileField(FileField):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload.
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB - 104857600
            250MB - 214958080
            500MB - 429916160
    """
    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types", [])
        self.max_upload_size = kwargs.pop("max_upload_size", [])

        super(ContentTypeRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ContentTypeRestrictedFileField, self).clean(*args, **kwargs)

        file = data.file
        try:
            content_type = file.content_type
            if content_type in self.content_types:
                if file.size > self.max_upload_size:
                    raise forms.ValidationError(_('ไม่สามารถอัพโหลดไฟล์ เนื่องจากไฟล์มีขนาดใหญ่เกิน %s. กรุณาบีบอัดไฟล์ และอัพโหลดไฟล์อีกครั้ง') % (filesizeformat(self.max_upload_size)))
            else:
                raise forms.ValidationError(_('ไม่สามารถอัพโหลดชนิดไฟล์ '+ str(file.content_type)+ ' ได้'))
        except AttributeError:
            pass

        return data