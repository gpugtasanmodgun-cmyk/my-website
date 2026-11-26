# -*- coding: utf-8 -*-
"""
MOCHI HOUSE — ตัวรับหน้าเว็บบน Render  (relay)

หน้าที่:
  • เปิดพอร์ตให้ Render เห็นตลอด + จุด /ping ให้ UptimeRobot ยิงปลุก
  • รับคำขอจากผู้เข้าเว็บ แล้วส่ง "ผ่านสะพาน" ไปให้บอท (kino.py) บนคอมคุณทำงานจริง
    (บอทเป็นฝ่ายต่อออกมาหา Render เอง → ไม่ต้องเปิดพอร์ต/ตั้งค่าเราเตอร์)
  • เตะคนที่กด F2 / F12 / Ctrl+U ... (หน้าเว็บส่งสัญญาณมาที่ /api/xmas/kick)
  • ถ้าบอทปิดอยู่: ยังเปิดหน้าเว็บเดิมจากแคชได้ ส่วนปุ่มที่ต้องใช้บอทจะแจ้งว่า "บอทออฟไลน์"

ตัวแปรสภาพแวดล้อม (ตั้งใน Render → Environment):
  BRIDGE_SECRET   รหัสลับของสะพาน (ต้องเหมือนกับ XMAS_BRIDGE_SECRET ในเครื่องคุณ)  ← จำเป็น
  KICK_MIN        นาทีที่แบนคนกด F2 (ค่าเริ่มต้น 10, ใส่ 0 = ปิดระบบเตะ)
  BRIDGE_TIMEOUT  วินาทีที่รอบอทตอบ (ค่าเริ่มต้น 25)
"""
import asyncio, hmac, itertools, json, os, struct, time
from aiohttp import web, WSMsgType
from multidict import CIMultiDict

SECRET = os.getenv("BRIDGE_SECRET", "").strip()
PORT = int(os.getenv("PORT", "10000"))
KICK_MIN = float(os.getenv("KICK_MIN", "10") or 0)
TIMEOUT = float(os.getenv("BRIDGE_TIMEOUT", "25"))
MAX_REQ = 30 * 1024 * 1024
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
       "transfer-encoding", "upgrade", "content-length", "host"}
DROP_IN = HOP | {"x-forwarded-for", "x-forwarded-host", "x-forwarded-proto", "x-real-ip", "forwarded",
                 "cf-connecting-ip", "true-client-ip", "accept-encoding"}
COMPRESS = {"text/html", "text/css", "text/plain", "application/json", "application/javascript", "text/javascript", "image/svg+xml"}

st = {"ws": None, "since": 0.0}
pending = {}
_ids = itertools.count(1)
cache = {}            # "GET /path?q" -> (เวลา, status, headers, body)
cache_bytes = [0]
CACHE_LIMIT = 120 * 1024 * 1024
kicked = {}
hits = {}

KICK_HTML = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>🚫 ถูกเตะออก</title>"
             "<body style='margin:0;min-height:100vh;display:grid;place-items:center;background:#150A30;color:#FFE0F4;font:600 20px/1.6 system-ui,sans-serif;text-align:center;padding:24px'>"
             "<div><div style='font-size:56px'>🚫</div>ตรวจพบการเปิดดูข้อมูลเว็บ (F2 / F12)<br><span style='font-weight:400;font-size:15px;opacity:.8'>คุณถูกเตะออกจากเว็บชั่วคราว ลองใหม่ภายหลัง</span></div>")
OFFLINE_HTML = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>MOCHI HOUSE</title>"
                "<body style='margin:0;min-height:100vh;display:grid;place-items:center;background:#150A30;color:#FFE0F4;font:600 20px/1.6 system-ui,sans-serif;text-align:center;padding:24px'>"
                "<div><div style='font-size:56px'>🎄</div>MOCHI HOUSE<br><span style='font-weight:400;font-size:15px;opacity:.8'>บอทกำลังออฟไลน์ชั่วคราว กรุณารอสักครู่แล้วรีเฟรชหน้านี้อีกครั้ง</span></div>"
                "<script>setTimeout(function(){location.reload()},15000)</script>")
OFFLINE_JSON = json.dumps({"ok": False, "error": "บอทออฟไลน์ชั่วคราว ลองใหม่อีกครั้งในอีกสักครู่"}, ensure_ascii=False).encode()


def pack(head, body=b""):
    h = json.dumps(head, ensure_ascii=False).encode()
    return struct.pack(">I", len(h)) + h + body


def unpack(data):
    n = struct.unpack(">I", data[:4])[0]
    return json.loads(data[4:4 + n].decode()), data[4 + n:]


def online():
    ws = st["ws"]
    return ws is not None and not ws.closed


def client_ip(req):
    return (req.headers.get("CF-Connecting-IP") or req.headers.get("True-Client-IP")
            or (req.headers.get("X-Forwarded-For") or "").split(",")[0].strip() or req.remote or "?")


def limited(ip, n, per):
    t = time.time(); k = ip
    hits[k] = [x for x in hits.get(k, []) if t - x < per]
    if len(hits[k]) >= n: return True
    hits[k].append(t)
    if len(hits) > 20000: hits.clear()
    return False


async def call_pc(method, path, headers, body=b""):
    """ส่งคำขอไปให้บอท · คืน (status, headers, body) หรือ None ถ้าบอทออฟไลน์"""
    ws = st["ws"]
    if ws is None or ws.closed: return None
    rid = next(_ids)
    fut = asyncio.get_running_loop().create_future(); pending[rid] = fut
    try:
        await ws.send_bytes(pack({"t": "req", "id": rid, "m": method, "p": path, "h": headers}, body))
        return await asyncio.wait_for(fut, TIMEOUT)
    except asyncio.TimeoutError:
        return (504, [["Content-Type", "application/json; charset=utf-8"]],
                json.dumps({"ok": False, "error": "บอทตอบช้าเกินไป ลองใหม่อีกครั้ง"}, ensure_ascii=False).encode())
    except Exception:
        return None
    finally:
        pending.pop(rid, None)


def cache_put(key, status, headers, body):
    if len(body) > 3 * 1024 * 1024: return
    old = cache.pop(key, None)
    if old: cache_bytes[0] -= len(old[3])
    if cache_bytes[0] + len(body) > CACHE_LIMIT:
        cache.clear(); cache_bytes[0] = 0
    cache[key] = (time.time(), status, headers, body); cache_bytes[0] += len(body)


def cacheable(req):
    p = req.path
    return (req.method == "GET" and "Authorization" not in req.headers and "Range" not in req.headers and
            (p in ("/", "/gallery", "/og.gif", "/og.jpg", "/api/xmas/site", "/api/xmas/banners") or p.startswith("/u/")))


def fresh_ok(req):
    """ไฟล์นิ่ง ๆ (รูปที่อัปโหลด/ภาพ og) ส่งจากแคชได้เลยเพื่อประหยัดเน็ตเครื่องคุณ · หน้าเว็บ/ API ถามบอททุกครั้ง (สถิติจะได้นับถูก)"""
    return req.path.startswith("/u/") or req.path in ("/og.gif", "/og.jpg")


def make_resp(req, status, hdrs, body, extra=None):
    h = CIMultiDict()
    for k, v in hdrs:
        if k.lower() in HOP: continue
        h.add(k, v)
    for k, v in (extra or {}).items(): h[k] = v
    resp = web.Response(status=status, body=body, headers=h)
    ct = h.get("Content-Type", "").split(";")[0].strip().lower()
    if len(body) > 1024 and status == 200 and "Content-Encoding" not in h and ct in COMPRESS and "gzip" in req.headers.get("Accept-Encoding", ""):
        resp.enable_compression()
    return resp


def offline_resp(req):
    wants_html = "text/html" in req.headers.get("Accept", "") and not req.path.startswith("/api/")
    if wants_html:
        return web.Response(status=503, text=OFFLINE_HTML, content_type="text/html", charset="utf-8", headers={"Retry-After": "15"})
    return web.Response(status=503, body=OFFLINE_JSON, content_type="application/json", charset="utf-8", headers={"Retry-After": "15"})


async def proxy(req):
    ip = client_ip(req)
    if limited(ip, 600, 60):
        return web.Response(status=429, text="too many requests")
    key = f"GET {req.path_qs}"
    if cacheable(req) and fresh_ok(req) and online():
        c = cache.get(key)
        if c and time.time() - c[0] < 3600:
            return make_resp(req, c[1], c[2], c[3], {"X-Cache": "HIT"})
    if not online():
        c = cache.get(key) if cacheable(req) else None
        if c: return make_resp(req, c[1], c[2], c[3], {"X-Offline": "1", "Cache-Control": "no-store"})
        return offline_resp(req)
    body = await req.read() if req.method in ("POST", "PUT", "PATCH", "DELETE") else b""
    heads = [[k, v] for k, v in req.headers.items() if k.lower() not in DROP_IN]
    heads += [["Host", req.host], ["X-Forwarded-Host", req.host], ["X-Forwarded-Proto", "https"],
              ["X-Forwarded-For", ip], ["CF-Connecting-IP", ip]]
    r = await call_pc(req.method, req.path_qs, heads, body)
    if r is None:
        c = cache.get(key) if cacheable(req) else None
        if c: return make_resp(req, c[1], c[2], c[3], {"X-Offline": "1", "Cache-Control": "no-store"})
        return offline_resp(req)
    status, hdrs, rb = r
    if cacheable(req) and status == 200: cache_put(key, status, hdrs, rb)
    return make_resp(req, status, hdrs, rb)


async def prewarm():
    """พอบอทต่อสะพานมา ดึงหน้าหลักเก็บแคชไว้ → ตอนบอทปิด หน้าเว็บยังเปิดได้"""
    await asyncio.sleep(1.5)
    for p in ("/", "/gallery", "/api/xmas/site", "/api/xmas/banners"):
        try:
            r = await call_pc("GET", p, [["Host", os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")], ["X-Forwarded-Proto", "https"], ["Accept", "text/html,application/json"]])
            if r and r[0] == 200: cache_put(f"GET {p}", r[0], r[1], r[2])
        except Exception: pass


async def bridge(req):
    if not SECRET: return web.Response(status=503, text="BRIDGE_SECRET not set")
    given = req.headers.get("X-Bridge-Secret", "")
    if not hmac.compare_digest(given.encode(), SECRET.encode()):
        await asyncio.sleep(1)
        return web.Response(status=401, text="unauthorized")
    ws = web.WebSocketResponse(heartbeat=20, max_msg_size=64 * 1024 * 1024)
    await ws.prepare(req)
    old = st["ws"]; st["ws"] = ws; st["since"] = time.time()
    print("🔗 บอทเชื่อมสะพานแล้ว")
    if old is not None and not old.closed:
        try: await old.close()
        except Exception: pass
    asyncio.create_task(prewarm())
    try:
        async for m in ws:
            if m.type == WSMsgType.BINARY:
                try:
                    head, body = unpack(m.data)
                    if head.get("t") == "res":
                        fut = pending.get(head.get("id"))
                        if fut and not fut.done(): fut.set_result((int(head["s"]), head.get("h", []), body))
                except Exception as e:
                    print("bridge frame error:", e)
    finally:
        if st["ws"] is ws:
            st["ws"] = None
            for f in list(pending.values()):
                if not f.done(): f.set_result(None)
            print("🔌 บอทตัดการเชื่อมต่อ (ออฟไลน์)")
    return ws


async def ping(req):
    return web.Response(text="ok", content_type="text/plain", headers={"X-Bot": "online" if online() else "offline", "Cache-Control": "no-store"})


async def status(req):
    return web.json_response({"relay": "ok", "bot": "online" if online() else "offline",
                              "since": int(st["since"]) if online() else None}, headers={"Cache-Control": "no-store"})


async def kick(req):
    if KICK_MIN and not limited("k:" + client_ip(req), 20, 60):
        if len(kicked) > 5000: kicked.clear()
        kicked[client_ip(req)] = time.time() + KICK_MIN * 60
    return web.Response(status=204)


@web.middleware
async def guard(req, handler):
    if KICK_MIN and req.path not in ("/ping", "/healthz", "/_status", "/_bridge"):
        ip = client_ip(req); t = kicked.get(ip)
        if t:
            if t < time.time(): kicked.pop(ip, None)
            else: return web.Response(status=403, text=KICK_HTML, content_type="text/html", charset="utf-8")
    try:
        resp = await handler(req)
    except web.HTTPException as ex:
        resp = ex
    return resp


def make_app():
    app = web.Application(middlewares=[guard], client_max_size=MAX_REQ)
    app.router.add_get("/ping", ping)
    app.router.add_get("/healthz", ping)
    app.router.add_get("/_status", status)
    app.router.add_get("/_bridge", bridge)
    app.router.add_post("/api/xmas/kick", kick)
    app.router.add_route("*", "/{tail:.*}", proxy)
    return app


if __name__ == "__main__":
    if not SECRET: print("⚠ ยังไม่ได้ตั้ง BRIDGE_SECRET — สะพานจะไม่ทำงาน")
    web.run_app(make_app(), host="0.0.0.0", port=PORT, access_log=None)
