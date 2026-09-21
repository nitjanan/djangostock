# Web Push -- อัปเดต badge ตอนปิดแอปอยู่

## ข้อจำกัดที่ต้องรู้ก่อน

**badge แบบเงียบสนิทตอนแอปปิด ทำไม่ได้** ทั้ง iOS และ Chrome บังคับให้ subscription
เป็น `userVisibleOnly: true` คือ push ทุกครั้งต้องมีแจ้งเตือนให้ผู้ใช้เห็น
ถ้าเราไม่แสดงเอง เบราว์เซอร์จะขึ้นข้อความ "เว็บไซต์นี้อัปเดตในเบื้องหลัง" ให้แทน

ระบบนี้จึงออกแบบให้ **push น้อยครั้งแต่มีความหมาย** แทนการอัปเดตตัวเลขถี่ ๆ:

| กติกา | เหตุผล |
|---|---|
| ส่งเฉพาะตอนตัวเลข **เพิ่มขึ้น** | ตอนตัวเลขลดแปลว่าผู้ใช้เพิ่งเคลียร์งาน ซึ่งเขาอยู่ในแอปอยู่แล้ว polling อัปเดตให้เอง ไม่ต้องเด้ง |
| เว้นระยะขั้นต่ำ 30 นาที/คน | กันโดนเด้งรัวตอนมีงานเข้าติด ๆ กัน |
| ส่งเฉพาะ 08:00-18:00 | ไม่กวนตอนกลางคืน |
| รวมเป็นแบนเนอร์เดียว | "มีรายการรอดำเนินการ N รายการ" ไม่เด้งทีละใบ |

ปรับได้ด้วย environment variable: `PUSH_MIN_INTERVAL_MINUTES`,
`PUSH_ACTIVE_HOUR_START`, `PUSH_ACTIVE_HOUR_END`

**ต้องมี HTTPS ก่อน** และผู้ใช้ต้องติดตั้ง PWA ลงหน้าจอโฮม (บน iOS บังคับ)

---

## ติดตั้ง

### 1. สร้าง VAPID key (ครั้งเดียว)

```powershell
python manage.py generate_vapid_keys
```

ตั้งค่าที่ได้เป็น environment variable ระดับเครื่อง:

```powershell
[Environment]::SetEnvironmentVariable('VAPID_PUBLIC_KEY', '<ค่าที่ได้>', 'Machine')
[Environment]::SetEnvironmentVariable('VAPID_PRIVATE_KEY', '<ค่าที่ได้>', 'Machine')
```

> **ห้าม commit private key ลง git** ใครได้ไปจะส่งแจ้งเตือนปลอมในนามระบบได้
> ถ้าเปลี่ยน key ใหม่ subscription เดิมใช้ไม่ได้ทั้งหมด ผู้ใช้ต้องกดอนุญาตใหม่

### 2. migrate

```powershell
python manage.py migrate
```

### 3. ตั้ง Task Scheduler ให้ส่งทุก 5 นาที

```powershell
schtasks /create /tn "STG Stock Badge Push" /sc minute /mo 5 ^
  /tr "C:\Users\Userpc\Documents\DjangoProject\djangostock\.venv\Scripts\python.exe C:\Users\Userpc\Documents\DjangoProject\djangostock\manage.py send_badge_push" ^
  /ru SYSTEM
```

ตรวจก่อนเปิดใช้จริงด้วย `--dry-run` ซึ่งคำนวณและบอกว่าจะส่งให้ใคร แต่ไม่ส่งจริง:

```powershell
python manage.py send_badge_push --dry-run
python manage.py send_badge_push --force --dry-run   # ข้ามเช็คเวลาและ throttle
```

---

## ผู้ใช้ต้องทำอะไร

1. เปิดเว็บผ่าน HTTPS แล้ว Add to Home Screen
2. เปิดแอปจากไอคอน แล้วแตะที่ไหนก็ได้ครั้งแรก -- ระบบจะขอสิทธิ์แจ้งเตือน
   (Safari ยอมให้ขอสิทธิ์จาก user gesture เท่านั้น จึงผูกไว้กับการแตะครั้งแรก)
3. กดอนุญาต -- หน้าเว็บจะสมัคร subscription ส่งไปเก็บที่เซิร์ฟเวอร์เอง

ตรวจสถานะได้ที่ `/badge-debug/`

---

## โครงสร้าง

| ไฟล์ | หน้าที่ |
|---|---|
| `stock/models.py` -> `PushSubscription` | เก็บ endpoint + key ของแต่ละอุปกรณ์ |
| `stock/views.py` -> `pushSubscribe` / `pushUnsubscribe` | รับ/ลบ subscription |
| `stock/templates/sw.js` | รับ push แล้วเรียก `setAppBadge` + แสดงแจ้งเตือน |
| `stock/templates/layouts.html` | ขอสิทธิ์และสมัคร subscription |
| `stock/management/commands/send_badge_push.py` | งานตามเวลา คำนวณและส่ง |
| `stock/management/commands/generate_vapid_keys.py` | สร้างคีย์ |

`send_badge_push` ใช้ `companyVisibleTab` ตัวเดียวกับที่หน้าเว็บใช้ โดยสร้าง request
ปลอมขึ้นมาให้ (ตรรกะเดิมอ่าน `request.user` และ `request.session`) เพื่อไม่ต้องรื้อ
ตรรกะนับแจ้งเตือนที่ซับซ้อนออกเป็นสองชุดที่ต้องตามแก้คู่กัน
ทดสอบแล้วว่าค่าที่ได้ตรงกับที่หน้าเว็บคำนวณทุกราย

## สิ่งที่ยังไม่ได้ทำ

- ยังไม่ลบ subscription ตอน logout -- ถ้าเครื่องถูกใช้ร่วมกัน คนก่อนหน้าอาจยังได้
  แจ้งเตือนจนกว่าคนใหม่จะล็อกอินแล้วสมัครทับ (endpoint เดียวกันจะถูกผูกกับคนล่าสุด)
- ยังไม่มีปุ่มให้ผู้ใช้ปิดแจ้งเตือนเองในหน้าเว็บ (ปิดได้จาก setting ของเครื่อง)
- ยังไม่มี event hook ตอนสร้าง/อนุมัติเอกสาร -- ตอนนี้พึ่งงานตามเวลาอย่างเดียว
  หน่วงสูงสุดเท่ากับ interval ที่ตั้งใน Task Scheduler
