/* ===== ตัวช่วยกลางใช้ทุกหน้า ===== */

// API client เดียว — ทุก fetch ผ่านที่นี่ (รูปแบบ response เดียวกัน กัน mismatch)
const API = {
  async req(path, method = "GET", body) {
    const opt = { method, headers: {} };
    if (body) {
      opt.headers["Content-Type"] = "application/json";
      opt.body = JSON.stringify(body);
    }
    const res = await fetch("/api" + path, opt);
    try { return await res.json(); }
    catch { return { ok: false, error: "เซิร์ฟเวอร์ผิดพลาด" }; }
  },
  get(p) { return this.req(p); },
  post(p, b) { return this.req(p, "POST", b); },
  patch(p, b) { return this.req(p, "PATCH", b); },
  del(p) { return this.req(p, "DELETE"); },
};

// ค่ากลางจาก server (กัน mismatch — ค่าเดียวกับฝั่ง Python)
const C = window.CONFIG || {};
const ME = window.ME || null;

// DOM helpers
function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html != null) e.innerHTML = html;
  return e;
}
function $(sel) { return document.querySelector(sel); }
function esc(s) { const d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
function thb(n) { return "฿" + Number(n).toLocaleString("th-TH"); }
function fmtDate(iso) { return new Date(iso).toLocaleDateString("th-TH"); }
function qs(name) { return new URLSearchParams(location.search).get(name); }
function go(url) { location.href = url; }

const AVA = ["#3b5bf6", "#12b886", "#ff922b", "#e64980", "#7950f2", "#15aabf"];
function avaColor(i) { return AVA[i % AVA.length]; }

// ไอคอน Lucide (เรียกซ้ำได้หลังเพิ่ม element ใหม่)
function icons() { if (window.lucide) window.lucide.createIcons(); }

// อัปเดต badge แดงกระดิ่งแจ้งเตือน
async function refreshBell() {
  const b = $("#bell-badge");
  if (!b) return;
  if (!ME || !ME.id) return;     // admin/ยังไม่ล็อกอิน ไม่มีแจ้งเตือน
  const d = await API.get("/notifications");
  const n = d.unread || 0;
  if (n > 0) { b.textContent = n > 9 ? "9+" : n; b.classList.remove("hide"); }
  else b.classList.add("hide");
}

document.addEventListener("DOMContentLoaded", () => {
  icons();
  refreshBell();
  setInterval(refreshBell, 8000);
});
