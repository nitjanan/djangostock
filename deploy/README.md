# ทำ HTTPS ให้ production (เงื่อนไขบังคับของ App Badge บนมือถือ)

## ทำไมต้องทำ

`navigator.setAppBadge()` และ `navigator.serviceWorker` เป็น **secure-context-only API**
บน origin ที่เป็น `http://` (ยกเว้น `localhost`) เบราว์เซอร์จะไม่สร้าง property พวกนี้ขึ้นมาเลย

ทดสอบยืนยันแล้วด้วย Chromium จริงผ่าน `http://192.168.0.104:8010/`:

```json
{ "isSecureContext": false, "hasServiceWorker": false, "hasSetAppBadge": false }
```

badge ที่เห็นบนเดสก์ท็อปทุกวันนี้คือ favicon ที่วาดด้วย canvas ซึ่งไม่ต้องใช้ secure context
ส่วนมือถือไม่มี favicon บนหน้าจอโฮม จึงไม่เห็นอะไรเลย
**แก้ที่โค้ดไม่ได้ ต้องขึ้น HTTPS เท่านั้น**

---

## ขั้นที่ 1 -- หาโฮสต์เนม

Let's Encrypt ออกใบรับรองให้ IP ไม่ได้ ต้องมีชื่อโฮสต์ เลือกทางใดทางหนึ่ง:

| ทาง | ค่าใช้จ่าย | หมายเหตุ |
|---|---|---|
| **DuckDNS** (แนะนำถ้าไม่อยากเสียเงิน) | ฟรี | สมัครที่ duckdns.org ได้ `ชื่อที่ตั้ง.duckdns.org` ชี้มาที่ public IP ของออฟฟิศ มี client อัปเดต IP อัตโนมัติเวลา IP เปลี่ยน |
| **ซื้อโดเมนเอง** | ~300-500 บาท/ปี | ดูเป็นมืออาชีพกว่า และย้ายผู้ให้บริการภายหลังง่าย |

ทั้งสองทางใช้กับ Caddy ได้เหมือนกัน ต่างแค่ชื่อที่ใส่ใน Caddyfile

## ขั้นที่ 2 -- เปิดพอร์ตที่เราเตอร์

Forward **80** และ **443** จากเราเตอร์มาที่ IP ภายในของเครื่อง server (`192.168.0.104`)

- พอร์ต 80 จำเป็นตอน Let's Encrypt ตรวจสอบความเป็นเจ้าของโดเมน ปิดไม่ได้
- ตั้ง IP ภายในของเครื่อง server ให้เป็น static หรือจอง DHCP reservation ไว้ ไม่งั้น IP เปลี่ยนแล้ว forward หลุด

## ขั้นที่ 3 -- ติดตั้ง Caddy

โหลด `caddy.exe` จาก caddyserver.com/download (ไฟล์เดียว ไม่ต้องติดตั้ง)

แก้ชื่อโฮสต์บรรทัดแรกใน [`Caddyfile`](Caddyfile) ให้ตรงกับที่ได้จากขั้นที่ 1 แล้วรัน:

```powershell
caddy run --config deploy\Caddyfile
```

Caddy จะขอใบรับรองเองและต่ออายุให้อัตโนมัติ ไม่ต้องตั้ง cron หรือ certbot

> เลือก Caddy แทน nginx เพราะบน Windows การตั้ง nginx + certbot ยุ่งกว่ามาก
> Caddy ทำ HTTPS อัตโนมัติมาในตัว

## ขั้นที่ 4 -- เปลี่ยนจาก runserver เป็น waitress

`manage.py runserver` เป็น dev server ไม่ควรใช้จริงและไม่ทน load
`gunicorn` ใน `Procfile` เป็นของเก่าสมัย Heroku รันบน Windows ไม่ได้

```powershell
pip install -r requirements.txt
python deploy\serve.py
```

## ขั้นที่ 5 -- แก้ settings.py

```python
DEBUG = False

# ใส่ชื่อโฮสต์จากขั้นที่ 1 + IP ภายในสำหรับคนในออฟฟิศ
ALLOWED_HOSTS = ['stgstock.duckdns.org', '192.168.0.104', '127.0.0.1']

# Caddy เป็นคนคุย TLS แล้วบอก Django ผ่าน header นี้
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True      # บรรทัด 250 เดิมเป็น False
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['https://stgstock.duckdns.org']
```

### กับดักที่ต้องระวัง

พอตั้ง `DEBUG = False` ตัว Django **หยุดเสิร์ฟ `/media/`** เพราะ `urls.py` เสิร์ฟให้เฉพาะตอน
`DEBUG` เป็น True เท่านั้น ถ้าไม่มีอะไรมารับช่วง `site.webmanifest` และไอคอน PWA จะ 404
ติดตั้ง PWA ไม่ได้ แล้ว badge ก็พังอีกรอบ

`Caddyfile` ที่ให้มามีบล็อก `handle_path /media/*` รับงานนี้ไว้แล้ว
ถ้าเปลี่ยนไปใช้ nginx หรือ IIS ต้องทำส่วนนี้เองด้วย

อย่าลืม `python manage.py collectstatic` หลังตั้ง `DEBUG = False`

## ขั้นที่ 6 -- ตรวจผล

1. เปิด `https://<โฮสต์เนม>/badge-debug/` บนมือถือ ดูว่าแถว **Secure context (ชี้ขาด)** เป็นสีเขียว
2. ลบไอคอนเดิมออกจากหน้าจอโฮมก่อน แล้ว Add to Home Screen ใหม่
   (manifest เดิม `name` ว่าง ติดตั้งไม่ได้จริง ของเก่าที่ค้างอยู่จะยังใช้ค่าเดิม)
3. เปิดแอปจากไอคอนใหม่ → `/badge-debug/` → กดปุ่มทดสอบ

---

## เรื่องที่ยังต้องเช็ค

**คนในออฟฟิศเข้าผ่านโฮสต์เนมได้ไหม** -- ตอนอยู่ในวงแลนแล้วเรียกชื่อโฮสต์ที่ชี้ไป public IP
เราเตอร์ต้องรองรับ NAT hairpin ส่วนใหญ่รองรับ แต่ไม่ทุกรุ่น ถ้าไม่รองรับจะเข้าไม่ได้จากในออฟฟิศ
ทางแก้คือตั้ง DNS ภายในให้ชื่อนี้ชี้ไป `192.168.0.104` แทน

**Android อาจขึ้นแค่จุด ไม่มีเลข** -- `setAppBadge(count)` บน Android ถูกแปลงเป็น notification dot
ของระบบ launcher มาตรฐาน (Pixel) วาดเป็นจุดเปล่า ๆ ส่วน Samsung One UI โชว์เลขได้ถ้าผู้ใช้เปิด
"แสดงพร้อมตัวเลข" เอง เป็นข้อจำกัดของ OS แก้ที่โค้ดไม่ได้
ถ้าจำเป็นต้องได้เลขจริงบน Android ต้องไปทาง Web Push (VAPID key + เก็บ subscription + ส่ง push จาก Django)
ซึ่งเป็นงานแยกอีกก้อน

**iOS** แสดงเลขได้จริงตั้งแต่ 16.4 ขึ้นไป ถ้าเปิดจากไอคอนบนหน้าจอโฮมและอนุญาต Notification แล้ว
