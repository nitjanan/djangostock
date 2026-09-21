"""ส่ง Web Push อัปเดต badge ให้ผู้ใช้ที่มีงานใหม่เข้ามา

ตั้งให้ Windows Task Scheduler เรียกทุก 5 นาที:
    python manage.py send_badge_push

ตัวเลือก:
    --dry-run   คำนวณและแสดงผลว่าจะส่งให้ใครบ้าง แต่ไม่ส่งจริง
    --force     ข้ามการเช็คช่วงเวลาทำงานและ throttle (ใช้ตอนทดสอบ)

นโยบายการส่ง (ออกแบบให้ไม่กวนผู้ใช้):
  * ส่งเฉพาะตอนตัวเลข "เพิ่มขึ้น" จากครั้งที่ส่งไปล่าสุด
    ตอนตัวเลขลดลงแปลว่าผู้ใช้เพิ่งเคลียร์งาน ซึ่งตอนนั้นเขาอยู่ในแอปอยู่แล้ว
    polling ในหน้าเว็บอัปเดต badge ให้เองโดยไม่ต้องเด้งแจ้งเตือน
  * เว้นระยะขั้นต่ำต่อคนตาม PUSH_MIN_INTERVAL_MINUTES
  * ส่งเฉพาะในช่วง PUSH_ACTIVE_HOUR_START ถึง PUSH_ACTIVE_HOUR_END

ทำไมต้องสร้าง request ปลอม: ตรรกะนับแจ้งเตือนทั้งหมดอยู่ใน context processor
ซึ่งอ่าน request.user และเขียน/อ่าน request.session การสร้าง request ปลอมให้มัน
ใช้ตรงนี้ ทำให้ไม่ต้องไปรื้อตรรกะเดิมที่ซับซ้อนและเสี่ยงพังเป็นสองชุด
"""
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.utils import timezone

from stock.models import PushSubscription


class Command(BaseCommand):
    help = 'ส่ง Web Push อัปเดต badge ให้ผู้ใช้ที่มีงานใหม่'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='แสดงผลว่าจะส่งให้ใคร แต่ไม่ส่งจริง')
        parser.add_argument('--force', action='store_true',
                            help='ข้ามการเช็คช่วงเวลาและ throttle')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
            self.stderr.write(self.style.ERROR(
                'ยังไม่ได้ตั้ง VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY '
                '-- รัน python manage.py generate_vapid_keys ก่อน'))
            return

        # โปรเจกต์นี้ตั้ง USE_TZ = False ทำให้ timezone.now() คืน naive datetime
        # ซึ่ง timezone.localtime() รับไม่ได้ -- รองรับทั้งสองโหมดไว้
        # เผื่อวันหลังเปิด USE_TZ แล้วโค้ดตรงนี้ไม่พัง
        now = timezone.localtime() if settings.USE_TZ else timezone.now()
        if not force and not (settings.PUSH_ACTIVE_HOUR_START <= now.hour < settings.PUSH_ACTIVE_HOUR_END):
            self.stdout.write('นอกช่วงเวลาทำงาน (%02d:00-%02d:00) ข้ามรอบนี้'
                              % (settings.PUSH_ACTIVE_HOUR_START, settings.PUSH_ACTIVE_HOUR_END))
            return

        min_gap = timezone.timedelta(minutes=settings.PUSH_MIN_INTERVAL_MINUTES)

        sent = skipped = failed = 0
        for sub in PushSubscription.objects.select_related('user').all():
            if not sub.user.is_active:
                continue

            if not force and sub.last_pushed_at and (now - sub.last_pushed_at) < min_gap:
                skipped += 1
                continue

            count = self._count_for_user(sub.user)

            # ส่งเฉพาะตอนมีงานใหม่เข้ามาจริง ๆ
            if count <= sub.last_pushed_count:
                # ตัวเลขลดลงหรือเท่าเดิม -- ไม่เด้ง แต่จำค่าใหม่ไว้เทียบรอบหน้า
                if count != sub.last_pushed_count:
                    sub.last_pushed_count = count
                    sub.save(update_fields=['last_pushed_count'])
                skipped += 1
                continue

            if dry_run:
                self.stdout.write('[dry-run] %s: %d -> %d'
                                  % (sub.user.username, sub.last_pushed_count, count))
                sent += 1
                continue

            if self._send(sub, count):
                sub.last_pushed_count = count
                sub.last_pushed_at = now
                sub.save(update_fields=['last_pushed_count', 'last_pushed_at'])
                sent += 1
            else:
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            'ส่ง %d / ข้าม %d / ล้มเหลว %d' % (sent, skipped, failed)))

    def _count_for_user(self, user):
        """นับแจ้งเตือนของ user โดยใช้ตรรกะเดียวกับที่หน้าเว็บใช้"""
        from stock.context_processors import companyVisibleTab

        request = RequestFactory().get('/')
        request.user = user
        # context processor อ่านและเขียน session ระหว่างคำนวณ
        # ใช้ dict ธรรมดาแทนของจริงได้ เพราะใช้แค่ภายในรอบการคำนวณนี้
        request.session = {}
        try:
            return companyVisibleTab(request).get('global_notification_badge_count', 0) or 0
        except Exception as e:
            self.stderr.write('นับไม่สำเร็จสำหรับ %s: %s' % (user.username, e))
            return 0

    def _send(self, sub, count):
        from pywebpush import WebPushException, webpush

        payload = {
            'count': count,
            'title': 'Southern Group Stock',
            'body': 'มีรายการรอดำเนินการ %d รายการ' % count,
            'url': '/',
        }
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={'sub': 'mailto:%s' % settings.VAPID_ADMIN_EMAIL},
                timeout=10,
            )
            return True
        except WebPushException as e:
            status = getattr(e.response, 'status_code', None)
            # 404/410 = endpoint ตายแล้ว (ผู้ใช้ถอนแอปหรือล้างข้อมูล) ลบทิ้งได้เลย
            if status in (404, 410):
                self.stdout.write('ลบ subscription ที่หมดอายุของ %s' % sub.user.username)
                sub.delete()
            else:
                self.stderr.write('ส่งให้ %s ไม่สำเร็จ (status=%s): %s'
                                  % (sub.user.username, status, e))
            return False
        except Exception as e:
            self.stderr.write('ส่งให้ %s ไม่สำเร็จ: %s' % (sub.user.username, e))
            return False
