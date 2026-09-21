"""สร้าง VAPID keypair สำหรับ Web Push (รันครั้งเดียวตอนตั้งระบบ)

    python manage.py generate_vapid_keys

แล้วเอาค่าที่ได้ไปตั้งเป็น environment variable บนเครื่อง server
ห้าม commit private key ลง git -- ใครได้ไปจะส่งแจ้งเตือนปลอมในนามระบบได้

ถ้าเปลี่ยน key ใหม่ subscription เดิมทั้งหมดจะใช้ไม่ได้
ผู้ใช้ทุกคนต้องกดสมัครรับแจ้งเตือนใหม่
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def _b64(raw):
    """urlsafe base64 แบบไม่มี padding ตามที่สเปค VAPID กำหนด"""
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


class Command(BaseCommand):
    help = 'สร้าง VAPID keypair สำหรับ Web Push'

    def handle(self, *args, **options):
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        private_raw = private_key.private_numbers().private_value.to_bytes(32, 'big')
        public_raw = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        self.stdout.write('')
        self.stdout.write('ตั้งค่าสองบรรทัดนี้เป็น environment variable บนเครื่อง server:')
        self.stdout.write('')
        self.stdout.write('VAPID_PUBLIC_KEY=%s' % _b64(public_raw))
        self.stdout.write('VAPID_PRIVATE_KEY=%s' % _b64(private_raw))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('อย่า commit private key ลง git'))
