"""ส่ง Web Push อัปเดต badge ให้ผู้ใช้ที่มีงานใหม่เข้ามา

ตั้งให้ Windows Task Scheduler เรียกทุก 5 นาที:
    python manage.py send_badge_push

ตัวเลือก:
    --dry-run   คำนวณและแสดงผลว่าจะส่งให้ใครบ้าง แต่ไม่ส่งจริง
    --force     ข้ามการเช็คช่วงเวลาทำงานและ throttle (ใช้ตอนทดสอบ)

นโยบายการส่ง -- แยก "badge" ออกจาก "แบนเนอร์" ชัดเจน:

  badge (ตัวเลขบนไอคอน)
    ส่งทุกครั้งที่ตัวเลขเปลี่ยน ไม่ว่าเพิ่มหรือลด และไม่จำกัดเวลา
    เพื่อให้เลขบนไอคอนตรงกับข้อมูลจริงเสมอ

  แบนเนอร์ (สิ่งที่ผู้ใช้เห็นและรบกวน)
    แสดงได้อย่างมากทุก PUSH_BANNER_INTERVAL_HOURS ชั่วโมง
    และเฉพาะในช่วง PUSH_ACTIVE_HOUR_START ถึง PUSH_ACTIVE_HOUR_END

รอบที่ยังไม่ถึงเวลาแบนเนอร์ จะส่ง payload notify=False เพื่ออัปเดต badge อย่างเดียว
พฤติกรรมฝั่ง service worker คุมด้วย PUSH_SILENT_MODE

ข้อควรรู้: iOS บังคับ userVisibleOnly ทดสอบแล้วว่าการแสดง notification
แล้วปิดทันที ('show-close') แบนเนอร์ยังโผล่ทุกครั้ง โหมด 'none' คือไม่แสดงเลย
ซึ่งเงียบกว่าแต่เสี่ยงที่เบราว์เซอร์จะขึ้นข้อความเองหรือเพิกถอนสิทธิ์ push

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
                            help='บังคับแสดงแบนเนอร์ ข้ามการเช็คช่วงเวลาและรอบ 4 ชั่วโมง')

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
        in_banner_hours = (settings.PUSH_ACTIVE_HOUR_START <= now.hour < settings.PUSH_ACTIVE_HOUR_END)
        banner_gap = timezone.timedelta(hours=settings.PUSH_BANNER_INTERVAL_HOURS)

        # ผู้ใช้คนเดียวอาจมีหลายอุปกรณ์ การนับ count กิน query หลักร้อยต่อครั้ง
        # จึงคำนวณครั้งเดียวต่อคนต่อรอบ แล้วใช้ซ้ำกับทุกอุปกรณ์ของคนนั้น
        count_cache = {}

        sent = skipped = failed = 0
        for sub in PushSubscription.objects.select_related('user').all():
            if not sub.user.is_active:
                continue

            if sub.user_id not in count_cache:
                count_cache[sub.user_id] = self._count_for_user(sub.user)
            count = count_cache[sub.user_id]

            # ไม่มีอะไรเปลี่ยน ก็ไม่ต้องรบกวนอุปกรณ์
            if count == sub.last_pushed_count:
                skipped += 1
                continue

            # ถึงเวลาที่ควรแจ้งเตือนหรือยัง
            notify = force or (
                in_banner_hours
                and (sub.last_banner_at is None or (now - sub.last_banner_at) >= banner_gap)
            )

            # ไม่ถึงเวลาแบนเนอร์ก็ยังส่ง -- แต่ส่งแบบเงียบเพื่ออัปเดต badge อย่างเดียว
            # ให้เลขบนไอคอนตรงกับข้อมูลตลอดแม้แอปปิดอยู่

            if dry_run:
                self.stdout.write('[dry-run] %s: %d -> %d (%s)'
                                  % (sub.user.username, sub.last_pushed_count, count,
                                     'แสดงแบนเนอร์' if notify
                                     else 'เงียบ โหมด %s' % settings.PUSH_SILENT_MODE))
                sent += 1
                continue

            if self._send(sub, count, notify):
                sub.last_pushed_count = count
                sub.last_pushed_at = now
                fields = ['last_pushed_count', 'last_pushed_at']
                if notify:
                    sub.last_banner_at = now
                    fields.append('last_banner_at')
                sub.save(update_fields=fields)
                sent += 1
            else:
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            'ส่ง %d / ข้าม %d / ล้มเหลว %d' % (sent, skipped, failed)))
        # บรรทัดสรุปแบบ ASCII ล้วน ให้ scheduler หยิบไป log ได้
        # console ของ Windows เป็น cp1252 เขียนภาษาไทยลงไปไม่ได้ ถ้าไม่มีบรรทัดนี้
        # ความล้มเหลวจะเงียบหายไปทั้งหมด (เคยเกิดจริง: ลืมติดตั้ง pywebpush
        # ใน Python ที่เซิร์ฟเวอร์ใช้ ทุก push พังหมดโดยไม่มีสัญญาณอะไรเลย)
        self.stdout.write('SUMMARY sent=%d skipped=%d failed=%d' % (sent, skipped, failed))

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

    def _send(self, sub, count, notify=True):
        from pywebpush import WebPushException, webpush

        payload = {
            'count': count,
            # notify=False -> service worker แสดงแล้วปิดทันที ผู้ใช้แทบไม่เห็น
            'notify': bool(notify),
            # บอก service worker ว่ารอบเงียบให้ทำตัวยังไง เปลี่ยนได้จาก settings
            # โดยไม่ต้องแก้ sw.js แล้วรอให้อุปกรณ์โหลด service worker ใหม่
            'silent_mode': getattr(settings, 'PUSH_SILENT_MODE', 'none'),
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
                self.stderr.write('ERROR push user=%s status=%s %r'
                                  % (sub.user.username, status, e))
            return False
        except Exception as e:
            self.stderr.write('ERROR push user=%s %r' % (sub.user.username, e))
            return False
