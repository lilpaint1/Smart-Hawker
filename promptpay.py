"""สร้าง PromptPay QR payload (มาตรฐาน EMVCo ของไทย) — ขึ้นต้นด้วย 00020101..."""


def _tlv(tag, value):
    return f"{tag}{len(value):02d}{value}"


def _crc16(data):
    crc = 0xFFFF
    for ch in data.encode("ascii"):
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def generate_payload(mobile, amount=None):
    # เบอร์ -> 0066 + เลข 9 หลัก (ตัด 0 หน้า)
    digits = "".join(c for c in mobile if c.isdigit())
    if digits.startswith("0"):
        digits = digits[1:]
    target = "0066" + digits

    merchant = _tlv("00", "A000000677010111") + _tlv("01", target)
    payload = (
        _tlv("00", "01")
        + _tlv("01", "12" if amount else "11")
        + _tlv("29", merchant)
        + _tlv("53", "764")  # THB
    )
    if amount:
        payload += _tlv("54", f"{float(amount):.2f}")
    payload += _tlv("58", "TH")
    payload += "6304"  # CRC tag+len
    return payload + _crc16(payload)
