"""ตัวช่วยกลาง: รูปแบบ response เดียวกัน + auth + OTP + ตรวจข้อมูล (กัน mismatch/โค้ดซ้ำ)"""
import os
import re
import hmac
import hashlib
import random
from functools import wraps
from datetime import datetime, timedelta
from flask import jsonify, session
from models import User


# ---------- response รูปแบบเดียวกันทุก API ----------
def ok(data=None, **kw):
    payload = {"ok": True}
    if data:
        payload.update(data)
    payload.update(kw)
    return jsonify(payload)


def fail(error, code=400):
    return jsonify({"ok": False, "error": error}), code


# ---------- auth ----------
def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return fail("กรุณาเข้าสู่ระบบ", 401)
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "ADMIN":
            return fail("เฉพาะผู้ดูแลระบบ", 403)
        return fn(*args, **kwargs)
    return wrapper


# ---------- OTP ----------
def gen_otp():
    return f"{random.randint(0, 999999):06d}"


def hash_otp(phone, code):
    secret = os.environ.get("SECRET_KEY", "dev-secret")
    return hmac.new(secret.encode(), f"{phone}:{code}".encode(),
                    hashlib.sha256).hexdigest()


def otp_expiry(minutes=5):
    return datetime.utcnow() + timedelta(minutes=minutes)


# ---------- validation ----------
def valid_phone(phone):
    return bool(re.fullmatch(r"0\d{9}", (phone or "").strip()))


def deposit_for(price_per_day):
    return max(50, round(price_per_day * 0.2))
