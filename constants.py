"""แหล่งความจริงเดียว (single source of truth) สำหรับค่าที่ใช้ทั้งฝั่ง Python และ JS
เพื่อ "กัน mismatch" — ค่าพวกนี้ถูกส่งเข้า template เป็น window.CONFIG ให้ JS ใช้ค่าเดียวกัน
(ดู base.html + app.py context_processor)
"""

ROLES = ["SELLER", "MARKET_OWNER", "ADMIN"]
RENT_TYPES = ["DAILY", "WEEKLY", "MONTHLY"]
BOOKING_STATUS = ["PENDING", "CONFIRMED", "CANCELLED"]
PAYMENT_STATUS = ["PENDING", "PAID", "FAILED"]

ROLE_LABEL = {
    "SELLER": "ผู้ขาย (พ่อค้าแม่ค้า)",
    "MARKET_OWNER": "เจ้าของตลาด / ผู้ให้เช่าพื้นที่",
    "ADMIN": "ผู้ดูแลระบบ",
}

RENT_TYPE_LABEL = {
    "DAILY": "รายวัน",
    "WEEKLY": "รายสัปดาห์",
    "MONTHLY": "รายเดือน",
}

# รวมค่าที่อยากส่งให้ JS ใช้
CLIENT_CONFIG = {
    "ROLES": ROLES,
    "RENT_TYPES": RENT_TYPES,
    "RENT_TYPE_LABEL": RENT_TYPE_LABEL,
    "ROLE_LABEL": ROLE_LABEL,
}
