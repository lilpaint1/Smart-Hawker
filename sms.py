"""ส่ง SMS แบบสลับผู้ให้บริการด้วย env SMS_PROVIDER (console=dev ฟรี, twilio=จริง)"""
import os
import base64
import urllib.parse
import urllib.request


def send_sms(phone, text):
    provider = os.environ.get("SMS_PROVIDER", "console").lower()
    if provider == "twilio":
        return _send_twilio(phone, text)
    # dev: โชว์ใน terminal (ไม่เสียเงิน)
    print(f"\n[SMS -> {phone}] {text}\n")
    return {"ok": True, "provider": "console"}


def _send_twilio(phone, text):
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    sender = os.environ.get("TWILIO_FROM")
    if not (sid and token and sender):
        print(f"[sms] Twilio env ไม่ครบ -> fallback console: [{phone}] {text}")
        return {"ok": True, "provider": "console-fallback"}

    # เบอร์ไทย 0xxxxxxxxx -> +66xxxxxxxxx
    to = "+66" + phone[1:] if phone.startswith("0") else phone
    data = urllib.parse.urlencode({"To": to, "From": sender, "Body": text}).encode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"ok": resp.status < 300, "provider": "twilio"}
    except Exception as e:  # pragma: no cover
        return {"ok": False, "provider": "twilio", "error": str(e)}
