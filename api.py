"""API ทั้งหมดอยู่ที่นี่ (Blueprint /api). ทุก endpoint ทำตามแพทเทิร์นเดียวกัน:
   รับ JSON -> ตรวจข้อมูล -> เช็คสิทธิ์ -> คุย DB -> ตอบ ok()/fail()
"""
import os
import random
from io import BytesIO
from datetime import datetime
import qrcode
from flask import Blueprint, request, session, send_file

from extensions import db
from models import (User, Market, Lot, Booking, Payment, Review,
                    Message, Notification, OtpCode)
from constants import RENT_TYPES
from helpers import (ok, fail, current_user, login_required, admin_required,
                     gen_otp, hash_otp, otp_expiry, valid_phone, deposit_for)
from sms import send_sms
from promptpay import generate_payload

api = Blueprint("api", __name__, url_prefix="/api")


# ============ ตัวช่วยแปลง model -> dict ============
def user_full(u):
    return {"id": u.id, "name": u.name, "phone": u.phone, "role": u.role,
            "shopName": u.shop_name, "productType": u.product_type, "bio": u.bio}


def lot_dto(l):
    return {"id": l.id, "code": l.code, "pricePerDay": l.price_per_day,
            "rentType": l.rent_type, "status": l.status, "note": l.note}


def market_item(m):
    avail = [l for l in m.lots if l.status == "AVAILABLE"]
    prices = [l.price_per_day for l in avail]
    return {"id": m.id, "name": m.name, "province": m.province,
            "district": m.district, "lat": m.lat, "lng": m.lng,
            "popularity": m.popularity,
            "minPrice": min(prices) if prices else None,
            "availableLots": len(avail), "totalLots": len(m.lots)}


def is_console_sms():
    return os.environ.get("SMS_PROVIDER", "console") == "console"


# ============ AUTH ============
@api.post("/auth/register")
def register():
    d = request.get_json(silent=True) or {}
    name, phone = (d.get("name") or "").strip(), (d.get("phone") or "").strip()
    role, email = d.get("role"), (d.get("email") or "").strip()
    if len(name) < 2:
        return fail("กรุณากรอกชื่อ")
    if not valid_phone(phone):
        return fail("เบอร์โทรต้องเป็นตัวเลข 10 หลัก")
    if role not in ("SELLER", "MARKET_OWNER"):
        return fail("กรุณาเลือกประเภทผู้ใช้")
    if User.query.filter_by(phone=phone).first():
        return fail("เบอร์นี้สมัครแล้ว กรุณาเข้าสู่ระบบ", 409)

    db.session.add(User(name=name, phone=phone, email=email or None, role=role))
    code = gen_otp()
    db.session.add(OtpCode(phone=phone, code_hash=hash_otp(phone, code),
                           expires_at=otp_expiry()))
    db.session.commit()
    send_sms(phone, f"Smart Hawker: รหัสยืนยัน OTP คือ {code} (หมดอายุ 5 นาที)")
    return ok({"phone": phone, "dev": code if is_console_sms() else None})


@api.post("/auth/otp/request")
def otp_request():
    d = request.get_json(silent=True) or {}
    phone = (d.get("phone") or "").strip()
    if not valid_phone(phone):
        return fail("เบอร์โทรไม่ถูกต้อง")
    if not User.query.filter_by(phone=phone).first():
        return fail("ไม่พบเบอร์นี้ในระบบ กรุณาสมัครก่อน", 404)
    code = gen_otp()
    db.session.add(OtpCode(phone=phone, code_hash=hash_otp(phone, code),
                           expires_at=otp_expiry()))
    db.session.commit()
    send_sms(phone, f"Smart Hawker: รหัสเข้าสู่ระบบ OTP คือ {code} (หมดอายุ 5 นาที)")
    return ok({"phone": phone, "dev": code if is_console_sms() else None})


@api.post("/auth/otp/verify")
def otp_verify():
    d = request.get_json(silent=True) or {}
    phone, code = (d.get("phone") or "").strip(), (d.get("code") or "").strip()
    otp = (OtpCode.query
           .filter_by(phone=phone, consumed=False)
           .filter(OtpCode.expires_at > datetime.utcnow())
           .order_by(OtpCode.created_at.desc()).first())
    if not otp or otp.code_hash != hash_otp(phone, code):
        return fail("รหัส OTP ไม่ถูกต้องหรือหมดอายุ", 401)
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return fail("ไม่พบผู้ใช้", 404)
    otp.consumed = True
    db.session.commit()
    session.clear()
    session["user_id"], session["role"], session["name"] = user.id, user.role, user.name
    return ok({"role": user.role})


@api.post("/auth/admin")
def admin_login():
    d = request.get_json(silent=True) or {}
    if (d.get("code") or "") != os.environ.get("ADMIN_CODE", "ake112233"):
        return fail("รหัสแอดมินไม่ถูกต้อง", 401)
    session.clear()
    session["role"], session["name"] = "ADMIN", "ผู้ดูแลระบบ"
    return ok({"role": "ADMIN"})


@api.post("/auth/quick")
def quick_login():
    """PROTOTYPE: เข้าระบบไวไม่ต้อง OTP (ปิดด้วย ENABLE_QUICK_LOGIN=0)"""
    if os.environ.get("ENABLE_QUICK_LOGIN", "1") == "0":
        return fail("quick login ถูกปิดอยู่", 403)
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip() or "ผู้ทดลอง"
    role = d.get("role")
    if role not in ("SELLER", "MARKET_OWNER"):
        return fail("เลือกบทบาทไม่ถูกต้อง")
    phone = "09" + f"{random.randint(0, 99999999):08d}"
    while User.query.filter_by(phone=phone).first():
        phone = "09" + f"{random.randint(0, 99999999):08d}"
    u = User(name=name, phone=phone, role=role, bio="(บัญชีทดลอง prototype)")
    db.session.add(u)
    db.session.commit()
    session.clear()
    session["user_id"], session["role"], session["name"] = u.id, u.role, u.name
    return ok({"role": u.role})


@api.post("/auth/logout")
def logout():
    session.clear()
    return ok()


@api.get("/me")
def me():
    uid, role = session.get("user_id"), session.get("role")
    if not role:
        return ok({"session": None, "user": None})
    u = current_user()
    return ok({"session": {"userId": uid, "role": role, "name": session.get("name")},
               "user": user_full(u) if u else None})


# ============ MARKETS / LOTS ============
@api.get("/markets")
def markets_list():
    q = (request.args.get("q") or "").strip()
    province = (request.args.get("province") or "").strip()
    rent_type = request.args.get("rentType") or ""
    max_price = request.args.get("maxPrice", type=float)

    query = Market.query
    if province:
        query = query.filter(Market.province.contains(province))
    if q:
        query = query.filter(Market.name.contains(q))
    markets = query.order_by(Market.popularity.desc()).all()

    items = []
    for m in markets:
        matching = [l for l in m.lots
                    if (max_price is None or l.price_per_day <= max_price)
                    and (not rent_type or l.rent_type == rent_type)]
        if (max_price is not None or rent_type) and not matching:
            continue
        items.append(market_item(m))
    return ok({"markets": items})


@api.post("/markets")
@login_required
def market_create():
    if session.get("role") != "MARKET_OWNER":
        return fail("เฉพาะเจ้าของตลาด", 403)
    d = request.get_json(silent=True) or {}
    if len((d.get("name") or "").strip()) < 2:
        return fail("กรุณากรอกชื่อตลาด")
    if not d.get("province"):
        return fail("กรุณาระบุจังหวัด")
    try:
        lat, lng = float(d["lat"]), float(d["lng"])
    except (KeyError, TypeError, ValueError):
        return fail("กรุณาปักหมุดตำแหน่งบนแผนที่")
    m = Market(owner_id=session["user_id"], name=d["name"].strip(),
               description=(d.get("description") or "").strip() or None,
               province=d["province"].strip(),
               district=(d.get("district") or "").strip() or None,
               lat=lat, lng=lng)
    db.session.add(m)
    db.session.commit()
    return ok({"marketId": m.id})


@api.get("/markets/<mid>")
def market_detail(mid):
    m = Market.query.get(mid)
    if not m:
        return fail("ไม่พบตลาด", 404)
    item = market_item(m)
    item.update({"description": m.description, "ownerId": m.owner_id,
                 "ownerName": m.owner.name,
                 "lots": [lot_dto(l) for l in sorted(m.lots, key=lambda x: x.code)]})
    return ok({"market": item})


@api.delete("/markets/<mid>")
@login_required
def market_delete(mid):
    m = Market.query.get(mid)
    if not m:
        return fail("ไม่พบตลาด", 404)
    if session.get("role") != "ADMIN" and m.owner_id != session.get("user_id"):
        return fail("ไม่มีสิทธิ์", 403)
    db.session.delete(m)   # cascade ลบ lots/bookings/payments
    Review.query.filter_by(target_type="MARKET", target_id=mid).delete()
    db.session.commit()
    return ok({"deleted": True})


@api.get("/owner/markets")
@login_required
def owner_markets():
    ms = (Market.query.filter_by(owner_id=session["user_id"])
          .order_by(Market.created_at.desc()).all())
    out = []
    for m in ms:
        out.append({
            "id": m.id, "name": m.name, "province": m.province, "district": m.district,
            "totalLots": len(m.lots),
            "availableLots": sum(1 for l in m.lots if l.status == "AVAILABLE"),
            "bookings": sum(len(l.bookings) for l in m.lots),
            "lots": [lot_dto(l) for l in m.lots],
        })
    return ok({"markets": out})


@api.get("/lots/<lid>")
def lot_get(lid):
    l = Lot.query.get(lid)
    if not l:
        return fail("ไม่พบล็อก", 404)
    return ok({"lot": {**lot_dto(l), "marketId": l.market.id,
                       "marketName": l.market.name,
                       "deposit": deposit_for(l.price_per_day)}})


@api.post("/lots")
@login_required
def lot_create():
    d = request.get_json(silent=True) or {}
    m = Market.query.get(d.get("marketId"))
    if not m or m.owner_id != session.get("user_id"):
        return fail("ไม่มีสิทธิ์เพิ่มล็อกในตลาดนี้", 403)
    if not (d.get("code") or "").strip():
        return fail("กรุณากรอกเลขล็อก")
    if d.get("rentType") not in RENT_TYPES:
        return fail("ประเภทเช่าไม่ถูกต้อง")
    try:
        price = float(d["pricePerDay"])
    except (KeyError, TypeError, ValueError):
        return fail("ราคาไม่ถูกต้อง")
    l = Lot(market_id=m.id, code=d["code"].strip(), price_per_day=price,
            rent_type=d["rentType"], note=(d.get("note") or "").strip() or None)
    db.session.add(l)
    db.session.commit()
    return ok({"lotId": l.id})


@api.patch("/lots/<lid>")
@login_required
def lot_toggle(lid):
    l = Lot.query.get(lid)
    if not l or l.market.owner_id != session.get("user_id"):
        return fail("ไม่มีสิทธิ์", 403)
    l.status = "AVAILABLE" if l.status == "CLOSED" else "CLOSED"
    db.session.commit()
    return ok({"status": l.status})


@api.delete("/lots/<lid>")
@login_required
def lot_delete(lid):
    l = Lot.query.get(lid)
    if not l or l.market.owner_id != session.get("user_id"):
        return fail("ไม่มีสิทธิ์", 403)
    db.session.delete(l)
    db.session.commit()
    return ok({"deleted": True})


# ============ BOOKINGS / PAYMENTS ============
@api.post("/bookings")
@login_required
def booking_create():
    d = request.get_json(silent=True) or {}
    l = Lot.query.get(d.get("lotId"))
    if not l:
        return fail("ไม่พบล็อก", 404)
    if l.status != "AVAILABLE":
        return fail("ล็อกนี้ไม่ว่าง", 409)
    try:
        date = datetime.fromisoformat(d["date"])
    except (KeyError, TypeError, ValueError):
        return fail("กรุณาเลือกวันที่")
    dep = deposit_for(l.price_per_day)
    b = Booking(lot_id=l.id, seller_id=session["user_id"], date=date, deposit_amount=dep)
    db.session.add(b)
    db.session.commit()
    return ok({"bookingId": b.id, "depositAmount": dep})


@api.get("/bookings")
@login_required
def bookings_mine():
    bs = (Booking.query.filter_by(seller_id=session["user_id"])
          .order_by(Booking.created_at.desc()).all())
    return ok({"bookings": [{
        "id": b.id, "date": b.date.isoformat(), "status": b.status,
        "paymentStatus": b.payment_status, "depositAmount": b.deposit_amount,
        "lotCode": b.lot.code, "marketName": b.lot.market.name,
        "marketId": b.lot.market.id} for b in bs]})


@api.get("/bookings/<bid>")
@login_required
def booking_get(bid):
    b = Booking.query.get(bid)
    if not b or b.seller_id != session.get("user_id"):
        return fail("ไม่พบการจอง", 404)
    return ok({"booking": {
        "id": b.id, "date": b.date.isoformat(), "status": b.status,
        "paymentStatus": b.payment_status, "depositAmount": b.deposit_amount,
        "lotCode": b.lot.code, "pricePerDay": b.lot.price_per_day,
        "marketName": b.lot.market.name, "marketId": b.lot.market.id,
        "qrPayload": b.payment.qr_payload if b.payment else None}})


@api.post("/payments/<bid>/promptpay")
@login_required
def payment_promptpay(bid):
    b = Booking.query.get(bid)
    if not b or b.seller_id != session.get("user_id"):
        return fail("ไม่พบการจอง", 404)
    payload = generate_payload(os.environ.get("PROMPTPAY_ID", "0812345678"),
                               b.deposit_amount)
    if not b.payment:
        db.session.add(Payment(booking_id=b.id, amount=b.deposit_amount,
                               method="PROMPTPAY", status="PENDING", qr_payload=payload))
    else:
        b.payment.qr_payload = payload
    db.session.commit()
    return ok({"qrPayload": payload, "amount": b.deposit_amount})


@api.get("/payments/<bid>/qr.png")
@login_required
def payment_qr(bid):
    b = Booking.query.get(bid)
    if not b or b.seller_id != session.get("user_id"):
        return fail("ไม่พบการจอง", 404)
    payload = generate_payload(os.environ.get("PROMPTPAY_ID", "0812345678"),
                               b.deposit_amount)
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@api.post("/payments/<bid>/confirm")
@login_required
def payment_confirm(bid):
    b = Booking.query.get(bid)
    if not b or b.seller_id != session.get("user_id"):
        return fail("ไม่พบการจอง", 404)
    if not b.payment:
        db.session.add(Payment(booking_id=b.id, amount=b.deposit_amount,
                               method="PROMPTPAY", status="PAID",
                               ref=f"MOCK-{int(datetime.utcnow().timestamp())}"))
    else:
        b.payment.status = "PAID"
        b.payment.ref = f"MOCK-{int(datetime.utcnow().timestamp())}"
    b.status, b.payment_status, b.lot.status = "CONFIRMED", "PAID", "BOOKED"
    db.session.add(Notification(user_id=b.seller_id, type="BOOKING_CONFIRMED",
                                title="จองสำเร็จ ✅",
                                body=f"จองล็อก {b.lot.code} ที่ {b.lot.market.name} เรียบร้อย"))
    db.session.commit()
    return ok({"confirmed": True})


# ============ PROFILE / REVIEWS ============
@api.post("/profile")
@login_required
def profile_update():
    d = request.get_json(silent=True) or {}
    u = current_user()
    if "name" in d and (d["name"] or "").strip():
        u.name = d["name"].strip()
    u.shop_name = (d.get("shopName") or "").strip() or None
    u.product_type = (d.get("productType") or "").strip() or None
    u.bio = (d.get("bio") or "").strip() or None
    db.session.commit()
    return ok({"user": user_full(u)})


@api.get("/reviews")
def reviews_list():
    tt, tid = request.args.get("targetType"), request.args.get("targetId")
    if not tt or not tid:
        return fail("ต้องระบุ target")
    rs = (Review.query.filter_by(target_type=tt, target_id=tid)
          .order_by(Review.created_at.desc()).all())
    avg = sum(r.rating for r in rs) / len(rs) if rs else None
    return ok({"average": avg, "count": len(rs),
               "reviews": [{"id": r.id, "rating": r.rating, "comment": r.comment,
                            "fromName": r.from_user.name} for r in rs]})


@api.post("/reviews")
@login_required
def review_create():
    d = request.get_json(silent=True) or {}
    if d.get("targetType") not in ("MARKET", "SELLER") or not d.get("targetId"):
        return fail("ข้อมูลไม่ครบ")
    rating = int(d.get("rating") or 0)
    if not 1 <= rating <= 5:
        return fail("กรุณาให้คะแนน 1-5")
    db.session.add(Review(from_user_id=session["user_id"], target_type=d["targetType"],
                          target_id=d["targetId"], rating=rating,
                          comment=(d.get("comment") or "").strip() or None))
    db.session.commit()
    return ok()


# ============ MESSAGES / USERS ============
def thread_id_for(a, b):
    return "__".join(sorted([a, b]))


@api.get("/messages")
@login_required
def messages_get():
    me_id = session["user_id"]
    tid = request.args.get("threadId")
    if tid:
        if me_id not in tid.split("__"):
            return fail("ไม่มีสิทธิ์", 403)
        msgs = Message.query.filter_by(thread_id=tid).order_by(Message.created_at).all()
        return ok({"messages": [{"id": m.id, "body": m.body, "imageUrl": m.image_url,
                                 "mine": m.from_user_id == me_id,
                                 "createdAt": m.created_at.isoformat()} for m in msgs]})
    # รายการห้องแชท
    all_msgs = (Message.query
                .filter((Message.from_user_id == me_id) | (Message.to_user_id == me_id))
                .order_by(Message.created_at.desc()).all())
    seen, threads = set(), []
    for m in all_msgs:
        if m.thread_id in seen:
            continue
        seen.add(m.thread_id)
        other = m.to_user if m.from_user_id == me_id else m.from_user
        threads.append({"threadId": m.thread_id, "otherId": other.id,
                        "otherName": other.name, "lastBody": m.body})
    return ok({"threads": threads})


@api.post("/messages")
@login_required
def message_send():
    d = request.get_json(silent=True) or {}
    me_id, to_id = session["user_id"], d.get("toUserId")
    body = (d.get("body") or "").strip()
    if not to_id or not body:
        return fail("ข้อมูลไม่ครบ")
    tid = thread_id_for(me_id, to_id)
    db.session.add(Message(thread_id=tid, from_user_id=me_id, to_user_id=to_id, body=body))
    db.session.add(Notification(user_id=to_id, type="MESSAGE", title="ข้อความใหม่",
                                body=body[:60]))
    db.session.commit()
    return ok({"threadId": tid})


@api.get("/users/<uid>")
@login_required
def user_public(uid):
    u = User.query.get(uid)
    if not u:
        return fail("ไม่พบผู้ใช้", 404)
    return ok({"user": {"id": u.id, "name": u.name, "role": u.role,
                        "shopName": u.shop_name}})


# ============ NOTIFICATIONS ============
@api.get("/notifications")
@login_required
def notifications_list():
    ns = (Notification.query.filter_by(user_id=session["user_id"])
          .order_by(Notification.created_at.desc()).limit(50).all())
    unread = sum(1 for n in ns if not n.read)
    return ok({"unread": unread, "notifications": [
        {"id": n.id, "type": n.type, "title": n.title, "body": n.body,
         "read": n.read, "createdAt": n.created_at.isoformat()} for n in ns]})


@api.post("/notifications")
@login_required
def notifications_read():
    Notification.query.filter_by(user_id=session["user_id"], read=False).update({"read": True})
    db.session.commit()
    return ok()


# ============ ADMIN ============
@api.get("/admin/stats")
@admin_required
def admin_stats():
    paid = db.session.query(db.func.sum(Payment.amount)).filter_by(status="PAID").scalar() or 0
    recent = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    return ok({"stats": {
        "sellers": User.query.filter_by(role="SELLER").count(),
        "owners": User.query.filter_by(role="MARKET_OWNER").count(),
        "markets": Market.query.count(), "lots": Lot.query.count(),
        "bookings": Booking.query.count(), "revenue": paid},
        "recent": [{"id": b.id, "seller": b.seller.name, "market": b.lot.market.name,
                    "lot": b.lot.code, "status": b.status,
                    "amount": b.deposit_amount} for b in recent]})


@api.get("/admin/users")
@admin_required
def admin_users_list():
    us = User.query.order_by(User.created_at.desc()).all()
    return ok({"users": [{"id": u.id, "name": u.name, "phone": u.phone, "role": u.role,
                          "markets": len(u.markets), "bookings": len(u.bookings)} for u in us]})


@api.post("/admin/users")
@admin_required
def admin_user_create():
    d = request.get_json(silent=True) or {}
    name, phone, role = (d.get("name") or "").strip(), (d.get("phone") or "").strip(), d.get("role")
    if len(name) < 2 or not valid_phone(phone) or role not in ("SELLER", "MARKET_OWNER"):
        return fail("ข้อมูลไม่ถูกต้อง")
    if User.query.filter_by(phone=phone).first():
        return fail("เบอร์นี้มีอยู่แล้ว", 409)
    u = User(name=name, phone=phone, role=role)
    db.session.add(u)
    db.session.commit()
    return ok({"id": u.id})


@api.delete("/admin/users/<uid>")
@admin_required
def admin_user_delete(uid):
    u = User.query.get(uid)
    if not u:
        return fail("ไม่พบผู้ใช้", 404)
    # ลบข้อมูลที่เกี่ยวข้อง
    for m in list(u.markets):
        db.session.delete(m)  # cascade
    Booking.query.filter_by(seller_id=uid).delete()
    Review.query.filter_by(from_user_id=uid).delete()
    Message.query.filter((Message.from_user_id == uid) | (Message.to_user_id == uid)).delete()
    Notification.query.filter_by(user_id=uid).delete()
    OtpCode.query.filter_by(phone=u.phone).delete()
    db.session.delete(u)
    db.session.commit()
    return ok({"deleted": True})
