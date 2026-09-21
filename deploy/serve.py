"""
รัน Django ด้วย waitress แทน manage.py runserver

runserver เป็น dev server เท่านั้น -- ไม่ทน load และไม่ควรเปิดสู่อินเทอร์เน็ต
ส่วน gunicorn ใน Procfile (ของเก่าสมัย Heroku) รันบน Windows ไม่ได้
waitress เป็น WSGI server ที่ทำงานบน Windows ได้จริง

bind ไว้ที่ 127.0.0.1 เท่านั้น -- ห้ามเปิดออกวงนอกตรง ๆ
ให้ Caddy เป็นตัวเดียวที่รับ request จากภายนอกแล้ว proxy เข้ามา

วิธีรัน:
    python deploy\serve.py
"""
import os
import sys

# สคริปต์นี้อยู่ใน deploy/ ตอนรัน python deploy\serve.py ตัว Python จะใส่ deploy/
# ลงใน sys.path ไม่ใช่ root ของโปรเจกต์ ทำให้ import djangostock.settings ไม่เจอ
# จึงต้องเติม root เข้าไปเอง
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangostock.settings')

from django.core.wsgi import get_wsgi_application
from waitress import serve

application = get_wsgi_application()

if __name__ == '__main__':
    serve(
        application,
        host='127.0.0.1',
        port=8020,
        threads=8,
        # Caddy เป็นคนคุย TLS กับ client แล้วส่ง X-Forwarded-Proto มาให้
        # ตั้ง url_scheme ให้ Django มองว่า request เป็น https
        url_scheme='https',
    )
