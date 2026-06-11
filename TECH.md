# Smart Hawker — เทคนิค / เครื่องมือ / Flow การทำงาน (ฉบับละเอียด)

แอปหา/จองพื้นที่ขายของหาบเร่ + เจ้าของตลาด · เวอร์ชันปัจจุบัน = **Flask + Jinja2 + vanilla JS/CSS**

---

## 1. ภาษาที่ใช้ (Languages)
| ภาษา | ใช้ทำอะไร |
|---|---|
| **Python** | หลังบ้านทั้งหมด (Flask API + ตรรกะ + ฐานข้อมูล) |
| **HTML** (Jinja2 template) | โครงหน้าเว็บ |
| **CSS** | ดีไซน์ + อนิเมชั่น (เขียนเอง ไม่ใช้เฟรมเวิร์ก) |
| **JavaScript** (vanilla) | โต้ตอบฝั่งผู้ใช้ + เรียก API |
| **SQL** | ฐานข้อมูล (สร้างผ่าน SQLAlchemy ไม่ได้เขียนมือ) |


---

## 2. เครื่องมือ / ไลบรารี (Tools & Libraries)
| เครื่องมือ | หน้าที่ | ทำไมเลือก |
|---|---|---|
| **Flask 3.0** | เว็บเฟรมเวิร์ก (เสิร์ฟหน้า + API) | เบา เรียนง่าย Python ล้วน |
| **Jinja2** | เทมเพลต HTML (มากับ Flask) | `base.html` เขียนครั้งเดียว หน้าอื่นสืบทอด → หลายหน้าไม่ซ้ำซ้อน |
| **Flask-SQLAlchemy** | ORM คุยฐานข้อมูล | เขียน Python แทน SQL ดิบ จัดการความสัมพันธ์ง่าย |
| **SQLite** | ฐานข้อมูล (ไฟล์เดียว) | ไม่ต้องตั้งเซิร์ฟเวอร์ DB / ขึ้น Postgres ทีหลังได้ |
| **Flask session** | ระบบ login (cookie เซ็นชื่อ) | built-in ปลอดภัย ไม่ต้องลง JWT |
| **python-dotenv** | อ่านค่าตั้งค่าจาก `.env` | แยก secret ออกจากโค้ด |
| **qrcode + Pillow** | สร้างรูป QR PromptPay | เรนเดอร์ภาพฝั่ง server |
| **Leaflet + OpenStreetMap** | แผนที่ (โหลดผ่าน CDN) | ฟรี ไม่ต้องใช้ API key |
| **Nominatim** | ค้นหาที่อยู่ / แปลงพิกัด→จังหวัด | ฟรี (ของ OpenStreetMap) |
| **Lucide** | ไอคอน (CDN) | เส้นสะอาด สวย |
| **Playwright** (เฉพาะตอนทดสอบ) | เปิดเบราว์เซอร์จริงคลิกทดสอบ | ยืนยันทุกปุ่มกดได้ + ไม่มี JS error |

---

## 3. เทคนิค & นวัตกรรมเด่น 
1. **MPA + Jinja2 inheritance** — `base.html` เป็นแม่แบบ (หัว/สคริปต์/ตัวแปรกลาง) หน้าอื่น `{% extends %}` → ลดโค้ดซ้ำมหาศาลแม้มี 19 หน้า
2. **กัน mismatch ด้วย "แหล่งความจริงเดียว"** — `constants.py` เก็บค่า role/rentType ชุดเดียว แล้ว**ส่งเข้า `window.CONFIG`** ให้ JS ใช้ค่าเดียวกับ Python (ไม่มีทางพิมพ์ค่าไม่ตรงกัน)
3. **API client เดียว** — ทุก fetch ฝั่ง JS ผ่านอ็อบเจกต์ `API` ตัวเดียวใน `app.js` → รูปแบบ request/response เหมือนกันหมด
4. **Response รูปแบบเดียว** — ทุก endpoint ตอบ `{ok:true,...}` หรือ `{ok:false,error}` ผ่านฟังก์ชัน `ok()/fail()`
5. **Auth + RBAC 3 บทบาท** (ผู้ขาย/เจ้าของตลาด/แอดมิน) ด้วย decorator `@login_required` / `@admin_required` — ตรวจสิทธิ์ที่เดียว
6. **OTP ปลอดภัย** — เก็บเป็น **HMAC-SHA256 hash** (ไม่เก็บรหัสดิบ) + หมดอายุ 5 นาที + ใช้ครั้งเดียว
7. **PromptPay QR มาตรฐาน EMVCo จริง** — `promptpay.py` สร้าง payload เอง (รวม CRC16) สแกนจ่ายได้จริง แล้วเรนเดอร์เป็น PNG
8. **แผนที่ปักหมุด + reverse geocode** — คลิก/ค้นหา/GPS แล้ว**เติมจังหวัด-เขตอัตโนมัติ** (ผู้สูงอายุไม่ต้องพิมพ์พิกัด)
9. **DB Transaction** — ตอนจ่ายเงิน/ลบ ใช้ commit ครั้งเดียวอัปเดตหลายตาราง (atomic ไม่ค้างครึ่งทาง)
10. **Provider abstraction (SMS)** — `sms.py` สลับ console/Twilio ด้วย env ตัวเดียว ไม่ต้องแก้โค้ด
11. **Feature flag** — Quick Login เปิด/ปิดด้วย `ENABLE_QUICK_LOGIN`
12. **ทดสอบอัตโนมัติด้วยเบราว์เซอร์จริง** — `test_ui.py` (Playwright) คลิก 19 จุด ยืนยันใช้งานได้จริง

---

## 4. สถาปัตยกรรมรวม
```
            [ เบราว์เซอร์มือถือ/PC ]
              │  โหลดหน้า (HTML)   │  fetch JSON
              ▼                    ▼
┌──────────────── Flask ────────────────────┐
│  app.py   = เสิร์ฟหน้า (render_template)    │
│             + ตรวจ session ก่อนเข้าหน้า      │
│  api.py   = REST API ทั้งหมด (/api/...)     │
│             ทุก endpoint: ตรวจ→query→ตอบ    │
│  helpers/constants/sms/promptpay = ตัวช่วย  │
└──────────────│─────────────────────────────┘
               ▼ SQLAlchemy
          [ SQLite: instance/dev.db ]
   external (ฝั่งเบราว์เซอร์): Leaflet tiles, Nominatim
```

## 5. Flow ฝั่ง Frontend (เกิดอะไรขึ้นเมื่อเปิดหน้า)
1. เบราว์เซอร์ขอหน้า เช่น `/search` → Flask `app.py` เช็ค session (ไม่ล็อกอิน → redirect `/login`)
2. Flask เรนเดอร์ `search.html` (สืบทอด `base.html`) ส่ง HTML กลับ
3. `base.html` ฝัง `window.CONFIG` (ค่ากลางจาก Python) + โหลด `app.js`
4. JS ของหน้านั้น (`{% block script %}`) เรียก `API.get("/markets?...")`
5. ได้ JSON → สร้าง element ด้วย DOM → ใส่อนิเมชั่น (CSS class)

## 6. Flow ฝั่ง Backend (ทุก API ทำเหมือนกัน)
```
Request → route ใน api.py
  1) request.get_json()           อ่านข้อมูล
  2) ตรวจความถูกต้อง (valid_phone ฯลฯ)  ──ผิด──► fail("ข้อความ", 400)
  3) เช็คสิทธิ์ (@login_required / session role)
  4) คุย DB ผ่าน SQLAlchemy (+ commit)
  5) ตอบ ok({...})  รูปแบบเดียวกันทุกตัว
```

## 7. Flow ตัวอย่าง end-to-end: "จองล็อก"
```
สมัคร  → POST /api/auth/register : บันทึก User + OTP(hash) + ส่ง SMS
ยืนยัน → POST /api/auth/otp/verify : เทียบ hash → ตั้ง session (login)
ค้นหา  → GET  /api/markets          → การ์ดตลาด
จอง    → POST /api/bookings          → Booking(PENDING) + คำนวณมัดจำ 20%
จ่าย   → GET  /api/payments/<id>/qr.png  → รูป QR PromptPay
ยืนยัน → POST /api/payments/<id>/confirm
        └ commit เดียว: Payment=PAID + Booking=CONFIRMED
                        + Lot=BOOKED + Notification
สำเร็จ → หน้า /confirm
```

## 8. โครงสร้างไฟล์ (อ่านง่าย ดูแลเอง)
```
app.py        เสิร์ฟหน้า + ตั้งค่า + ส่ง config เข้า template
api.py        API ทั้งหมด (~26 endpoint)
models.py     9 ตาราง (User, Market, Lot, Booking, Payment, Review, Message, Notification, OtpCode)
constants.py  ค่ากลาง (กัน mismatch)
helpers.py    ok()/fail() + auth decorator + OTP
sms.py        ส่ง SMS (console/twilio)
promptpay.py  สร้าง QR payload (EMVCo + CRC16)
seed.py       ข้อมูลตัวอย่าง
templates/    19 หน้า HTML (base.html = แม่แบบ, _bottomnav/_appheader/_quicklogin = ชิ้นส่วนใช้ซ้ำ)
static/css/styles.css   ดีไซน์ + อนิเมชั่น
static/js/app.js        ตัวช่วยกลาง (API client + helper)
test_ui.py    ทดสอบคลิกอัตโนมัติ (Playwright)
```

## 9. โมเดลข้อมูล (ความสัมพันธ์)
```
User ─< Market ─< Lot ─< Booking ─ Payment
User ─< Booking (ผู้ขายที่จอง)
User: เป็นได้ทั้ง SELLER / MARKET_OWNER / ADMIN
Review/Message/Notification/OtpCode = ตารางเสริม
```

## 10. ความปลอดภัย (สรุป)
- รหัสผ่าน/OTP ไม่เก็บดิบ (OTP = HMAC-SHA256)
- session cookie เซ็นชื่อด้วย SECRET_KEY (ปลอมไม่ได้)
- ตรวจสิทธิ์ทุก API (login/admin/เจ้าของข้อมูล)
- รหัสแอดมินอยู่ใน env (ไม่ hardcode)
- ลบข้อมูลเชิงสัมพันธ์ครบ (ไม่เหลือขยะ)
