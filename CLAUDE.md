# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ระบบเบิกพัสดุ / จัดซื้อ (ใบขอเบิก, PR, เปรียบเทียบราคา, PO, รับของ, ซ่อมบำรุง, สมุดรถ, ผู้จัดจำหน่าย) ของกลุ่มบริษัท เขียนด้วย Django 4.2 + Python 3.9 บน MySQL 8 คอมเมนต์และข้อความในโค้ดเป็นภาษาไทย

## Commands

ใช้ Python ของ `venv/` เสมอ (python ของเครื่องเป็น 3.14 ไม่มีแพ็กเกจของโปรเจกต์) และตั้ง `PYTHONIOENCODING=utf-8` ไม่งั้นข้อความภาษาไทยพังบน Windows

```bash
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe manage.py runserver
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe manage.py test stock --keepdb --noinput            # ทั้งชุด
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe manage.py test stock.tests_new_old_product --keepdb  # ไฟล์เดียว
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe manage.py test stock.tests_new_old_product.NewOldProductTestCase.test_lowercase_to_uppercase_same_code --keepdb
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe manage.py makemigrations --check --dry-run          # model แก้แล้วลืมสร้าง migration
```

- เทสต์อยู่ใน `stock/tests.py` และ `stock/tests_*.py` (ไฟล์ละฟีเจอร์) รันบน MySQL จริง (`test_djangostockdb`) ไม่ใช่ SQLite
- CI (`.github/workflows/django-checks.yml`) ใช้ `DJANGO_SETTINGS_MODULE=djangostock.settings_ci` ซึ่งอ่าน DB จาก env และตัด `pg_db` ออก: migrate บน MySQL ว่าง → `check` → `makemigrations --check` → `test stock`
- `security-checks.yml`: gitleaks และ bandit บล็อกเฉพาะปัญหาใหม่ (bandit เทียบกับ `.github/bandit-baseline.json`) ส่วน CodeQL / pip-audit / `check --deploy` แค่รายงาน
- Deploy ด้วย `Procfile`: `release: python manage.py migrate` แล้วรัน gunicorn

## Local environment

- DB ที่เครื่อง dev เป็น MySQL 8 ใน docker container `djangostock-mysql` พอร์ต **13307** ฐาน `djangostockdb` อย่า restart MariaDB ตัวเก่า (ชนพอร์ต)
- `settings.py` โหลด `.env` จาก root ของโปรเจกต์ (`load_dotenv(BASE_DIR / ".env")`) สำหรับ email, `GOOGLE_MAPS_API_KEY`, `TOMTOM_API_KEY`
- `djangostock/local_settings.py` ไม่ได้ถูก import จากที่ไหน

## Architecture

แอปเดียวคือ `stock/` ไฟล์หลักใหญ่มาก: `views.py` (~14,600 บรรทัด, function views เกือบทั้งหมด) และ `models.py` (~74 model) ค้นด้วย Grep แทนการอ่านทั้งไฟล์ URL ทั้งหมดอยู่ใน `djangostock/urls.py` (ไม่มี `stock/urls.py`)

- **ฐานข้อมูล 2 ตัว:** `default` = MySQL ของระบบนี้ และ `pg_db` = PostgreSQL ภายนอกของโปรแกรมบัญชี Express (model `OESTNH`, `OESTND`, `OEINVD`, `OEINVH`, `APTRNH` เป็น `managed = False` และ query ผ่าน `.using('pg_db')`) เทสต์และ CI ต่อ `pg_db` ไม่ได้
- **ชื่อตาราง:** model ส่วนใหญ่ตั้ง `db_table` เป็นชื่อ CamelCase (เช่น `Requisition`, `Distributor`, `BaseUnit`) ตัวที่ไม่ได้ตั้งจะเป็น `stock_<model>` เช่น `Product` → `stock_product`, `Category` → `stock_category` ตาราง lookup ขึ้นต้นด้วย `Base*`
- **Collation ไม่สนตัวพิมพ์ (`utf8mb4_general_ci`):** `Product.objects.get(id='NT-G0-151')` เจอแถว `nt-g0-151` และ PK เก็บสองรหัสที่ต่างแค่ตัวเล็ก/ใหญ่ไม่ได้ ถ้าจะเปลี่ยนแค่ตัวพิมพ์ต้องผ่านรหัสชั่วคราว (ดู `newOld` / `_transfer_product` ใน `views.py`)
- **บริษัทที่เลือก:** login แล้วต้องเลือกบริษัท เก็บใน `request.session['company_code']` และ view ส่วนใหญ่กรองข้อมูลตามค่านี้ (`'ALL'` = ทุกบริษัท) `RequireCompanyCodeMiddleware` จะ logout คนที่ session ไม่มีค่านี้ ในเทสต์ให้ `force_login` แล้วตั้ง `session["company_code"]` เอง
- **สิทธิ์:** ใช้ Django Group ผ่าน helper `is_*(user)` ใน `views.py` (เช่น `is_edit_new_old` → กลุ่ม `NewOld`) ร่วมกับ `Position` / `BasePermission` / `PositionBasePermission` และ `UserProfile.visible` (`BaseVisible`) กำหนดว่าเห็นแท็บ/เมนูไหน ปุ่มที่ซ่อนใน template ต้องเช็คสิทธิ์ซ้ำที่ server ด้วย
- **Audit log:** `AuditUserMiddleware` + `stock/signals.py` + `stock/audit.py` บันทึกการแก้ `ComparisonPrice*` / `PurchaseOrder*` ลง `DocumentChangeLog`
- **อื่นๆ:** `Product.save()` สร้าง QR code ลง `media/pd_qr_codes/` เอง, REST API ใช้ DRF + SimpleJWT (`serializers.py`), admin ใช้ django-import-export (`resources.py`), template อยู่ใน `stock/templates/` แยกโฟลเดอร์ตามโมดูล ใช้ Bootstrap 4 + crispy-forms
- **Migrations:** อยู่ที่ `stock/migrations/` (`migrations_old/` เป็นของเก่า ไม่ได้ใช้) เมื่อ branch ชนกันเรื่อง migration ให้สร้าง merge migration และ migration ต้องรันบน MySQL ว่างได้ (CI ตรวจ)

## Git

- `djangostock/settings.py`: ถ้าไฟล์นี้แก้แค่ `'PORT'` ของ `DATABASES['default']` (เช่น `''` → `'13307'` สำหรับ MySQL ใน docker ที่เครื่อง) ไม่ต้อง `git add` / commit ไฟล์นี้ ให้ค้างไว้ในเครื่อง เพราะ production ต้องใช้ `'PORT': ''`
  - ก่อน commit ให้ดู `git diff djangostock/settings.py` ถ้ามีส่วนอื่นเปลี่ยนด้วย ให้ stage เฉพาะส่วนนั้น ไม่เอาบรรทัด `PORT` ไปด้วย
  - อย่าใช้ `git add -A` / `git add .` / `git commit -a` ให้ add ทีละไฟล์ (`runtime.txt` และ `.superpowers/` ก็มักมีของเครื่องค้างอยู่)
- ไฟล์ใน repo เป็น LF และเครื่องตั้ง `core.autocrlf=true` ถ้าเขียน blob เองด้วย `git hash-object` ต้องใส่ `--path <file>` ไม่งั้น diff จะขึ้นว่าแก้ทั้งไฟล์
