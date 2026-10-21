# settings สำหรับ GitHub Actions (.github/workflows): ฐานข้อมูลอ่านจาก env (MySQL service ของ CI)
# และตัด pg_db (Express บน PostgreSQL ภายนอก) ออก CI ต้องไม่ต่อออกไปฐานข้อมูลจริง
import os

from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'djangostockdb'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    },
}

# ไม่ยิง API แผนที่จริงระหว่าง CI
GOOGLE_MAPS_API_KEY = None
TOMTOM_API_KEY = None
