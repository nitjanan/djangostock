import io
import os
import sys
import threading
import time

from django.apps import AppConfig


class StockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock'

    def ready(self):
        _start_badge_push_scheduler()


# กันเธรดซ้ำ -- ready() ถูกเรียกได้มากกว่าหนึ่งครั้งในบางสถานการณ์
_scheduler_started = False
_scheduler_lock = threading.Lock()


def _log_safe(message):
    """เขียน log โดยไม่พึ่ง encoding ของ console

    stderr ของโปรเซสบน Windows มักเป็น cp1252 ซึ่งเข้ารหัสภาษาไทยไม่ได้
    ข้อความที่ส่งเข้ามาจึงควรเป็น ASCII และยังเผื่อ errors='replace' ไว้อีกชั้น
    """
    try:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()
    except Exception:
        try:
            enc = getattr(sys.stderr, 'encoding', None) or 'ascii'
            sys.stderr.buffer.write(message.encode(enc, 'replace') + b"\n")
        except Exception:
            pass


def _should_run_scheduler():
    """ตัดสินว่าโปรเซสนี้ควรเป็นตัวส่ง push หรือไม่

    ต้องระวังสองเรื่อง:
      1. คำสั่ง manage.py อื่น ๆ (migrate, collectstatic, shell, test) ไม่ควรมี
         เธรดนี้ติดไปด้วย ไม่งั้น migrate ครั้งเดียวก็ยิงแจ้งเตือนใส่ผู้ใช้
      2. runserver แบบมี auto-reload จะ fork เป็นสองโปรเซส ถ้าไม่กันไว้
         ผู้ใช้จะได้แจ้งเตือนซ้ำสองรอบทุกครั้ง
    """
    from django.conf import settings

    if not getattr(settings, 'PUSH_AUTO_SEND', True):
        return False

    argv = sys.argv
    # เรียกผ่าน manage.py ด้วยคำสั่งอื่นที่ไม่ใช่ runserver -> ไม่ต้องรัน
    if len(argv) > 1 and argv[1] != 'runserver':
        return False

    if len(argv) > 1 and argv[1] == 'runserver' and '--noreload' not in argv:
        # โหมด auto-reload: โปรเซสลูกเท่านั้นที่มี RUN_MAIN
        return os.environ.get('RUN_MAIN') == 'true'

    return True


def _start_badge_push_scheduler():
    global _scheduler_started

    if not _should_run_scheduler():
        return

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    from django.conf import settings

    interval = max(30, int(getattr(settings, 'PUSH_AUTO_INTERVAL_MINUTES', 1)) * 60)

    def loop():
        from django.core.management import call_command
        from django.db import connection

        # หน่วงก่อนรอบแรก ให้เซิร์ฟเวอร์ boot เสร็จและรับ request ได้ก่อน
        time.sleep(30)
        while True:
            try:
                # ดักผลลัพธ์ไว้ใน buffer ไม่ปล่อยลง console โดยตรง
                # console ของ Windows ใช้ cp1252 เขียนข้อความไทยลงไปจะโยน
                # UnicodeEncodeError ทำให้เธรดพังและ push ตายเงียบทั้งระบบ
                buf = io.StringIO()
                call_command('send_badge_push', verbosity=0, stdout=buf, stderr=buf)
                # หยิบเฉพาะบรรทัด ASCII ออกมา log -- ถ้าไม่ทำ ความล้มเหลวจะเงียบ
                # สนิท เคยเกิดจริงตอน Python ที่รันเซิร์ฟเวอร์ไม่มี pywebpush
                for line in buf.getvalue().splitlines():
                    if line.startswith('ERROR') or (line.startswith('SUMMARY') and 'failed=0' not in line):
                        _log_safe('badge push: ' + line)
            except Exception as e:
                _log_safe('badge push scheduler error: %r' % (e,))
            finally:
                # เธรดนี้อยู่ยาว ถ้าไม่ปิด connection ที่ใช้เสร็จแล้ว
                # จะค้างเป็น connection ตายใน MySQL
                try:
                    connection.close()
                except Exception:
                    pass
            time.sleep(interval)

    t = threading.Thread(target=loop, name='badge-push-scheduler', daemon=True)
    t.start()
    _log_safe('badge push scheduler started (every %d seconds)' % interval)
