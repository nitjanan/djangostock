import logging
import os
from io import BytesIO

from PIL import Image, ImageOps
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

#แปลงรูปทุกโหมดเป็น RGB สำหรับบันทึก JPEG พื้นโปร่งใสให้เป็นสีขาว (ถ้า convert ตรงๆ จะกลายเป็นพื้นดำ)
def to_rgb(img):
    if img.mode == "RGB":
        return img
    if img.mode == "P" and "transparency" in img.info:
        img = img.convert("RGBA")
    if img.mode in ("RGBA", "LA", "PA", "RGBa", "La"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        return bg
    if img.mode.startswith("I;16"):
        img = img.convert("I")
    if img.mode == "I":
        img = img.point(lambda v: v * (1 / 256)).convert("L")  # PNG 16 บิต ลดเหลือ 8 บิต
    return img.convert("RGB")

#ย่อรูปและบีบอัดเป็น JPEG ถ้าบีบแล้วไม่เล็กลง ไม่ใช่รูป หรือบีบไม่สำเร็จ จะคืนค่า None (ให้เก็บไฟล์เดิมไว้)
#ห้ามโยน exception ออกไป เพราะจะทำให้การบันทึกเอกสารทั้งใบล้ม
def compress_image(field_file, max_size=(1600, 1600), quality=75):
    name = getattr(field_file, "name", "")
    try:
        field_file.seek(0)
        img = Image.open(field_file)
        # JPEG ให้ถอดรหัสที่ความละเอียดต่ำตั้งแต่แรก ประหยัด RAM กับรูปกล้อง 50MP+
        img.draft("RGB", max_size)
    except Image.DecompressionBombError:
        logger.warning("compress_image: รูปความละเอียดสูงเกินไป ข้ามการบีบอัด %s", name)
        field_file.seek(0)
        return None
    except Exception:
        # ไม่ใช่รูป หรือรูปแบบที่ Pillow ไม่รองรับ (เช่น HEIC) เก็บไฟล์เดิม
        field_file.seek(0)
        return None

    try:
        img = ImageOps.exif_transpose(img)  # แก้รูปตะแคงจากมือถือ และตัด EXIF ทิ้ง
    except Exception:
        # EXIF เสีย (เช่น TypeError จาก TiffImagePlugin.tobytes) ข้ามการหมุนรูปไป
        logger.warning("compress_image: EXIF เสีย ข้ามการหมุนรูป %s", name, exc_info=True)

    try:
        img = to_rgb(img)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)  # ย่อด้านยาวสุดไม่เกิน max_size

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    except Exception:
        # ไฟล์ขาด (เน็ตหลุดระหว่างอัพโหลด), RAM ไม่พอ, โหมดสีแปลกๆ ฯลฯ
        logger.warning("compress_image: บีบอัดรูปไม่สำเร็จ เก็บไฟล์เดิม %s", name, exc_info=True)
        field_file.seek(0)
        return None

    if buf.tell() >= field_file.size:
        field_file.seek(0)
        return None

    new_name = os.path.splitext(os.path.basename(name))[0] + ".jpg"
    return ContentFile(buf.getvalue(), name=new_name)

#บีบอัดรูปเฉพาะที่เพิ่งอัพโหลด (ยังไม่ได้บันทึกลง storage) เพื่อไม่ให้บีบซ้ำทุกครั้งที่ save
def compress_uploaded_images(instance, field_names, **kwargs):
    for field_name in field_names:
        f = getattr(instance, field_name)
        if f and not f._committed:
            compressed = compress_image(f, **kwargs)
            if compressed is not None:
                setattr(instance, field_name, compressed)
