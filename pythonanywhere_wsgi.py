# ============================================================
# WSGI สำหรับ PythonAnywhere
# วิธีใช้: คัดลอกเนื้อหาทั้งไฟล์นี้ไปวางทับใน WSGI file ของ PythonAnywhere
# (แท็บ Web -> ลิงก์ "WSGI configuration file") แล้วแก้ YOURUSERNAME เป็นชื่อจริง
# ============================================================
import os
import sys

# 1) ชี้ไปที่โฟลเดอร์โปรเจกต์บน PythonAnywhere (แก้ YOURUSERNAME)
project = "/home/YOURUSERNAME/flask-app"
if project not in sys.path:
    sys.path.insert(0, project)

# 2) ตั้งค่า env (แก้ค่าตามต้องการ — อย่างน้อยเปลี่ยน SECRET_KEY ให้ยาวๆ สุ่มๆ)
os.environ["SECRET_KEY"] = "เปลี่ยนเป็นข้อความสุ่มยาวๆ-abc123xyz789"
os.environ["ADMIN_CODE"] = "ake112233"
os.environ["SMS_PROVIDER"] = "console"
os.environ["ENABLE_QUICK_LOGIN"] = "1"
os.environ["PROMPTPAY_ID"] = "0812345678"
os.environ["APP_NAME"] = "Smart Hawker"

# 3) โหลดแอป (PythonAnywhere ต้องการตัวแปรชื่อ application)
from app import app as application
