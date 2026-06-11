"""Smart Hawker — Flask app (จุดเริ่มต้น)
รัน local:  python app.py   (หรือ flask run)
"""
import os
import sys
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for

# Windows console เป็น cp1252 พิมพ์ไทย/emoji ไม่ได้ -> บังคับ UTF-8 (กัน crash ตอน print OTP)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

load_dotenv()

from extensions import db
from constants import CLIENT_CONFIG, ROLE_LABEL
from helpers import current_user
from api import api  # blueprint รวม API ทั้งหมด


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    db_url = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()

    # ส่งค่ากลางเข้า template ทุกหน้า (ให้ JS ใช้ค่าเดียวกัน -> กัน mismatch)
    @app.context_processor
    def inject_globals():
        me = current_user()
        return {
            "client_config": CLIENT_CONFIG,
            "me": me,
            "session_role": session.get("role"),
            "role_label": ROLE_LABEL,
            "app_name": os.environ.get("APP_NAME", "Smart Hawker"),
            "enable_quick_login": os.environ.get("ENABLE_QUICK_LOGIN", "1") != "0",
        }

    register_pages(app)
    return app


# ----- ตัวช่วยป้องกันหน้า (redirect ไป login ถ้ายังไม่เข้าระบบ) -----
def page_login_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        return fn(*a, **k)
    return wrapper


def page_admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if session.get("role") != "ADMIN":
            return redirect(url_for("admin_login_page"))
        return fn(*a, **k)
    return wrapper


def register_pages(app):
    # ----- หน้าสาธารณะ -----
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/admin/login")
    def admin_login_page():
        return render_template("admin_login.html")

    # ----- หน้าที่ต้องเข้าระบบ -----
    @app.route("/search")
    @page_login_required
    def search_page():
        return render_template("search.html")

    @app.route("/map")
    @page_login_required
    def map_page():
        return render_template("map.html")

    @app.route("/market/<mid>")
    @page_login_required
    def market_page(mid):
        return render_template("market.html", market_id=mid)

    @app.route("/book/<lot_id>")
    @page_login_required
    def book_page(lot_id):
        return render_template("book.html", lot_id=lot_id)

    @app.route("/checkout/<booking_id>")
    @page_login_required
    def checkout_page(booking_id):
        return render_template("checkout.html", booking_id=booking_id)

    @app.route("/confirm/<booking_id>")
    @page_login_required
    def confirm_page(booking_id):
        return render_template("confirm.html", booking_id=booking_id)

    @app.route("/bookings")
    @page_login_required
    def bookings_page():
        return render_template("bookings.html")

    @app.route("/chat")
    @page_login_required
    def chat_page():
        return render_template("chat.html")

    @app.route("/chat/<user_id>")
    @page_login_required
    def chat_thread_page(user_id):
        return render_template("chat_thread.html", other_id=user_id)

    @app.route("/profile")
    @page_login_required
    def profile_page():
        return render_template("profile.html")

    @app.route("/notifications")
    @page_login_required
    def notifications_page():
        return render_template("notifications.html")

    @app.route("/owner")
    @page_login_required
    def owner_page():
        return render_template("owner.html")

    # ----- หน้าแอดมิน -----
    @app.route("/admin")
    @page_admin_required
    def admin_page():
        return render_template("admin.html")

    @app.route("/admin/users")
    @page_admin_required
    def admin_users_page():
        return render_template("admin_users.html")


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
