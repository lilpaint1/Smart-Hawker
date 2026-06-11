"""โครงสร้างฐานข้อมูล (9 ตาราง) ด้วย SQLAlchemy
หมายเหตุ: ใช้ String สำหรับ role/status + ตรวจค่าด้วย constants.py (กัน mismatch)
"""
import uuid
from datetime import datetime
from extensions import db


def new_id():
    """สร้าง id แบบสุ่ม (เหมือน cuid)"""
    return uuid.uuid4().hex


class User(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    role = db.Column(db.String, nullable=False)        # SELLER | MARKET_OWNER | ADMIN
    phone = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)
    name = db.Column(db.String, nullable=False)
    avatar_url = db.Column(db.String)
    # โปรไฟล์ผู้ขาย
    shop_name = db.Column(db.String)
    product_type = db.Column(db.String)
    bio = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Market(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    owner_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    province = db.Column(db.String, nullable=False)
    district = db.Column(db.String)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    cover_photo_url = db.Column(db.String)
    popularity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.relationship("User", backref="markets")
    lots = db.relationship("Lot", backref="market", cascade="all, delete-orphan")


class Lot(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    market_id = db.Column(db.String, db.ForeignKey("market.id"), nullable=False)
    code = db.Column(db.String, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    rent_type = db.Column(db.String, nullable=False)   # DAILY | WEEKLY | MONTHLY
    status = db.Column(db.String, default="AVAILABLE")  # AVAILABLE | BOOKED | CLOSED
    note = db.Column(db.String)
    bookings = db.relationship("Booking", backref="lot", cascade="all, delete-orphan")


class Booking(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    lot_id = db.Column(db.String, db.ForeignKey("lot.id"), nullable=False)
    seller_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, default="PENDING")          # PENDING|CONFIRMED|CANCELLED
    deposit_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String, default="PENDING")  # PENDING|PAID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller = db.relationship("User", backref="bookings")
    payment = db.relationship("Payment", backref="booking", uselist=False,
                              cascade="all, delete-orphan")


class Payment(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    booking_id = db.Column(db.String, db.ForeignKey("booking.id"), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String)              # PROMPTPAY | CARD
    status = db.Column(db.String, default="PENDING")
    ref = db.Column(db.String)
    qr_payload = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    from_user_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    target_type = db.Column(db.String, nullable=False)   # MARKET | SELLER
    target_id = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    from_user = db.relationship("User")


class Message(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    thread_id = db.Column(db.String, nullable=False, index=True)
    from_user_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    to_user_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])


class Notification(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    user_id = db.Column(db.String, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String)
    title = db.Column(db.String)
    body = db.Column(db.String)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OtpCode(db.Model):
    id = db.Column(db.String, primary_key=True, default=new_id)
    phone = db.Column(db.String, nullable=False, index=True)
    code_hash = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    consumed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
