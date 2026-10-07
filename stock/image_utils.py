import os
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.files.base import ContentFile

#ย่อรูปและบีบอัดเป็น JPEG ถ้าบีบแล้วไม่เล็กลงหรือไม่ใช่รูป จะคืนค่า None
def compress_image(field_file, max_size=(1600, 1600), quality=75):
    try:
        field_file.seek(0)
        img = Image.open(field_file)
        img = ImageOps.exif_transpose(img)  # แก้รูปตะแคงจากมือถือ และตัด EXIF ทิ้ง
    except (UnidentifiedImageError, OSError, ValueError):
        return None

    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail(max_size, Image.Resampling.LANCZOS)  # ย่อด้านยาวสุดไม่เกิน max_size

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    if buf.tell() >= field_file.size:
        field_file.seek(0)
        return None

    name = os.path.splitext(os.path.basename(field_file.name))[0] + ".jpg"
    return ContentFile(buf.getvalue(), name=name)

#บีบอัดรูปเฉพาะที่เพิ่งอัพโหลด (ยังไม่ได้บันทึกลง storage) เพื่อไม่ให้บีบซ้ำทุกครั้งที่ save
def compress_uploaded_images(instance, field_names, **kwargs):
    for field_name in field_names:
        f = getattr(instance, field_name)
        if f and not f._committed:
            compressed = compress_image(f, **kwargs)
            if compressed is not None:
                setattr(instance, field_name, compressed)
