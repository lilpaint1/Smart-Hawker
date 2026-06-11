"""ใส่ข้อมูลตัวอย่าง: python seed.py"""
from app import app
from extensions import db
from models import User, Market, Lot

MARKETS = [
    ("ตลาดนัดจตุจักร", "กรุงเทพมหานคร", "จตุจักร", 13.7999, 100.5503, 95,
     "ตลาดนัดสุดสัปดาห์ที่ใหญ่ที่สุด นักท่องเที่ยวเยอะ"),
    ("ตลาดนัดรถไฟ ศรีนครินทร์", "กรุงเทพมหานคร", "ประเวศ", 13.6878, 100.6479, 88,
     "ตลาดกลางคืน บรรยากาศวินเทจ คนเดินเยอะช่วงเย็น"),
    ("ตลาดคลองเตย", "กรุงเทพมหานคร", "คลองเตย", 13.7146, 100.5663, 76,
     "ตลาดสดขายส่ง เปิดเช้ามืด ค่าเช่าย่อมเยา"),
    ("ตลาดอมรพันธ์", "กรุงเทพมหานคร", "ลาดพร้าว", 13.8155, 100.6011, 70,
     "ตลาดชุมชน ลูกค้าประจำเยอะ เหมาะขายอาหารตามสั่ง"),
    ("ตลาดประชานิเวศน์ 1", "นนทบุรี", "เมืองนนทบุรี", 13.8412, 100.5375, 65,
     "ตลาดเช้า-เย็น ทำเลดีติดถนนใหญ่"),
]
RENT_TYPES = ["DAILY", "WEEKLY", "MONTHLY"]

with app.app_context():
    db.drop_all()
    db.create_all()

    owner = User(role="MARKET_OWNER", name="คุณวิชัย เจ้าของตลาด",
                 phone="0900000001", email="owner@smarthawker.test")
    seller = User(role="SELLER", name="สมหญิง ใจดี", phone="0812345678",
                  shop_name="ร้านส้มตำเจ๊หญิง", product_type="อาหารอีสาน",
                  bio="ส้มตำ ไก่ย่าง ข้าวเหนียว สดใหม่ทุกวัน")
    db.session.add_all([owner, seller])
    db.session.commit()

    for name, prov, dist, lat, lng, pop, desc in MARKETS:
        m = Market(owner_id=owner.id, name=name, description=desc, province=prov,
                   district=dist, lat=lat, lng=lng, popularity=pop)
        db.session.add(m)
        db.session.flush()
        for i in range(6):
            db.session.add(Lot(
                market_id=m.id,
                code=f"{chr(65 + i // 3)}{i % 3 + 1}",
                price_per_day=80 + i * 40 + (pop // 10) * 10,
                rent_type=RENT_TYPES[i % 3],
                status="BOOKED" if i == 2 else "AVAILABLE",
                note="ทำเลหน้าตลาด คนเดินผ่านเยอะ" if i == 0 else None,
            ))
    db.session.commit()
    print(f"[OK] seed done: {len(MARKETS)} markets")
