# -*- coding: utf-8 -*-
"""
MOCHI HOUSE · Christmas Web v3 — เว็บกิจกรรมคริสต์มาส ผูกกับบอท kino.py (ไม่มีระบบเหรียญ)
- เว็บเซิร์ฟเวอร์ aiohttp รันในบอทตัวเดียวกัน (XMAS_PORT ค่าเริ่มต้น 8088)
- ✅ คำสั่งเดียว: /xmas (แอดมิน) → สร้าง 2 ห้องให้อัตโนมัติ แล้วทุกอย่างเป็นปุ่ม ไม่ต้องพิมพ์คำสั่งอื่น
    🎛️ ห้องควบคุมเว็บ (เห็นเฉพาะแอดมิน): พาร์ทเนอร์ (เพิ่ม/แก้ไข/ลบ/ย้าย/ตั้งคำโปรโมทดิส) · แบนเนอร์ · ตั้งค่าหน้าเข้าร่วม
        · ตั้งห้องรูปภาพ/มีเดีย/คอมเม้น/คนออก · โพสต์โปรโมทเว็บ · สถิติเข้าเว็บ · ทดสอบ DM
    🎄 ห้องเมนูเว็บ (ทุกคน): 🔑 รับโค้ดเข้าเว็บ · 🎁 ส่งของขวัญให้เพื่อน · ลิงก์เข้าเว็บ/แกลเลอรี
- หน้าพาร์ทเนอร์บนเว็บ: การ์ดดิสคอร์ดมีปุ่ม "ดูรายละเอียด" เด้งหน้าต่างคำโปรโมทที่แอดมินตั้งไว้
- ลิงก์เว็บที่ส่งในดิสคอร์ดจะขึ้นการ์ด (Open Graph) ใช้รูป xmas_web/og.jpg · โพสต์โปรโมทใช้ xmas_web/og.gif
- 🗓️ ห้องจัดการกิจกรรม (เฉพาะแอดมิน): แก้ไข "กิจกรรมตลอดเทศกาล" ด้วยปุ่ม (เพิ่ม/แก้ไข/ลบ/รีเซ็ต) + จัดการ "สมัครกิจกรรม" (สร้าง/ตั้งค่า/แบนเนอร์/ยศ/รายชื่อ/ประกาศ)
- 📝 ห้องสมัครกิจกรรม (ทุกคนอ่านได้): เมื่อมีคนสมัครกิจกรรมบนเว็บ บอทจะเด้งข้อความ "สมัครแล้ว" เข้าห้องนี้ทันที (ยกเลิกสมัคร = ข้อความถูกแก้เป็นยกเลิก)
.env (ไม่บังคับ): XMAS_SIGNUP_CHANNEL, XMAS_PORT, XMAS_PUBLIC_URL, XMAS_TEST_DATE=YYYY-MM-DD, XMAS_MEMBERS_PUBLIC=0, XMAS_BANNER_URL
"""
import os, io, time, random, secrets, string, asyncio, re, hashlib
from datetime import datetime, timezone, timedelta
import discord
from aiohttp import web, ClientSession, ClientTimeout
from urllib.parse import urlencode

TH = timezone(timedelta(hours=7))
CODE_TTL, SESSION_TTL, PAGE = 300, 7 * 86400, 48
DEFAULT_URL = "https://blackberry-minister-replacement-feelings.trycloudflare.com"
DEFAULT_BANNER = "https://i.imgur.com/your-mochi-banner.gif"  # ← เปลี่ยนเป็นลิงก์ GIF ของคุณ

# กิจกรรมประจำวัน (แก้ข้อความได้ตามใจ) — ช่องที่ยังไม่ถึงวันจะไม่ถูกส่งไปที่หน้าเว็บ
ACTIVITIES = [
    "ตกแต่งโปรไฟล์หรือชื่อเล่นในเซิร์ฟเป็นธีมคริสต์มาส", "ทักทายสมาชิกใหม่ 1 คน", "แชร์เพลงคริสต์มาสที่ชอบพร้อมเหตุผล",
    "วาดรูปซานต้าหรือกวางเรนเดียร์แล้วโพสต์ในห้องแกลเลอรี", "เข้าห้องเสียงคุยกับเพื่อนอย่างน้อย 15 นาที",
    "เล่าความทรงจำคริสต์มาสที่ประทับใจที่สุด", "โพสต์รูปมุมตกแต่งบ้านหรือห้องของคุณ", "ชวนเพื่อน 1 คนมาเล่นเกมด้วยกัน",
    "ส่งอีโมจิน่ารักให้เพื่อน 3 คน", "เขียนคำอวยพรให้สมาชิกที่ไม่ค่อยได้คุยด้วย", "โหวตเมนูอาหารคริสต์มาสในห้องแชท",
    "ทายปริศนาคริสต์มาสร่วมกันในห้องกิจกรรม", "แชร์สูตรเครื่องดื่มร้อนที่ชอบ", "ถ่ายรูปของขวัญที่อยากให้ตัวเอง",
    "ร้องเพลงสั้น 30 วินาทีในห้องเสียง", "เขียนรีวิวหนังคริสต์มาสที่ชอบ", "ชวนเพื่อนจัดคืนดูหนังด้วยกัน",
    "แต่งหรือวาดต้นคริสต์มาสในสไตล์ของคุณ", "ขอบคุณสมาชิกที่เคยช่วยเหลือคุณ", "เล่นเกมวอยซ์แชทกับเพื่อนอย่างน้อย 1 รอบ",
    "โพสต์ wishlist สำหรับ Secret Santa", "เตรียมของขวัญและข้อความสำหรับ Secret Santa",
    "คืนคริสต์มาสอีฟ มาร่วมปาร์ตี้ในห้องเสียง", "วันคริสต์มาส ส่งความสุขให้ทั้งเซิร์ฟเวอร์",
]

# ตารางกิจกรรมทั้งหมด + ทีมงาน — แก้ได้ที่ไฟล์ xmas_config.json (สร้างให้อัตโนมัติ ไม่ต้องรีสตาร์ท รอไม่เกิน 30 วินาที)
DEFAULT_CFG = {
    "owner": {"id": 0, "title": "หัวหน้าเซิร์ฟเวอร์", "bio": ""},  # id = กำหนดเอง (0 = ใช้เจ้าของเซิร์ฟเวอร์อัตโนมัติ) · bio = ข้อความสั้นใต้ชื่อ (ว่าง = ไม่แสดง)
    "admins": [],
    "devs": [],
    "events": [
        {"date": "2026-12-01", "time": "", "icon": "🎄", "title": "เปิดเทศกาลคริสต์มาส", "desc": "ปฏิทินกิจกรรมเริ่มต้น พร้อมเปิดรับสมัคร Secret Santa"},
        {"date": "2026-12-05", "time": "20:00", "icon": "📸", "title": "ประกวดมุมคริสต์มาส", "desc": "โพสต์รูปต้นคริสต์มาสหรือมุมตกแต่งของคุณในห้องแกลเลอรี ส่งได้ถึงวันที่ 20"},
        {"date": "2026-12-10", "time": "20:00", "icon": "🎮", "title": "คืนเกมสุดป่วน", "desc": "รวมพลเล่นเกมวอยซ์แชทกับเพื่อนทั้งเซิร์ฟเวอร์"},
        {"date": "2026-12-15", "time": "21:00", "icon": "🎅", "title": "จับคู่ Secret Santa", "desc": "ปิดรับสมัครและประกาศคู่ลับทาง DM"},
        {"date": "2026-12-18", "time": "20:30", "icon": "🎬", "title": "คืนดูหนังคริสต์มาส", "desc": "ดูหนังด้วยกันในห้องเสียง นั่งอุ่นๆ กับเพื่อน"},
        {"date": "2026-12-20", "time": "20:00", "icon": "🗳️", "title": "โหวตผลประกวดมุมคริสต์มาส", "desc": "ทุกคนช่วยกันโหวตภาพที่ชอบที่สุด"},
        {"date": "2026-12-24", "time": "20:00", "icon": "🎤", "title": "ปาร์ตี้คริสต์มาสอีฟ", "desc": "คาราโอเกะ เปิดเผยตัวซานต้า และกิจกรรมปิดท้ายสุดอบอุ่น"},
        {"date": "2026-12-25", "time": "18:00", "icon": "🏆", "title": "ประกาศผลและมอบยศพิเศษ", "desc": "สรุปผลทุกกิจกรรม พร้อมมอบยศให้ผู้ร่วมสนุก"},
    ],
}

def setup(bot, g):
    BASE = g["BASE_DIR"]
    load_json, save_json = g["load_json"], g["save_json"]
    DATA_DIR = os.getenv("XMAS_DATA_DIR") or BASE   # Render: ตั้งเป็นโฟลเดอร์ของ Disk เช่น /var/data
    try: os.makedirs(DATA_DIR, exist_ok=True)
    except Exception: pass
    DATA = os.path.join(DATA_DIR, "xmas_data.json")
    WEB = os.path.join(BASE, "xmas_web", "index.html")
    GAL = os.path.join(BASE, "xmas_web", "gallery.html")
    PORT = int(os.getenv("XMAS_PORT") or os.getenv("PORT") or "8088")   # Render ส่งพอร์ตมาใน PORT
    HOST = os.getenv("XMAS_HOST", "0.0.0.0")
    def fix_url(u):
        """แก้ลิงก์ใน .env ที่พิมพ์ผิด เช่น 'https:https://x.com' / ไม่มี https:// / มีช่องว่าง"""
        u = (u or "").strip().strip("\"'")
        ms = list(re.finditer(r"https?://", u))
        if ms: u = u[ms[-1].start():]
        elif u: u = "https://" + u.lstrip(":/")
        return u.rstrip("/")
    PUBLIC = fix_url(os.getenv("XMAS_PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or DEFAULT_URL) or fix_url(DEFAULT_URL)
    ORIGIN = os.getenv("XMAS_ORIGIN", "")
    TEST = os.getenv("XMAS_TEST_DATE", "")
    OPEN_MEMBERS = os.getenv("XMAS_MEMBERS_PUBLIC", "1") != "0"
    BANNER = os.getenv("XMAS_BANNER_URL") or (PUBLIC + "/og.gif" if os.path.exists(os.path.join(BASE, "xmas_web", "og.gif")) else DEFAULT_BANNER)
    lock = asyncio.Lock()
    hits, cache = {}, {"t": 0, "rows": [], "stats": None, "bn": None, "site": None}

    def db():
        d = load_json(DATA, {})
        for k in ("codes", "sessions", "advent", "santa", "gifts"): d.setdefault(k, {})
        if not isinstance(d.get("banners"), list): d["banners"] = []
        if not isinstance(d.get("partners"), list): d["partners"] = []
        if not isinstance(d.get("events"), list): d["events"] = []      # กิจกรรมตลอดเทศกาลที่แก้ผ่านดิสคอร์ด (ใช้เมื่อ events_custom = True)
        if not isinstance(d.get("signups"), list): d["signups"] = []    # กิจกรรมที่เปิดให้สมัครบนเว็บ
        if not isinstance(d.get("regs"), dict): d["regs"] = {}          # ผู้สมัคร: regs[id กิจกรรม][uid] = {...}
        if not isinstance(d.get("site"), dict): d["site"] = {}
        return d

    def now_th():
        if TEST:
            try: return datetime.strptime(TEST, "%Y-%m-%d").replace(tzinfo=TH)
            except ValueError: pass
        return datetime.now(TH)

    def guild():
        gid = g.get("GUILD_ID")
        return bot.get_guild(gid) if gid else (bot.guilds[0] if bot.guilds else None)

    def advent_day():
        t = now_th()
        return t.day if (t.month == 12 and t.day <= 25) else 0

    # ---- /xmasweb ----
    async def give_code(interaction: discord.Interaction):
        async with lock:
            d, t = db(), time.time()
            d["codes"] = {c: v for c, v in d["codes"].items() if v["exp"] > t}
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            while code in d["codes"]: code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            d["codes"][code] = {"uid": interaction.user.id, "exp": t + CODE_TTL}
            save_json(DATA, d)
        await interaction.response.send_message(
            f"🎄 **โค้ดเข้าเว็บคริสต์มาส MOCHI HOUSE**\n# `{code}`\nใส่ที่ {PUBLIC} ภายใน 5 นาที (ใช้ได้ครั้งเดียว)\n"
            f"-# อย่าส่งโค้ดนี้ให้ใคร", ephemeral=True)

    # ---- 🟣 NEW: /xmaslink (Promotion Embed) ----
    async def post_promo(interaction, image_url=None, title=None, description=None, button_label=None, channel=None):
        banner_url = image_url or BANNER
        embed_title = title or "✨ MOCHI HOUSE · Christmas 2026 ✨"
        embed_desc = description or (
            "🎄 **ยินดีต้อนรับสู่เทศกาลคริสต์มาสสุดอลังการ!** 🎄\n\n"
            "ร่วมสนุกกับกิจกรรมตลอด 25 วัน, ปฏิทินสุ่มรับดาว ⭐, "
            "จับคู่ Secret Santa 🎅 และอีกมากมาย\n\n"
            "─────────────────────\n"
            "**🎁 สิ่งที่รอคุณอยู่**\n"
            "› ปฏิทินกิจกรรมประจำวัน 25 วัน\n"
            "› ระบบสะสมดาวและรับรางวัล\n"
            "› จับคู่ Secret Santa กับเพื่อนในเซิร์ฟ\n"
            "› ประกวดมุมคริสต์มาส + ปาร์ตี้คืนอีฟ\n"
            "─────────────────────\n\n"
            "**👇 คลิกปุ่มด้านล่างเพื่อเข้าสู่เว็บกิจกรรมทันที**"
        )
        btn_text = button_label or "🚀 เข้าสู่เว็บกิจกรรม MOCHI HOUSE"

        embed = discord.Embed(
            title=embed_title,
            description=embed_desc,
            color=0xF2509F,
            url=PUBLIC
        )
        local_gif = os.path.join(BASE, "xmas_web", "og.gif")
        gif_file = None
        if not image_url and not os.getenv("XMAS_BANNER_URL") and os.path.exists(local_gif):
            gif_file = discord.File(local_gif, filename="og.gif")  # แนบไฟล์ตรงๆ ไม่ต้องพึ่งลิงก์เว็บ (ngrok ไม่บล็อก)
            embed.set_image(url="attachment://og.gif")
        else:
            embed.set_image(url=banner_url)
        embed.set_footer(
            text="MOCHI HOUSE · Merry Christmas 2026 · บ้านโมชิ",
            icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        )
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label=btn_text,
            style=discord.ButtonStyle.link,
            url=PUBLIC,
            emoji="🎄"
        ))
        target = channel or interaction.channel
        await interaction.response.defer(ephemeral=True)
        try:
            kw = {"embed": embed, "view": view}
            if gif_file: kw["file"] = gif_file
            await target.send(**kw)
        except discord.Forbidden:
            return await interaction.followup.send(f"⚠️ บอทส่งข้อความใน {target.mention} ไม่ได้ — ให้สิทธิ์ ส่งข้อความ · ฝังลิงก์ · แนบไฟล์", ephemeral=True)
        await interaction.followup.send(f"✅ โพสต์โปรโมทใน {target.mention} แล้ว", ephemeral=True)
    # -------------------------------------------

    # ---- 🎁 NEW: /xmasgift (ส่งของขวัญ + แอนิเมชันต้นคริสต์มาส) ----
    gift_last = {}
    GIFT_TTL = 90 * 86400

    async def do_gift(interaction, user, message="MERRY CHRISTMAS", note=None, private=False, anonymous=False):
        message = " ".join((message or "").split())[:60] or "MERRY CHRISTMAS"
        note = " ".join((note or "").split())[:120]
        if user.bot:
            return await interaction.response.send_message("🤖 บอทรับของขวัญไม่ได้นะ ลองส่งให้เพื่อนที่เป็นคนจริงๆ", ephemeral=True)
        t = time.time()
        if t - gift_last.get(interaction.user.id, 0) < 20:
            return await interaction.response.send_message("⏳ รอสักครู่ก่อนส่งของขวัญชิ้นต่อไปนะ (เว้น 20 วินาที)", ephemeral=True)
        gift_last[interaction.user.id] = t

        gid = secrets.token_urlsafe(6)
        sender = "ซานต้าลึกลับ" if anonymous else interaction.user.display_name
        async with lock:
            d = db()
            d["gifts"][gid] = {"from": sender, "from_id": interaction.user.id, "to": user.display_name, "to_id": user.id,
                               "msg": message, "note": note, "at": int(t), "views": 0}
            d["gifts"] = {k: v for k, v in d["gifts"].items() if t - v.get("at", 0) < GIFT_TTL}
            if len(d["gifts"]) > 1000:
                keep = sorted(d["gifts"].items(), key=lambda kv: kv[1].get("at", 0))[-1000:]
                d["gifts"] = dict(keep)
            save_json(DATA, d)
        link = f"{PUBLIC}/?gift={gid}"

        # โหลดห่อของขวัญในดิสคอร์ด
        def bar(p): return "▰" * round(p / 10) + "▱" * (10 - round(p / 10))
        frames = [(0, "🎁 กำลังหาของขวัญ"), (28, "🎀 กำลังห่อของขวัญ"), (57, "✨ กำลังผูกริบบิ้น"), (84, "🎄 กำลังใส่ต้นคริสต์มาส"), (100, "🎁 เสร็จแล้ว!")]
        head = f"{user.mention} " if not private else ""
        await interaction.response.send_message(f"{head}{frames[0][1]} …\n`{bar(0)}` 0%", ephemeral=private)
        for p, txt in frames[1:]:
            await asyncio.sleep(0.8)
            try: await interaction.edit_original_response(content=f"{head}{txt} …\n`{bar(p)}` {p}%")
            except Exception: break
        await asyncio.sleep(0.5)

        embed = discord.Embed(
            title=f"🎁 ของขวัญคริสต์มาสสำหรับ {user.display_name}",
            description=f"**จาก** {sender}\n\n🎄 กดปุ่มด้านล่างเพื่อ **เปิดของขวัญ** — ต้นคริสต์มาสจะขึ้นในบัญชีของคุณบนเว็บ MOCHI HOUSE!\n-# ล็อกอินด้วยโค้ดจากปุ่ม 🔑 ในห้องเมนูเว็บ · เปิดได้เฉพาะผู้รับเท่านั้น",
            color=0xF2509F, url=link)
        if os.getenv("XMAS_BANNER_URL"): embed.set_image(url=BANNER)
        embed.set_footer(text="MOCHI HOUSE · Christmas 2026")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="เปิดของขวัญ", style=discord.ButtonStyle.link, url=link, emoji="🎁"))

        if not private:
            return await interaction.edit_original_response(content=f"{user.mention} 🎁 มีของขวัญจาก **{sender}** มาถึงแล้ว!", embed=embed, view=view)
        try:
            await user.send(embed=embed, view=view)
            await interaction.edit_original_response(content=f"✅ ส่งของขวัญเป็น DM ให้ **{user.display_name}** เรียบร้อย\nผู้รับจะเห็นต้นคริสต์มาสในบัญชีตัวเองเมื่อเข้าเว็บ")
        except (discord.Forbidden, discord.HTTPException):
            await interaction.edit_original_response(content=f"⚠️ ส่ง DM ให้ **{user.display_name}** ไม่ได้ (เขาปิด DM ไว้)\nส่งลิงก์นี้ให้เขาเองได้เลย (เปิดได้เฉพาะเขา): {link}")
    # -----------------------------------------------------------

    # ---- 🎞️ /xmasbanner (แอดมินจัดการแบนเนอร์กิจกรรมบนเว็บ) ----
    THEMES = {"pink": "ชมพู", "purple": "ม่วง", "gold": "ทอง", "blue": "ฟ้า", "green": "เขียว", "red": "แดง"}
    MAX_BANNERS = 12

    def is_admin(i):
        p = getattr(i.user, "guild_permissions", None)
        return bool(p and (p.administrator or p.manage_guild))

    # ---- 🖼️ อัปโหลดรูปจากเครื่อง: บอทดาวน์โหลดไฟล์เก็บไว้ที่ xmas_web/uploads แล้วเสิร์ฟเองที่ /u/<ชื่อไฟล์> (ลิงก์ดิสคอร์ดหมดอายุ แต่ไฟล์นี้ถาวร) ----
    UPL = os.path.join(os.getenv("XMAS_DATA_DIR") or os.path.join(BASE, "xmas_web"), "uploads")
    UP_MAX = 8 * 1024 * 1024
    UP_RE = re.compile(r"^/u/[A-Za-z0-9_-]{6,40}\.(?:png|jpg|gif|webp)$")

    async def say(i, text):
        if i.response.is_done(): await i.followup.send(text, ephemeral=True)
        else: await i.response.send_message(text, ephemeral=True)

    async def save_upload(att):
        """คืน (path '/u/xxx.png', error)"""
        if att.size > UP_MAX: return None, f"รูปใหญ่เกินไป (ไม่เกิน {UP_MAX // 1048576} MB)"
        if not ((att.content_type or "").lower().startswith("image/") or att.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))):
            return None, "ไฟล์ต้องเป็นรูปภาพ (png / jpg / gif / webp)"
        try: data = await att.read()
        except Exception: return None, "ดาวน์โหลดรูปจากดิสคอร์ดไม่สำเร็จ ลองใหม่อีกครั้ง"
        kind, ext = sniff(data)
        if kind != "i" or ext not in ("png", "jpg", "gif", "webp"): return None, "รองรับเฉพาะ png / jpg / gif / webp (ไฟล์ HEIC/AVIF ไม่รองรับ)"
        try:
            os.makedirs(UPL, exist_ok=True)
            name = secrets.token_urlsafe(9) + "." + ext
            with open(os.path.join(UPL, name), "wb") as fh: fh.write(data)
        except Exception as e:
            print(f"   ✖ บันทึกรูปอัปโหลดไม่สำเร็จ: {type(e).__name__}: {e}")
            return None, "บันทึกรูปลงเครื่องไม่สำเร็จ (ตรวจสิทธิ์เขียนโฟลเดอร์ xmas_web/uploads)"
        return "/u/" + name, None

    def drop_upload(path):
        """ลบไฟล์อัปโหลดเก่าที่ไม่ได้ใช้แล้ว (เฉพาะไฟล์ที่เราเก็บเอง)"""
        try:
            if path and UP_RE.fullmatch(path): os.remove(os.path.join(UPL, path[3:]))
        except Exception: pass

    def clean_url(u):
        u = (u or "").strip()
        return u[:400] if re.fullmatch(r"https://[^\s<>\"']+", u or "") else ""

    def clean_fields(title, desc, event_date, event_time, icon, theme, image_url, link, label, cta=None):
        """คืน (dict, error) — ฟิลด์ที่เป็น None = ไม่ส่งมา"""
        out = {}
        if title is not None: out["title"] = " ".join(title.split())[:48]
        if desc is not None: out["desc"] = " ".join(desc.split())[:140]
        if icon is not None: out["icon"] = icon.strip()[:8] or "🎄"
        if theme is not None: out["theme"] = theme if theme in THEMES else "pink"
        if label is not None: out["label"] = " ".join(label.split())[:24]
        if cta is not None: out["cta"] = " ".join(cta.split())[:20]
        if event_date is not None:
            ed = event_date.strip()
            if ed in ("", "-"): out["date"] = ""
            else:
                try: datetime.strptime(ed, "%Y-%m-%d")
                except ValueError: return None, "วันที่ต้องเป็นรูปแบบ `YYYY-MM-DD` เช่น `2026-12-24`"
                out["date"] = ed
        if event_time is not None:
            et = event_time.strip()
            if et in ("", "-"): out["time"] = ""
            elif re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", et): out["time"] = et
            else: return None, "เวลาต้องเป็นรูปแบบ `HH:MM` เช่น `20:00`"
        for key, val in (("image", image_url), ("link", link)):
            if val is not None:
                if val.strip() in ("", "-"): out[key] = ""
                elif key == "link" and re.fullmatch(r"#[A-Za-z0-9_-]{1,40}", val.strip()): out[key] = val.strip()   # ลิงก์ในหน้าเว็บ เช่น #signup
                else:
                    cu = clean_url(val)
                    if not cu: return None, "ลิงก์ต้องขึ้นต้นด้วย `https://` (หรือ `#signup` = พาไปหมวดสมัครกิจกรรม)"
                    out[key] = cu
        return out, None

    def banner_list_text(rows):
        if not rows: return "ยังไม่มีแบนเนอร์ที่ตั้งเอง — เว็บกำลังใช้กิจกรรมจากตารางกิจกรรมอัตโนมัติ"
        return "\n".join(f"**{n}.** {'🙈' if b.get('off') else b.get('icon','🎄')} {b['title']}" + (f" · `{b['date']}`" if b.get("date") else "") +
                         (f" {b['time']}" if b.get("time") else "") + f" · {THEMES.get(b.get('theme'), 'ชมพู')}" + (" · ซ่อนอยู่" if b.get("off") else "") for n, b in enumerate(rows, 1))

    THEME_CH = [discord.app_commands.Choice(name=v, value=k) for k, v in THEMES.items()]

    async def deny(i): await i.response.send_message("🔒 คำสั่งนี้สำหรับแอดมินเท่านั้น", ephemeral=True)


    # ---- 🤝 /xmaspartner : พาร์ทเนอร์ (คน / ดิสคอร์ด) ที่โชว์ในเมนูขีดสามขีดบนเว็บ ----
    MAX_PARTNERS = 40
    KIND_NAME = {"person": "คน", "server": "ดิสคอร์ด"}
    KIND_CH = [discord.app_commands.Choice(name="คน (พาร์ทเนอร์บุคคล / ครีเอเตอร์)", value="person"),
               discord.app_commands.Choice(name="ดิสคอร์ด (เซิร์ฟเวอร์พาร์ทเนอร์)", value="server")]

    def partner_text(rows):
        if not rows: return "ยังไม่มีพาร์ทเนอร์ — กด ➕ ที่ห้องควบคุม"
        return "\n".join(f"**{n}.** {'🤝' if p['kind'] == 'person' else '🌐'} {p.get('name') or '(ใช้ชื่อจากดิสคอร์ด)'} · {KIND_NAME.get(p['kind'], '')}"
                         + (f" · <@{p['uid']}>" if p.get("uid") else "") for n, p in enumerate(rows, 1))

    def clean_partner(name, title, desc, image_url, link, promo=None):
        out = {}
        if promo is not None: out["promo"] = clean_promo(promo)
        if name is not None: out["name"] = " ".join(name.split())[:48]
        if title is not None: out["title"] = " ".join(title.split())[:24]
        if desc is not None: out["desc"] = " ".join(desc.split())[:140]
        for key, val in (("image", image_url), ("link", link)):
            if val is not None:
                if val.strip() in ("", "-"): out[key] = ""
                else:
                    cu = clean_url(val)
                    if not cu: return None, "ลิงก์ต้องขึ้นต้นด้วย `https://`"
                    out[key] = cu
        return out, None


    # ---- ⚙️ /xmasset : ตั้งค่าหน้าเข้าร่วมบนเว็บ (ไม่ต้องแก้ไฟล์ index.html) ----
    INVITE_RE = re.compile(r"https://(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[\w-]{2,40}")

    # ---- helpers ----
    def sess(req):
        s = db()["sessions"].get(req.headers.get("Authorization", "")[7:])
        return s if s and s["exp"] > time.time() else None

    def avatar(m): return str(m.display_avatar.replace(size=64, format="webp").url)

    def js(data, status=200): return web.json_response(data, status=status)

    def limited(req, key, n, per):
        ip = req.headers.get("X-Forwarded-For", req.remote or "?").split(",")[0].strip()
        k, t = f"{key}:{ip}", time.time()
        hits[k] = [x for x in hits.get(k, []) if t - x < per]
        if len(hits[k]) >= n: return True
        hits[k].append(t); return False

    def rows_cached():
        """สร้างรายชื่อสมาชิกครั้งเดียวต่อ 20 วินาที กันเว็บหน่วงตอนมีคนเปิดพร้อมกันเยอะ"""
        if time.time() - cache["t"] < 20 and cache["rows"]: return cache["rows"]
        gd = guild(); out = []
        if gd:
            stars = {u: len(v) for u, v in db()["advent"].items()}
            for m in gd.members:
                if m.bot: continue
                tr = m.top_role
                out.append({"name": m.display_name, "avatar": avatar(m), "on": m.status != discord.Status.offline,
                            "role": "" if tr.is_default() else tr.name,
                            "color": f"#{tr.color.value:06x}" if tr.color.value else "",
                            "stars": stars.get(str(m.id), 0), "_k": m.display_name.lower()})
            out.sort(key=lambda r: (not r["on"], r["_k"]))
        cache["t"], cache["rows"] = time.time(), out
        return out

    CFG_FILE = os.path.join(DATA_DIR, "xmas_config.json")
    cfgc = {"t": 0, "v": None, "info": None}

    def cfg():
        if time.time() - cfgc["t"] > 30 or cfgc["v"] is None:
            if not os.path.exists(CFG_FILE): save_json(CFG_FILE, DEFAULT_CFG)
            v = load_json(CFG_FILE, DEFAULT_CFG)
            cfgc["v"], cfgc["t"], cfgc["info"] = v, time.time(), None
        return cfgc["v"]

    def events_now():
        """กิจกรรมตลอดเทศกาล: ถ้าแอดมินแก้ผ่านปุ่มในดิสคอร์ดแล้ว ใช้ของในฐานข้อมูล · ไม่งั้นใช้จาก xmas_config.json"""
        d = db()
        return d["events"] if d.get("events_custom") else cfg().get("events", [])

    def events_dirty(): cache["bn"] = None; cfgc["info"] = None

    def person(m, title, bio=""):
        return {"name": m.display_name, "avatar": str(m.display_avatar.replace(size=128, format="webp").url),
                "on": getattr(m, "status", None) not in (None, discord.Status.offline), "title": title, "bio": bio}

    def build_info():
        c, gd = cfg(), guild(); team = {"owner": None, "admins": [], "devs": [], "bot": None}
        if gd:
            def ref(item):
                try: return gd.get_member(int(item.get("id", 0)))
                except Exception: return None
            o = ref(c.get("owner", {})) or gd.owner
            ob = str(c.get("owner", {}).get("bio", "") or "")
            if "ใส่ id เพื่อกำหนดเอง" in ob: ob = ""  # ข้อความอธิบายเก่าจากไฟล์ตั้งค่าที่สร้างไว้ก่อนหน้า ไม่ต้องโชว์บนเว็บ
            if o: team["owner"] = person(o, c.get("owner", {}).get("title") or "หัวหน้าเซิร์ฟเวอร์", ob)
            seen = {o.id} if o else set()
            adm = c.get("admins") or []
            if adm:
                for it in adm:
                    m = ref(it)
                    if m and m.id not in seen: seen.add(m.id); team["admins"].append(person(m, it.get("title") or "แอดมิน", it.get("bio", "")))
            else:
                for m in sorted(gd.members, key=lambda x: x.display_name.lower()):
                    if not m.bot and m.id not in seen and m.guild_permissions.administrator and len(team["admins"]) < 12:
                        seen.add(m.id); team["admins"].append(person(m, "แอดมิน"))
            for it in c.get("devs") or []:
                m = ref(it)
                if m: team["devs"].append(person(m, it.get("title") or "ผู้พัฒนาระบบ", it.get("bio", "")))
            u = bot.user
            if u: team["bot"] = {"name": u.display_name, "avatar": str(u.display_avatar.replace(size=128, format="webp").url), "on": True,
                                 "title": "ระบบบอทประจำเซิร์ฟเวอร์", "bio": "ดูแลกิจกรรม ปฏิทิน และเชื่อมต่อเว็บนี้กับดิสคอร์ด"}
        return {"ok": True, "events": events_now(), "team": team}

    async def info(req):
        if cfgc["info"] is None or time.time() - cfgc["t"] > 30: cfg(); cfgc["info"] = build_info()
        return js(cfgc["info"])

    # ---- handlers ----
    page_bytes = {}
    async def index(req):
        track_view(req, "home")
        # ใช้โดเมนที่คนเปิดเข้ามาจริงทำลิงก์ og:image/og:url (กัน .env ผูกโดเมนเก่าของ trycloudflare)
        host = (req.headers.get("X-Forwarded-Host") or req.host or "").split(",")[0].strip()
        base = f"https://{host}" if host.endswith((".trycloudflare.com", ".onrender.com")) else PUBLIC
        if base not in page_bytes:
            b = open(WEB, "rb").read().replace(b"__PUBLIC__", base.encode())
            _d = os.path.join(BASE, "xmas_web")
            if not os.path.exists(os.path.join(_d, "og.jpg")) and os.path.exists(os.path.join(_d, "og.gif")):
                b = b.replace(b"/og.jpg", b"/og.gif").replace(b'content="image/jpeg"', b'content="image/gif"')
            page_bytes[base] = b
        r = web.Response(body=page_bytes[base], content_type="text/html", charset="utf-8")
        r.enable_compression(); return r

    async def upload_file(req):
        name = req.match_info.get("name", "")
        if not UP_RE.fullmatch("/u/" + name): raise web.HTTPNotFound()
        path = os.path.join(UPL, name)
        if not os.path.isfile(path): raise web.HTTPNotFound()
        ct = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}[name.rsplit(".", 1)[1]]
        return web.FileResponse(path, headers={"Content-Type": ct})

    async def og_file(req):
        name = req.match_info["name"]
        path = os.path.join(BASE, "xmas_web", name)
        if name not in ("og.gif", "og.jpg"): raise web.HTTPNotFound()
        if not os.path.exists(path):  # ไฟล์ที่ขอไม่มี → ลองใช้อีกไฟล์แทน
            name = "og.gif" if name == "og.jpg" else "og.jpg"
            path = os.path.join(BASE, "xmas_web", name)
            if not os.path.exists(path): raise web.HTTPNotFound()
        return web.FileResponse(path, headers={"Content-Type": "image/gif" if name.endswith(".gif") else "image/jpeg"})

    async def stats(req):
        gd = guild()
        if not gd: return js({"ok": False}, 503)
        if time.time() - (cache["stats"] or {}).get("t", 0) > 10:
            cache["stats"] = {"t": time.time(), "v": {
                "members": gd.member_count,
                "online": sum(1 for m in gd.members if not m.bot and m.status != discord.Status.offline),
                "voice": sum(len(v.members) for v in gd.voice_channels)}}
        d = db(); day = advent_day()
        return js({"ok": True, "name": gd.name, **cache["stats"]["v"], "santa": len(d["santa"]),
                   "day": day, "today": now_th().strftime("%Y-%m-%d"), "acts": ACTIVITIES[:day]})

    async def members(req):
        if not OPEN_MEMBERS and not sess(req): return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        q = req.query.get("q", "").strip().lower()[:40]
        only = req.query.get("status") == "online"
        try: p = max(0, int(req.query.get("page", 0)))
        except ValueError: p = 0
        rows = [r for r in rows_cached() if (not only or r["on"]) and (not q or q in r["_k"])]
        chunk = [{k: v for k, v in r.items() if k != "_k"} for r in rows[p * PAGE:(p + 1) * PAGE]]
        return js({"ok": True, "total": len(rows), "rows": chunk, "more": (p + 1) * PAGE < len(rows)})

    # ---- 🔐 Discord OAuth2 login (scope: identify) ----
    # .env: DISCORD_CLIENT_ID (ใช้ id บอทได้), DISCORD_CLIENT_SECRET (จาก Developer Portal > OAuth2)
    # และเพิ่ม Redirect URI = <XMAS_PUBLIC_URL>/api/xmas/oauth/callback ใน Developer Portal > OAuth2 > Redirects
    OA_ID = os.getenv("DISCORD_CLIENT_ID", "")
    OA_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
    oa_states = {}

    def oa_base(req):
        host = (req.headers.get("X-Forwarded-Host") or req.host or "").split(",")[0].strip()
        return f"https://{host}" if host.endswith((".trycloudflare.com", ".onrender.com")) else PUBLIC

    async def oauth_status(req):
        return js({"ok": True, "enabled": bool(OA_SECRET and (OA_ID or (bot.user and bot.user.id)))})

    async def oauth_start(req):
        cid = OA_ID or (str(bot.user.id) if bot.user else "")
        if not (cid and OA_SECRET): raise web.HTTPFound("/?oauth=off")
        if limited(req, "oas", 20, 60): raise web.HTTPFound("/?oauth=busy")
        now = time.time()
        for k in [k for k, v in oa_states.items() if now - v[0] > 600]: oa_states.pop(k, None)
        st = secrets.token_urlsafe(16)
        back = req.query.get("back", "/")
        back = back if back in ("/", "/gallery") else "/"
        oa_states[st] = (now, back)
        q = urlencode({"client_id": cid, "redirect_uri": oa_base(req) + "/api/xmas/oauth/callback", "response_type": "code", "scope": "identify", "state": st, "prompt": "none"})
        raise web.HTTPFound("https://discord.com/oauth2/authorize?" + q)

    async def oauth_callback(req):
        st = req.query.get("state", ""); ent = oa_states.pop(st, None)
        if not ent or time.time() - ent[0] > 600 or req.query.get("error"): raise web.HTTPFound("/?oauth=fail")
        code = req.query.get("code", ""); back = ent[1]
        cid = OA_ID or (str(bot.user.id) if bot.user else "")
        try:
            async with ClientSession(timeout=ClientTimeout(total=12)) as cs:
                async with cs.post("https://discord.com/api/v10/oauth2/token", data={"client_id": cid, "client_secret": OA_SECRET, "grant_type": "authorization_code",
                        "code": code, "redirect_uri": oa_base(req) + "/api/xmas/oauth/callback"}, headers={"Content-Type": "application/x-www-form-urlencoded"}) as r:
                    tk = await r.json()
                if "access_token" not in tk: raise web.HTTPFound("/?oauth=fail")
                async with cs.get("https://discord.com/api/v10/users/@me", headers={"Authorization": "Bearer " + tk["access_token"]}) as r:
                    u = await r.json()
            uid = int(u["id"])
        except web.HTTPException: raise
        except Exception as e:
            print(f"   ✖ OAuth ล้มเหลว: {type(e).__name__}: {e}"); raise web.HTTPFound("/?oauth=fail")
        gd = guild()
        if not gd or not gd.get_member(uid): raise web.HTTPFound("/?oauth=notmember")
        async with lock:
            d = db(); tok = secrets.token_urlsafe(32)
            d["sessions"][tok] = {"uid": uid, "exp": time.time() + SESSION_TTL}
            d["sessions"] = {k: v for k, v in d["sessions"].items() if v["exp"] > time.time()}
            save_json(DATA, d)
        raise web.HTTPFound(back + "#tok=" + tok)

    async def login(req):
        if limited(req, "login", 8, 60): return js({"ok": False, "error": "ลองบ่อยเกินไป รอสักครู่"}, 429)
        try: code = str((await req.json()).get("code", "")).strip().upper()
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        async with lock:
            d = db(); c = d["codes"].pop(code, None)
            if not c or c["exp"] < time.time():
                save_json(DATA, d); return js({"ok": False, "error": "โค้ดไม่ถูกต้องหรือหมดอายุ"}, 401)
            tok = secrets.token_urlsafe(32)
            d["sessions"][tok] = {"uid": c["uid"], "exp": time.time() + SESSION_TTL}
            d["sessions"] = {k: v for k, v in d["sessions"].items() if v["exp"] > time.time()}
            save_json(DATA, d)
        return js({"ok": True, "token": tok})

    async def me(req):
        s = sess(req)
        if not s: return js({"ok": False}, 401)
        gd = guild(); m = gd.get_member(int(s["uid"])) if gd else None
        d = db(); uid = str(s["uid"])
        return js({"ok": True, "name": m.display_name if m else "สมาชิก", "avatar": avatar(m) if m else "",
                   "claimed": sorted(int(k) for k in d["advent"].get(uid, {})), "santa": d["santa"].get(uid)})

    async def claim(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        day = advent_day()
        if not day: return js({"ok": False, "error": "ปฏิทินเปิดวันที่ 1–25 ธ.ค."}, 400)
        uid = str(s["uid"])
        async with lock:
            d = db(); mine = d["advent"].setdefault(uid, {})
            if str(day) in mine: return js({"ok": False, "error": "ทำเครื่องหมายช่องวันนี้แล้ว"}, 409)
            mine[str(day)] = int(time.time()); save_json(DATA, d); cache["t"] = 0
        return js({"ok": True, "day": day, "stars": len(mine)})

    async def santa(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        try: wish = str((await req.json()).get("wish", "")).strip()[:200]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        if not wish: return js({"ok": False, "error": "เขียนของขวัญที่อยากได้ก่อนนะ"}, 400)
        async with lock:
            d = db(); new = str(s["uid"]) not in d["santa"]
            d["santa"][str(s["uid"])] = {"wish": wish, "at": int(time.time())}; save_json(DATA, d); cnt = len(d["santa"])
        if new:   # สมัครครั้งแรก → เด้งเข้าห้องสมัครกิจกรรม (ไม่โชว์ของขวัญที่ขอ เพราะเป็นความลับ)
            gd = guild(); m = gd.get_member(int(s["uid"])) if gd else None
            if m: asyncio.create_task(post_reg_notice(m, "🎅", "Secret Santa", "red", cnt))
        return js({"ok": True, "count": cnt})

    async def gift_redirect(req):
        # ลิงก์เก่า /gift/<id> → เข้าหน้าเว็บหลัก แล้วต้นคริสต์มาสขึ้นในบัญชีผู้รับ
        gid = re.sub(r"[^A-Za-z0-9_-]", "", req.match_info.get("gid", ""))[:24]
        raise web.HTTPFound("/?gift=" + gid)

    async def gifts(req):
        """ของขวัญที่ส่งถึงคนที่ล็อกอินอยู่เท่านั้น (ใหม่สุดก่อน)"""
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        if limited(req, "gifts", 90, 60): return js({"ok": False, "error": "เปิดบ่อยเกินไป รอสักครู่"}, 429)
        uid = int(s["uid"])
        mine = [(k, v) for k, v in db()["gifts"].items() if int(v.get("to_id", 0)) == uid]
        mine.sort(key=lambda kv: kv[1].get("at", 0), reverse=True)
        return js({"ok": True, "gifts": [{
            "id": k, "from": v.get("from", ""), "msg": v.get("msg", ""), "note": v.get("note", ""),
            "at": v.get("at", 0), "seen": bool(v.get("seen", v.get("views", 0) > 0))} for k, v in mine[:50]]})

    async def gift_seen(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        try: gid = str((await req.json()).get("id", ""))[:24]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        async with lock:
            d = db(); gf = d["gifts"].get(gid)
            if not gf or int(gf.get("to_id", 0)) != int(s["uid"]): return js({"ok": False, "error": "ไม่พบของขวัญนี้"}, 404)
            gf["seen"] = True; gf["views"] = gf.get("views", 0) + 1; save_json(DATA, d)
        return js({"ok": True})

    async def gift_delete(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        try: gid = str((await req.json()).get("id", ""))[:24]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        async with lock:
            d = db(); gf = d["gifts"].get(gid)
            if not gf or int(gf.get("to_id", 0)) != int(s["uid"]): return js({"ok": False, "error": "ไม่พบของขวัญนี้"}, 404)
            del d["gifts"][gid]; save_json(DATA, d)
        return js({"ok": True})

    def server_cover():
        """รูปปกเซิร์ฟเวอร์: banner → splash → ไอคอน"""
        try:
            gd = guild()
            for k in ("banner", "splash", "icon"):
                asset = getattr(gd, k, None) if gd else None
                if asset: return str(asset.replace(size=1024).url)
        except Exception: pass
        return ""

    def banners_now():
        """แบนเนอร์ที่แอดมินตั้งไว้ (ข้ามอันที่ซ่อน) ถ้าไม่มี → ดึงจากตารางกิจกรรม (ที่ยังไม่ถึง/วันนี้ก่อน)"""
        c = cache["bn"]
        if c and time.time() - c[0] < 8: return c[1]
        rows = db()["banners"]
        if rows:
            out = [{k: b.get(k, "") for k in ("id", "icon", "title", "desc", "date", "time", "theme", "image", "link", "label", "cta")} for b in rows if not b.get("off")]
            auto = False
        else:
            today = now_th().strftime("%Y-%m-%d")
            evs = sorted((e for e in events_now() if e.get("date")), key=lambda e: (e["date"], e.get("time", "")))
            up = [e for e in evs if e["date"] >= today] or evs[-6:]
            ths = ["pink", "purple", "gold", "blue", "red", "green"]
            out = [{"id": f"e{n}", "icon": e.get("icon", "🎄"), "title": e.get("title", ""), "desc": e.get("desc", ""), "date": e["date"],
                    "time": e.get("time", ""), "theme": ths[n % 6], "image": "", "link": "", "label": "", "cta": ""} for n, e in enumerate(up[:8])]
            auto = True
        res = {"ok": True, "auto": auto, "banners": out, "cover": server_cover()}
        cache["bn"] = (time.time(), res)
        return res

    async def banners(req): return js(banners_now())

    def site_now():
        """ตั้งค่าหน้าเข้าร่วม + พาร์ทเนอร์ (คน/ดิสคอร์ด) — ดึงชื่อ/รูปคนจากสมาชิกในเซิร์ฟสดๆ"""
        c = cache["site"]
        if c and time.time() - c[0] < 8: return c[1]
        d, gd = db(), guild(); persons, servers = [], []
        for p in d["partners"]:
            name, image = p.get("name", ""), p.get("image", "")
            if p.get("kind") == "person":
                m = gd.get_member(int(p["uid"])) if (gd and p.get("uid")) else None
                if m: name = name or m.display_name; image = image or str(m.display_avatar.replace(size=128, format="webp").url)
                image = image or p.get("av", "")
            row = {"id": p.get("id", ""), "name": name or "—", "title": p.get("title", ""), "desc": p.get("desc", ""), "promo": p.get("promo", ""), "cover": p.get("banner", ""), "image": image, "link": p.get("link", "")}
            (persons if p.get("kind") == "person" else servers).append(row)
        res = {"ok": True, "settings": {k: d["site"].get(k, "") for k in ("invite", "banner", "title", "desc", "intro_on", "intro_sec", "intro_text")},
               "partners": {"persons": persons, "servers": servers}}
        cache["site"] = (time.time(), res)
        return res

    async def site(req): return js(site_now())

    # ---- 🛠️ แจ้งปัญหา: ผู้ใช้กดแจ้งเอง หรือเว็บตรวจเจอ error แล้วส่งหาแอดมินทันที ----
    # ตั้งห้องรับแจ้งได้ด้วย .env: XMAS_REPORT_CHANNEL=<id ห้อง>  (ไม่ตั้ง = ส่ง DM หาเจ้าของเซิร์ฟ + แอดมินใน xmas_config.json)
    REPORT_CH = int(os.getenv("XMAS_REPORT_CHANNEL", "0") or 0)
    rp_seen = {}

    def esc(v, n):
        v = discord.utils.escape_markdown(str(v or "")[:n])
        return discord.utils.escape_mentions(v) or "—"

    async def report_targets():
        out = []
        if REPORT_CH:
            ch = bot.get_channel(REPORT_CH)
            if ch: out.append(ch)
        if out: return out
        ids, gd = set(), guild()
        if gd and gd.owner_id: ids.add(gd.owner_id)
        for it in (cfg().get("admins") or []):
            try: ids.add(int(it.get("id") if isinstance(it, dict) else it))
            except Exception: pass
        for uid in ids:
            try: out.append(bot.get_user(uid) or await bot.fetch_user(uid))
            except Exception: pass
        return out

    async def report(req):
        if limited(req, "rp", 8, 600): return js({"ok": False, "error": "ส่งบ่อยเกินไป รอสักครู่นะ"}, 429)
        try: b = await req.json()
        except Exception: return js({"ok": False}, 400)
        if not isinstance(b, dict): return js({"ok": False}, 400)
        auto = b.get("kind") == "auto"
        msg = str(b.get("msg") or "").strip()
        if len(msg) < (3 if auto else 5): return js({"ok": False, "error": "อธิบายปัญหาสั้นๆ ก่อนนะ"}, 400)
        now = time.time()
        for k in [k for k, v in rp_seen.items() if now - v > 900]: rp_seen.pop(k, None)
        fp = ("a:" if auto else "m:") + msg[:80]
        if fp in rp_seen: return js({"ok": True, "dup": True})
        if auto and sum(1 for k in rp_seen if k.startswith("a:")) >= 15: return js({"ok": True, "skipped": True})
        rp_seen[fp] = now
        s, gd, who = sess(req), guild(), "ผู้เยี่ยมชม (ยังไม่ได้ล็อกอิน)"
        if s:
            m = gd.get_member(int(s["uid"])) if gd else None
            who = f"{m.display_name} (<@{m.id}>)" if m else f"uid {s['uid']}"
        ref = secrets.token_hex(3).upper()
        ty = str(b.get("type") or "อื่นๆ")
        TS = {"ใช้งานไม่ได้": ("🐞", 0xE5484D), "แสดงผลผิดปกติ": ("🖼️", 0xF59E0B), "ข้อเสนอแนะ": ("💡", 0x3B82F6), "อื่นๆ": ("💬", 0xF2509F)}
        emo, col = TS.get(ty, ("💬", 0xF2509F))
        embed = discord.Embed(title="🚨 ระบบตรวจพบข้อผิดพลาดอัตโนมัติ" if auto else f"{emo} แจ้งปัญหา · {esc(ty, 40)}",
                              color=0xE5484D if auto else col, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=f"Ref #{ref} · MOCHI HOUSE Support")
        embed.description = (f"**💬 ข้อความจากผู้ใช้**\n>>> {esc(msg, 900)}" if not auto else f"**ข้อผิดพลาดที่ตรวจพบ**\n{esc(msg, 900)}")
        if not auto: embed.add_field(name="ประเภท", value=esc(b.get("type") or "อื่นๆ", 40), inline=True)
        embed.add_field(name="ผู้แจ้ง", value=who, inline=True)
        embed.add_field(name="📱 รุ่นเครื่อง", value=esc(b.get("device") or "ไม่ทราบ", 300), inline=False)
        fence = chr(96) * 3
        det = str(b.get("detail") or "")[:700].replace(fence, chr(39) * 3)
        if det.strip(): embed.add_field(name="รายละเอียดทางเทคนิค", value=f"{fence}\n{det}\n{fence}", inline=False)
        embed.add_field(name="หน้า / อุปกรณ์", value=esc(f"{b.get('url', '')} · {b.get('vp', '')}\n{b.get('ua', '')}", 400), inline=False)
        async with lock:
            d = db(); d.setdefault("reports", []).append({"t": int(now), "auto": auto, "ref": ref, "msg": msg[:300], "type": str(b.get("type") or "")[:40],
                                                         "uid": s["uid"] if s else "", "device": str(b.get("device") or "")[:200], "url": str(b.get("url") or "")[:120]})
            d["reports"] = d["reports"][-100:]; save_json(DATA, d)
        sent = 0
        try:
            for tg in await report_targets():
                try: await tg.send(embed=embed, allowed_mentions=discord.AllowedMentions.none()); sent += 1
                except Exception: pass
        except Exception as e: print(f"   ✖ ส่งแจ้งปัญหาไม่สำเร็จ: {type(e).__name__}: {e}")
        return js({"ok": True, "sent": sent, "ref": ref})


    # ---- 🤝 ติดต่อ/สมัครเป็นพาร์ทเนอร์ : ฟอร์มบนเว็บ → ส่ง embed หาแอดมินทันที ----
    PK_LABEL = {"person": ("🤝", "พาร์ทเนอร์บุคคล / ครีเอเตอร์"), "server": ("🌐", "ดิสคอร์ดพาร์ทเนอร์"), "other": ("💬", "ติดต่อเรื่องอื่น")}

    async def partner_apply(req):
        if limited(req, "pa", 4, 900): return js({"ok": False, "error": "ส่งบ่อยเกินไป รอสักครู่นะ"}, 429)
        try: b = await req.json()
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        if not isinstance(b, dict): return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        kind = b.get("kind") if b.get("kind") in PK_LABEL else "other"
        name = " ".join(str(b.get("name") or "").split())[:60]
        contact = " ".join(str(b.get("contact") or "").split())[:100]
        link = str(b.get("link") or "").strip()[:300]
        msg = str(b.get("msg") or "").strip()[:700]
        if len(name) < 2: return js({"ok": False, "error": "ใส่ชื่อของคุณหรือชื่อเซิร์ฟเวอร์ก่อนนะ"}, 400)
        if len(contact) < 3: return js({"ok": False, "error": "ใส่ช่องทางติดต่อกลับ เช่น ชื่อดิสคอร์ด"}, 400)
        if len(msg) < 10: return js({"ok": False, "error": "เล่ารายละเอียดข้อเสนออย่างน้อยสั้นๆ ก่อนนะ"}, 400)
        if link and not re.fullmatch(r"https://[^\s<>\"']+", link): return js({"ok": False, "error": "ลิงก์ต้องขึ้นต้นด้วย https://"}, 400)
        now = time.time()
        fp = "p:" + name.lower()[:40] + contact.lower()[:40]
        for k in [k for k, v in rp_seen.items() if now - v > 900]: rp_seen.pop(k, None)
        if fp in rp_seen: return js({"ok": True, "dup": True})
        rp_seen[fp] = now
        s, gd, who = sess(req), guild(), "ผู้เยี่ยมชม (ยังไม่ได้ล็อกอิน)"
        if s:
            m = gd.get_member(int(s["uid"])) if gd else None
            who = f"{m.display_name} (<@{m.id}>)" if m else f"uid {s['uid']}"
        ref = "P" + secrets.token_hex(3).upper()
        emo, lab = PK_LABEL[kind]
        embed = discord.Embed(title=f"{emo} คำขอพาร์ทเนอร์ใหม่ · {lab}", color=0xF2509F, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=f"Ref #{ref} · MOCHI HOUSE Partner")
        embed.description = f">>> {esc(msg, 900)}"
        embed.add_field(name="ชื่อ / เซิร์ฟเวอร์", value=esc(name, 80), inline=True)
        embed.add_field(name="ติดต่อกลับ", value=esc(contact, 120), inline=True)
        embed.add_field(name="ผู้ส่งบนเว็บ", value=who, inline=True)
        if link: embed.add_field(name="ลิงก์", value=esc(link, 300), inline=False)
        async with lock:
            d = db(); d.setdefault("partner_reqs", []).append({"t": int(now), "ref": ref, "kind": kind, "name": name, "contact": contact,
                                                              "link": link, "msg": msg[:400], "uid": s["uid"] if s else ""})
            d["partner_reqs"] = d["partner_reqs"][-100:]; save_json(DATA, d)
        sent = 0
        try:
            for tg in await report_targets():
                try: await tg.send(embed=embed, allowed_mentions=discord.AllowedMentions.none()); sent += 1
                except Exception: pass
        except Exception as e: print(f"   ✖ ส่งคำขอพาร์ทเนอร์ไม่สำเร็จ: {type(e).__name__}: {e}")
        return js({"ok": True, "sent": sent, "ref": ref})

    # ---- 🖼️ แกลเลอรีเรียลไทม์: รูปล่าสุดจากห้องรูปภาพ + คอมเมนต์ใต้ภาพ (เหมือนเฟส/อินสตาแกรม) ----
    # เก็บรูปล่าสุดไว้ในหน่วยความจำ อัปเดตทันทีจาก on_message / on_raw_message_delete → หน้าเว็บ poll ทุก 3 วินาที (ไม่ยิง Discord ซ้ำ)
    GAL_MAX = 60          # จำนวนรูปล่าสุดที่โชว์ (ไม่โหลดรูปเก่ากว่านี้)
    IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif")
    gal = {"items": [], "ver": 1, "loaded": False, "t": 0, "cid": 0}
    gal_lock, gcm = asyncio.Lock(), {"v": None}

    def gal_reset():
        gal.update(loaded=False, cid=0, items=[]); gal["ver"] += 1

    def gal_channel():
        cid = db()["site"].get("gallery") or os.getenv("XMAS_GALLERY_CHANNEL", "")
        try: return bot.get_channel(int(cid)) if cid else None
        except Exception: return None

    glc = {"v": None}
    def glk_all():
        if glc["v"] is None: glc["v"] = db().get("glikes", {})
        return glc["v"]

    def cm_all():
        if gcm["v"] is None: gcm["v"] = db().get("gcomments", {})
        return gcm["v"]

    def gal_items(m):
        out = []
        if m.author.bot: return out
        for a in m.attachments:
            if not ((a.content_type or "").lower().startswith("image/") or a.filename.lower().endswith(IMG_EXT)): continue
            th = a.proxy_url or a.url
            th += ("&" if "?" in th else "?") + "format=webp&width=1080"
            out.append({"id": f"{m.id}_{a.id}", "url": a.url, "thumb": th, "w": a.width or 0, "h": a.height or 0,
                        "by": m.author.display_name, "av": avatar(m.author), "at": int(m.created_at.timestamp()),
                        "text": (m.clean_content or "")[:200], "uid": m.author.id})
        return out

    async def gal_ensure():
        ch = gal_channel()
        if not ch: return None
        if gal["cid"] != ch.id: gal.update(loaded=False, cid=ch.id, items=[])
        if gal["loaded"] and time.time() - gal["t"] < 3 * 3600: return ch   # ลิงก์รูปของดิสคอร์ดหมดอายุ ~24 ชม. → รีเฟรชทุก 3 ชม.
        async with gal_lock:
            if gal["loaded"] and time.time() - gal["t"] < 3 * 3600: return ch
            items, msgs = [], []
            async for m in ch.history(limit=100):
                its = gal_items(m); items += its
                if its: msgs.append(m)
            gal.update(items=items[:GAL_MAX], loaded=True, t=time.time()); gal["ver"] += 1
        asyncio.create_task(gd_sync_many(msgs[:GAL_MAX]))   # ดึงรายชื่อคนกดรีแอ็กชันในดิสคอร์ด (กันพลาดตอนบอทออฟไลน์)
        return ch

    async def gal_on_message(m):
        if not gal["loaded"] or m.author.bot or m.channel.id != gal["cid"]: return
        its = gal_items(m)
        if its: gal["items"] = (its + gal["items"])[:GAL_MAX]; gal["ver"] += 1

    async def gal_on_delete(p):
        if not gal["loaded"] or p.channel_id != gal["cid"]: return
        pre, n = f"{p.message_id}_", len(gal["items"])
        gal["items"] = [i for i in gal["items"] if not i["id"].startswith(pre)]
        if len(gal["items"]) != n: gal["ver"] += 1

    async def gallery_page(req):
        if not os.path.exists(GAL): raise web.HTTPNotFound()
        track_view(req, "gallery")
        return web.FileResponse(GAL, headers={"Content-Type": "text/html; charset=utf-8"})

    async def gallery(req):
        if limited(req, "gal", 150, 60): return js({"ok": False, "error": "เปิดบ่อยเกินไป รอสักครู่"}, 429)
        try: ch = await gal_ensure()
        except Exception as e:
            print(f"   ✖ อ่านห้องรูปภาพไม่ได้: {type(e).__name__}: {e}")
            return js({"ok": False, "error": "อ่านห้องรูปภาพไม่ได้ (ตรวจสิทธิ์บอท)"}, 503)
        try: await gp_refresh()
        except Exception: pass
        try: v = int(req.query.get("v", "0"))
        except ValueError: v = 0
        if v and v == gal["ver"]: return js({"ok": True, "same": True})
        s = sess(req); me = int(s["uid"]) if s else 0
        cm = cm_all(); items = []
        merged = sorted(list(gal["items"]) + [tp_item(p, me) for p in gp_all()], key=lambda x: -x.get("at", 0))[:GAL_MAX]
        for it in merged:
            cs = [{"id": c["id"], "name": c.get("name", ""), "av": c.get("av", ""), "text": c.get("text", ""), "at": c.get("at", 0),
                   "mine": bool(me) and int(c.get("uid", 0)) == me} for c in cm.get(it["id"], [])]
            rs, mine, nl = reacts_of(it["id"], me)
            items.append({**{k: v for k, v in it.items() if k != "uid"}, "comments": cs, "likes": nl, "liked": bool(mine), "mine": mine, "reacts": rs})
        return js({"ok": True, "configured": True, "channel": ch.name if ch else "", "ver": gal["ver"], "items": items, "max": GAL_MAX, "lim": media_limit()})

    async def gal_comment(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "เข้าสู่ระบบก่อนจึงจะคอมเมนต์ได้"}, 401)
        if limited(req, "gcm", 10, 60): return js({"ok": False, "error": "คอมเมนต์ถี่เกินไป รอสักครู่นะ"}, 429)
        try: b = await req.json()
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        pid = str(b.get("id") or "")[:60] if isinstance(b, dict) else ""
        text = " ".join(str(b.get("text") or "").split())[:300] if isinstance(b, dict) else ""
        if not text: return js({"ok": False, "error": "พิมพ์ข้อความก่อนนะ"}, 400)
        if not gal_has(pid): return js({"ok": False, "error": "ไม่พบโพสต์นี้แล้ว"}, 404)
        gd = guild(); m = gd.get_member(int(s["uid"])) if gd else None
        async with lock:
            d = db(); gc = d.setdefault("gcomments", {}); lst = gc.setdefault(pid, [])
            if len(lst) >= 200: return js({"ok": False, "error": "รูปนี้มีคอมเมนต์ครบแล้ว"}, 400)
            rec = {"id": secrets.token_urlsafe(4), "uid": int(s["uid"]), "name": m.display_name if m else "สมาชิก",
                   "av": avatar(m) if m else "", "text": text, "at": int(time.time())}
            lst.append(rec)
            if len(gc) > 400:
                for k in sorted(gc, key=lambda k: max((c.get("at", 0) for c in gc[k]), default=0))[:100]: gc.pop(k, None)
            save_json(DATA, d); gcm["v"] = gc; gal["ver"] += 1
        asyncio.create_task(cm_forward(pid, rec))   # เด้งเข้าห้องฟอรั่มคอมเม้น + แจ้งเจ้าของโพสต์
        return js({"ok": True})

    async def gal_cdel(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "เข้าสู่ระบบก่อน"}, 401)
        try: b = await req.json(); pid, cid = str(b.get("id") or "")[:60], str(b.get("cid") or "")[:20]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        async with lock:
            d = db(); lst = d.get("gcomments", {}).get(pid, [])
            hit = next((c for c in lst if c.get("id") == cid and int(c.get("uid", 0)) == int(s["uid"])), None)
            if not hit: return js({"ok": False, "error": "ลบได้เฉพาะคอมเมนต์ของตัวเอง"}, 404)
            lst.remove(hit); save_json(DATA, d); gcm["v"] = d["gcomments"]; gal["ver"] += 1
        asyncio.create_task(cm_unforward(hit))
        return js({"ok": True})

    # ---- โพสต์ข้อความ (เหมือนโพสต์เฟส): เก็บในหน่วยความจำ + บันทึกลง xmas_data.json ----
    gpc = {"v": None}
    GBG = {"", "g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8"}
    def gp_all():
        if gpc["v"] is None: gpc["v"] = db().get("gposts", [])
        return gpc["v"]

    def tp_item(p, me):
        md = []
        for x in p.get("media", []):
            u = x.get("url", ""); th = u
            if x.get("t") == "i" and not u.split("?")[0].lower().endswith(".gif"):
                th = x.get("px") or u; th += ("&" if "?" in th else "?") + "format=webp&width=1080"
            md.append({"t": x.get("t", "i"), "url": u, "thumb": th, "w": x.get("w", 0), "h": x.get("h", 0)})
        return {"id": "t_" + p["id"], "kind": "text", "url": "", "thumb": "", "w": 0, "h": 0, "by": p.get("name", "สมาชิก"), "av": p.get("av", ""),
                "at": p.get("at", 0), "text": p.get("text", ""), "bg": p.get("bg", ""), "media": md, "mine": bool(me) and int(p.get("uid", 0)) == me}

    def media_limit():
        gd = guild()
        try: n = int(getattr(gd, "filesize_limit", 0) or 0)
        except Exception: n = 0
        return min(n or 10 * 1024 * 1024, 50 * 1024 * 1024)

    def sniff(b):
        """ตรวจชนิดไฟล์จากเนื้อไฟล์จริง (ไม่เชื่อนามสกุล/ชนิดที่ผู้ใช้ส่งมา)"""
        if b[:8] == b"\x89PNG\r\n\x1a\n": return "i", "png"
        if b[:3] == b"\xff\xd8\xff": return "i", "jpg"
        if b[:4] == b"GIF8": return "i", "gif"
        if b[:4] == b"RIFF" and b[8:12] == b"WEBP": return "i", "webp"
        if b[4:8] == b"ftyp":
            br = b[8:12]
            if br in (b"heic", b"heix", b"heim", b"heis", b"mif1", b"msf1", b"avif", b"avis"): return None, None
            return "v", ("mov" if br == b"qt  " else "mp4")
        if b[:4] == b"\x1a\x45\xdf\xa3": return "v", "webm"
        return None, None

    async def part_bytes(part, cap):
        buf = bytearray()
        while True:
            c = await part.read_chunk(65536)
            if not c: break
            buf += c
            if len(buf) > cap: raise OverflowError
        return bytes(buf)

    async def media_channel():
        cid = db()["site"].get("media") or os.getenv("XMAS_MEDIA_CHANNEL", "")
        if not cid:
            return gal_channel()
        try:
            n = int(cid); return bot.get_channel(n) or await bot.fetch_channel(n)
        except Exception: return None

    gpr = {"lock": asyncio.Lock()}
    async def gp_refresh():
        """ลิงก์ไฟล์ของดิสคอร์ดหมดอายุ ~24 ชม. → รีเฟรชลิงก์ของโพสต์มีเดียทุก 3 ชม. (ถ้าข้อความถูกลบในดิสคอร์ด = โพสต์หายด้วย)"""
        now = time.time()
        due = [p for p in gp_all()[:GAL_MAX] if p.get("mid") and now - p.get("rt", 0) > 3 * 3600][:5]
        if not due or gpr["lock"].locked(): return
        async with gpr["lock"]:
            changed = False
            for p in due:
                try:
                    ch = bot.get_channel(p["cid"]) or await bot.fetch_channel(p["cid"])
                    m = await ch.fetch_message(p["mid"])
                    for md, a in zip(p.get("media", []), m.attachments): md.update(url=a.url, px=a.proxy_url or a.url)
                    try: await gd_sync(m)
                    except Exception: pass
                    p["rt"] = now; changed = True
                except discord.NotFound:
                    if p in gp_all(): gp_all().remove(p)
                    changed = True
                except Exception: p["rt"] = now - 3 * 3600 + 600
            if changed:
                d = db(); d["gposts"] = gp_all(); save_json(DATA, d); gal["ver"] += 1

    async def gp_on_delete(pl):
        lst = gp_all(); hit = next((x for x in lst if x.get("mid") == pl.message_id), None)
        if not hit: return
        async with lock:
            if hit in lst:
                lst.remove(hit); d = db(); d["gposts"] = lst; save_json(DATA, d); gal["ver"] += 1

    def gal_has(pid):
        return any(i["id"] == pid for i in gal["items"]) or (pid.startswith("t_") and any("t_" + p["id"] == pid for p in gp_all()))

    async def gal_post(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "เข้าสู่ระบบก่อนจึงจะโพสต์ได้"}, 401)
        multi = (req.content_type or "").startswith("multipart/")
        if limited(req, "gup" if multi else "gpost", 4 if multi else 6, 60): return js({"ok": False, "error": "โพสต์ถี่เกินไป รอสักครู่นะ"}, 429)
        lim = media_limit(); raw, bg, files = "", "", []
        try:
            if multi:
                if req.content_length and req.content_length > lim + 262144: return js({"ok": False, "error": f"ไฟล์ใหญ่เกินไป (รวมกันไม่เกิน {lim // 1048576} MB)"}, 413)
                rd = await req.multipart(); used = 0
                while True:
                    part = await rd.next()
                    if part is None: break
                    if part.name == "text": raw = (await part_bytes(part, 8192)).decode("utf-8", "ignore")
                    elif part.name == "bg": bg = (await part_bytes(part, 16)).decode("utf-8", "ignore")[:3]
                    elif part.name == "files" and part.filename:
                        if len(files) >= 4: return js({"ok": False, "error": "แนบได้สูงสุด 4 ไฟล์"}, 400)
                        data = await part_bytes(part, lim - used); used += len(data); files.append(data)
            else:
                b = await req.json(); raw = str(b.get("text") or ""); bg = str(b.get("bg") or "")[:3]
        except OverflowError: return js({"ok": False, "error": f"ไฟล์ใหญ่เกินไป (รวมกันไม่เกิน {lim // 1048576} MB)"}, 413)
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        lines = []
        for l in raw.replace("\r", "").split("\n"):
            l = l.strip()
            if l or (lines and lines[-1]): lines.append(l)
        text = "\n".join(lines).strip()[:500]
        media = []
        for data in files:
            k, ext = sniff(data)
            if not k: return js({"ok": False, "error": "รองรับเฉพาะรูปภาพ (png/jpg/gif/webp) และวิดีโอ (mp4/mov/webm)"}, 400)
            media.append((k, ext, data))
        if not text and not media: return js({"ok": False, "error": "พิมพ์ข้อความหรือแนบรูป/วิดีโอก่อนนะ"}, 400)
        if bg not in GBG or media: bg = ""
        gd = guild(); m = gd.get_member(int(s["uid"])) if gd else None
        name = m.display_name if m else "สมาชิก"
        rec = {"id": secrets.token_urlsafe(5), "uid": int(s["uid"]), "name": name, "av": avatar(m) if m else "", "text": text, "bg": bg, "at": int(time.time())}
        if media:
            ch = await media_channel()
            if not ch: return js({"ok": False, "error": "แอดมินยังไม่ได้ตั้งห้องมีเดีย (ปุ่ม 🎬 ในห้องควบคุม) หรือบอทมองไม่เห็นห้อง"}, 503)
            try:
                fl = [discord.File(io.BytesIO(d), filename=f"{secrets.token_hex(4)}.{e}") for _, e, d in media]
                head = "🌐 โพสต์จากเว็บ MOCHI HOUSE · **" + discord.utils.escape_markdown(name) + "**"
                msg = await ch.send(content=(head + ("\n" + text if text else ""))[:1990], files=fl, allowed_mentions=discord.AllowedMentions.none())
            except Exception as e:
                print(f"   ✖ ส่งโพสต์ไปห้องมีเดียไม่สำเร็จ: {type(e).__name__}: {e}")
                return js({"ok": False, "error": "ส่งไปห้องมีเดียไม่สำเร็จ (บอทต้องมีสิทธิ์ ส่งข้อความ + แนบไฟล์ ในห้องนั้น)"}, 502)
            rec.update(cid=ch.id, mid=msg.id, rt=time.time(),
                       media=[{"t": k, "url": a.url, "px": a.proxy_url or a.url, "w": a.width or 0, "h": a.height or 0} for (k, _, _), a in zip(media, msg.attachments)])
        async with lock:
            d = db(); lst = gp_all(); lst.insert(0, rec); del lst[200:]
            d["gposts"] = lst; save_json(DATA, d); gal["ver"] += 1
        return js({"ok": True})

    async def gal_post_del(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "เข้าสู่ระบบก่อน"}, 401)
        try: b = await req.json(); pid = str(b.get("id") or "")[:60]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        async with lock:
            lst = gp_all()
            hit = next((p for p in lst if "t_" + p["id"] == pid and int(p.get("uid", 0)) == int(s["uid"])), None)
            if not hit: return js({"ok": False, "error": "ลบได้เฉพาะโพสต์ของตัวเอง"}, 404)
            lst.remove(hit); d = db(); d["gposts"] = lst
            gc = d.setdefault("gcomments", {}); gc.pop(pid, None); gcm["v"] = gc
            glk_all().pop(pid, None); d["glikes"] = glk_all(); grx_all().pop(pid, None); d["grx"] = grx_all()
            save_json(DATA, d); gal["ver"] += 1
        if hit.get("mid"):
            try:
                ch = bot.get_channel(hit["cid"]) or await bot.fetch_channel(hit["cid"])
                await ch.get_partial_message(hit["mid"]).delete()
            except Exception: pass
        return js({"ok": True})

    # ================= 🔗 ซิงก์ ❤️ เว็บ ⇄ ดิสคอร์ด =================
    # • ดิส → เว็บ : ใครกดรีแอ็กชัน "อะไรก็ได้" ที่ข้อความรูป (ในห้องรูป/ห้องมีเดีย) = นับเป็น 1 ใจบนเว็บทันที (ฟัง raw event + ตรวจซ้ำทุก 3 ชม.)
    # • เว็บ → ดิส : บอทกดรีแอ็กชันแทนคนอื่นไม่ได้ จึงตอบใต้รูปด้วยข้อความ "🌐❤️ N คนกดใจจากเว็บ @ชื่อ…" แล้วแก้ไขตัวเลขให้อัตโนมัติ (ถอนใจ = ข้อความอัปเดต/หายไป)
    # • ใจรวมบนเว็บ = (คนกดบนเว็บ ∪ คนกดรีแอ็กชันในดิส) ไม่นับซ้ำ  · กดซ้ำบนเว็บ = ถอนทั้งสองฝั่ง (ถ้าบอทมีสิทธิ์ Manage Messages)
    gdc, gll_c = {"v": None}, {"v": None}
    gl_dirty = set()

    def gd_all():
        if gdc["v"] is None: gdc["v"] = db().get("gdlikes", {})
        return gdc["v"]

    def gll():
        if gll_c["v"] is None: gll_c["v"] = db().get("glog", {})
        return gll_c["v"]

    def gd_save():
        d = db(); d["gdlikes"] = gd_all(); d["glog"] = gll(); d["grx"] = grx_all(); d["gbr"] = gbr_all(); save_json(DATA, d)

    def item_loc(pid):
        """id รูป → (id ห้อง, id ข้อความดิสคอร์ด)"""
        if pid.startswith("t_"):
            p = next((p for p in gp_all() if "t_" + p["id"] == pid), None)
            return (int(p["cid"]), str(p["mid"])) if p and p.get("mid") else (0, "")
        return gal["cid"], pid.split("_")[0]

    # รีแอ็กชันแบบเฟซบุ๊ก: เว็บเลือกได้ 1 อย่างต่อคน (RXS) · ดิสคอร์ดกดอิโมจิอะไรก็ได้ (รวมอิโมจิเซิร์ฟเวอร์) → แสดงบนเว็บทั้งหมด
    RXS = ("👍", "❤️", "🥰", "😆", "😮", "😢", "😡")
    grc = {"v": None}
    def grx_all():
        if grc["v"] is None: grc["v"] = db().get("grx", {})
        return grc["v"]

    def canon(e):
        t = e.replace("\ufe0f", "")
        for r in RXS:
            if r.replace("\ufe0f", "") == t: return r
        return e

    def cx_info(e):
        m = re.match(r"^<(a?):\w+:(\d+)>$", e)
        if m: return {"e": e, "img": f"https://cdn.discordapp.com/emojis/{m.group(2)}.{'gif' if m.group(1) else 'png'}?size=48"}
        return {"e": e}

    def user_emojis(pid):
        """uid → [อิโมจิ] รวมเว็บ (ของเก่า = ❤️) + ดิสคอร์ด"""
        _, mid = item_loc(pid); out = {}
        for u in glk_all().get(pid, []): out[int(u)] = ["❤️"]
        for u, e in grx_all().get(pid, {}).items(): out[int(u)] = [canon(e)]
        if mid:
            for u, es in gd_all().get(mid, {}).items():
                lst = out.setdefault(int(u), [])
                for e in es:
                    e = canon(e)
                    if e not in lst: lst.append(e)
        return out

    def reacts_of(pid, me):
        ue = user_emojis(pid); cnt = {}
        for es in ue.values():
            for e in es: cnt[e] = cnt.get(e, 0) + 1
        rs = sorted(({**cx_info(e), "n": n} for e, n in cnt.items()), key=lambda r: -r["n"])
        return rs, ((ue.get(me) or [""])[0] if me else ""), len(ue)

    def known_mid(mid, cid):
        if cid == gal["cid"] and any(i["id"].startswith(mid + "_") for i in gal["items"]): return True
        return any(str(p.get("mid")) == mid for p in gp_all())

    def web_likers_of(mid):
        """รายชื่อ (uid, อิโมจิ) ที่กดบนเว็บ สำหรับข้อความดิสคอร์ดนี้"""
        glk, grx = glk_all(), grx_all()
        keys = [k for k in set(glk) | set(grx) if k.startswith(mid + "_")] + ["t_" + p["id"] for p in gp_all() if str(p.get("mid")) == mid]
        out = {}
        for k in keys:
            for u in glk.get(k, []): out[int(u)] = "❤️"
            for u, e in grx.get(k, {}).items(): out[int(u)] = canon(e)
        return list(out.items())

    async def gd_react(pl, add):
        if pl.user_id == bot.user.id: return
        if add and getattr(pl, "member", None) and pl.member.bot: return
        mid = str(pl.message_id)
        if not known_mid(mid, pl.channel_id): return
        uid, e = str(pl.user_id), str(pl.emoji)
        async with lock:
            dl = gd_all(); cur = dl.setdefault(mid, {}); lst = cur.setdefault(uid, [])
            if add:
                if e not in lst: lst.append(e)
            elif e in lst: lst.remove(e)
            if not lst: cur.pop(uid, None)
            if not cur: dl.pop(mid, None)
            if len(dl) > 1500:
                for k in list(dl):
                    if not known_mid(k, pl.channel_id): dl.pop(k, None)
            gd_save(); gal["ver"] += 1

    async def gd_on_add(pl): await gd_react(pl, True)
    async def gd_on_remove(pl): await gd_react(pl, False)

    async def gd_sync(m):
        """อ่านรีแอ็กชันจริงของข้อความ แล้วทับข้อมูลของข้อความนั้น (ผิดพลาด = ไม่แตะข้อมูลเดิม)"""
        cur = {}
        for r in m.reactions:
            async for u in r.users(limit=200):
                if u.bot: continue
                cur.setdefault(str(u.id), []).append(str(r.emoji))
        norm = lambda d: {k: sorted(v) for k, v in (d or {}).items()}
        async with lock:
            dl = gd_all(); mid = str(m.id)
            if norm(dl.get(mid)) == norm(cur): return False
            if cur: dl[mid] = cur
            else: dl.pop(mid, None)
            gd_save(); gal["ver"] += 1; return True

    async def gd_sync_many(msgs):
        try:
            dl = gd_all()
            for m in msgs:
                if m.reactions or str(m.id) in dl:
                    try: await gd_sync(m)
                    except Exception as e: print(f"   ⚠ ซิงก์รีแอ็กชันไม่สำเร็จ: {type(e).__name__}: {e}")
                    await asyncio.sleep(0.4)
        except Exception as e: print(f"   ⚠ ซิงก์รีแอ็กชัน: {type(e).__name__}: {e}")

    async def gd_unreact(cid, mid, uid):
        try:
            ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
            pm = ch.get_partial_message(int(mid))
            for e in list(gd_all().get(mid, {}).get(str(uid), [])):
                await pm.remove_reaction(e, discord.Object(id=uid))
            return True
        except Exception as e:
            print(f"   ✖ ถอนรีแอ็กชันในดิสไม่ได้ (ต้องมีสิทธิ์ Manage Messages): {type(e).__name__}: {e}")
            return False

    # เลขกำกับใต้รูป: 1-9 = 1️⃣-9️⃣ · 10 = 🔟 · มากกว่า 10 = 🔟➕
    KEYCAP = {n: [f"{n}\ufe0f\u20e3"] for n in range(1, 10)}
    KEYCAP[10] = ["\U0001F51F"]; KEYCAP[11] = ["\U0001F51F", "\u2795"]
    gbc = {"v": None}
    def gbr_all():
        if gbc["v"] is None: gbc["v"] = db().get("gbr", {})
        return gbc["v"]

    async def gl_render(mid):
        """เว็บ → ดิส: บอทกดรีแอ็กชันใต้รูปตามอิโมจิที่คนกดบนเว็บ (ถอนครบ = บอทถอนรีแอ็กชันออก)"""
        loc = next((c for c, k in [(gal["cid"], i["id"]) for i in gal["items"]] if k.startswith(mid + "_")), 0) or \
              next((int(p["cid"]) for p in gp_all() if str(p.get("mid")) == mid and p.get("cid")), 0)
        if not loc:
            if not gal["loaded"]: gl_dirty.add(mid)   # ยังโหลดห้องรูปไม่เสร็จ → ลองใหม่ทีหลัง
            return
        ch = bot.get_channel(loc) or await bot.fetch_channel(loc)
        pm = ch.get_partial_message(int(mid))
        old = gll().get(mid)
        if old:   # ของเดิม: ข้อความสรุปใจที่บอทตอบใต้รูป → ลบทิ้ง ใช้รีแอ็กชันแทน
            try: await ch.get_partial_message(int(old)).delete()
            except Exception: pass
            async with lock: gll().pop(mid, None); gd_save()
        want = []   # ซิงก์ทางเดียว ดิส → เว็บ: ไม่แสดงรีแอ็กชันจากเว็บในดิสแล้ว (ฟังก์ชันนี้เหลือไว้ลบรีแอ็กชัน/ข้อความเก่าของบอทเท่านั้น)
        have = list(gbr_all().get(mid, []))
        try:
            for e in have:
                if e not in want: await pm.remove_reaction(e, bot.user)
            for e in want:
                if e not in have: await pm.add_reaction(e)
        except discord.NotFound: return
        except discord.Forbidden:
            print("   ✖ บอทกดรีแอ็กชันใต้รูปไม่ได้ (ต้องมีสิทธิ์ Add Reactions + Read Message History ในห้องนั้น)"); return
        except discord.HTTPException as e:
            print(f"   ⚠ กดรีแอ็กชันใต้รูปไม่สำเร็จ: {e}"); return
        async with lock:
            if want: gbr_all()[mid] = want
            else: gbr_all().pop(mid, None)
            gd_save()

    async def gl_worker():
        for mid in list(gll()) + list(gbr_all()): gl_dirty.add(mid)   # เก็บกวาดข้อความ/รีแอ็กชันเก่าของบอทที่เคยแสดงใจจากเว็บ
        while True:
            await asyncio.sleep(2.5)
            try:
                for mid in list(gl_dirty)[:4]:
                    gl_dirty.discard(mid)
                    try: await gl_render(mid)
                    except Exception as e: print(f"   ⚠ อัปเดตข้อความสรุปใจ: {type(e).__name__}: {e}")
            except Exception: pass

    async def gl_on_delete(pl):
        mid = str(pl.message_id)
        if mid not in gd_all() and mid not in gll() and mid not in gbr_all(): return
        async with lock:
            gd_all().pop(mid, None); gbr_all().pop(mid, None); cur = gll().pop(mid, None); gd_save(); gal["ver"] += 1
        if cur:
            try:
                ch = bot.get_channel(pl.channel_id) or await bot.fetch_channel(pl.channel_id)
                await ch.get_partial_message(int(cur)).delete()
            except Exception: pass

    async def gal_like(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "เข้าสู่ระบบก่อนจึงจะรีแอ็กได้"}, 401)
        if limited(req, "glk", 60, 60): return js({"ok": False, "error": "กดถี่เกินไป รอสักครู่นะ"}, 429)
        try: b = await req.json(); pid = str(b.get("id") or "")[:60]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        if not gal_has(pid): return js({"ok": False, "error": "ไม่พบโพสต์นี้แล้ว"}, 404)
        uid = int(s["uid"]); cid, mid = item_loc(pid)
        has_any = uid in user_emojis(pid)
        if "emoji" in b:
            target = canon(str(b.get("emoji") or "")[:16])
            if target and target not in RXS: return js({"ok": False, "error": "รีแอ็กชันนี้ใช้ไม่ได้"}, 400)
        else: target = "" if has_any else "❤️"      # เวอร์ชันเก่า: กดเดียว = สลับ ❤️
        was_d = bool(mid) and str(uid) in gd_all().get(mid, {})
        if not target and was_d and not await gd_unreact(cid, mid, uid):   # ถอนใจ → ถอนรีแอ็กชันที่กดไว้ในดิสคอร์ดด้วย
            return js({"ok": False, "error": "ถอนรีแอ็กชันในดิสคอร์ดไม่ได้ ลองกดถอนในดิสคอร์ดเองนะ"}, 502)
        async with lock:
            lk_all, rx = glk_all(), grx_all()
            lst = lk_all.get(pid, [])
            if uid in lst: lst.remove(uid)
            if not lst: lk_all.pop(pid, None)
            m = rx.setdefault(pid, {})
            if target: m[str(uid)] = target
            else:
                m.pop(str(uid), None)
                if was_d:
                    dl = gd_all(); dm = dl.get(mid, {}); dm.pop(str(uid), None)
                    if not dm: dl.pop(mid, None)
            if not m: rx.pop(pid, None)
            if len(lk_all) + len(rx) > 1500:
                live = {i["id"] for i in gal["items"]} | {"t_" + p["id"] for p in gp_all()}
                for k in list(lk_all):
                    if k not in live: lk_all.pop(k, None)
                for k in list(rx):
                    if k not in live: rx.pop(k, None)
            d = db(); d["glikes"] = lk_all; d["grx"] = rx; d["gdlikes"] = gd_all(); save_json(DATA, d); gal["ver"] += 1
        return js({"ok": True})

    # ================= 📊 สถิติคนเข้าเว็บ + 💬 ห้องคอมเม้น (ฟอรั่ม) + 👋 คนเข้า/ออก =================
    xt = {"v": None, "dirty": False}
    BOT_UA = ("bot", "crawler", "spider", "preview", "facebookexternalhit", "slack", "whatsapp", "telegram", "curl", "python", "headless", "rv:38.0", "monitor", "uptime")
    SRC_OK = {"join", "leave", "cmt", "promo"}
    NONE_MENT = discord.AllowedMentions.none()

    def xt_all():
        if xt["v"] is None:
            v = db().get("xtrack")
            if not isinstance(v, dict): v = {}
            v.setdefault("salt", secrets.token_hex(8)); v.setdefault("days", {})
            xt["v"] = v
        return xt["v"]

    def req_ip(req):
        h = req.headers
        return (h.get("CF-Connecting-IP") or (h.get("X-Forwarded-For") or "").split(",")[0].strip() or req.remote or "")

    def vis_id(req):
        ua = req.headers.get("User-Agent", "")
        return hashlib.sha256((xt_all()["salt"] + req_ip(req) + ua).encode()).hexdigest()[:12]

    def is_bot_ua(req):
        ua = req.headers.get("User-Agent", "").lower()
        return (not ua) or any(k in ua for k in BOT_UA)

    def xt_day():
        k = now_th().strftime("%Y-%m-%d"); days = xt_all()["days"]
        if k not in days:
            days[k] = {"pv": {}, "u": {}, "src": {}, "su": {}, "clk": {}}
            for old in sorted(days)[:-90]: days.pop(old, None)
        return days[k]

    def xt_add_u(dct, key, vid):
        lst = dct.setdefault(key, [])
        if vid not in lst and len(lst) < 4000: lst.append(vid)

    def track_view(req, page):
        """นับคนเปิดหน้าเว็บ (ไม่นับบอท/ตัวดึงพรีวิวของดิสคอร์ด) + ลิงก์ที่มา ?s=join|leave|cmt|promo"""
        try:
            if is_bot_ua(req): return
            vid = vis_id(req); d = xt_day()
            d["pv"][page] = d["pv"].get(page, 0) + 1; xt_add_u(d["u"], page, vid)
            src = req.query.get("s", ""); src = src if src in SRC_OK else "direct"
            d["src"][src] = d["src"].get(src, 0) + 1; xt_add_u(d["su"], src, vid)
            xt["dirty"] = True
        except Exception: pass

    async def track(req):
        if limited(req, "trk", 90, 60) or is_bot_ua(req): return js({"ok": True})
        try: b = await req.json()
        except Exception: return js({"ok": True})
        if not isinstance(b, dict): return js({"ok": True})
        page = "gallery" if b.get("p") == "gallery" else "home"
        label = " ".join(str(b.get("l") or "").split())[:40]
        if not label: return js({"ok": True})
        d = xt_day(); key = f"{page}|{label}"
        if key not in d["clk"] and len(d["clk"]) >= 150: key = f"{page}|อื่นๆ"
        d["clk"][key] = d["clk"].get(key, 0) + 1; xt["dirty"] = True
        return js({"ok": True})

    async def xt_flush_loop():
        while True:
            await asyncio.sleep(20)
            if not xt["dirty"]: continue
            xt["dirty"] = False
            try:
                async with lock:
                    d = db(); d["xtrack"] = xt_all(); save_json(DATA, d)
            except Exception as e: print(f"   ⚠ บันทึกสถิติเว็บไม่สำเร็จ: {type(e).__name__}: {e}")

    PAGE_NAME = {"home": "🏠 หน้าหลัก", "gallery": "🖼️ แกลเลอรี"}
    SRC_NAME = {"join": "👋 DM ต้อนรับคนเข้าใหม่", "leave": "🚪 DM ตอนคนออก", "cmt": "💬 แจ้งคอมเม้น", "promo": "📣 โพสต์โปรโมท", "direct": "🔗 พิมพ์/แชร์ลิงก์เอง"}

    async def visits_send(i, n, label):
        days = xt_all()["days"]; today = now_th().date()
        keys = [(today - timedelta(days=k)).strftime("%Y-%m-%d") for k in range(n)]
        pv, uq, src, srcu, clk, allu, daily = {}, {}, {}, {}, {}, set(), []
        for k in reversed(keys):
            d = days.get(k)
            if not d: continue
            for p, c in d["pv"].items(): pv[p] = pv.get(p, 0) + c
            for p, l in d["u"].items(): uq.setdefault(p, set()).update(l); allu.update(l)
            for s_, c in d["src"].items(): src[s_] = src.get(s_, 0) + c
            for s_, l in d["su"].items(): srcu.setdefault(s_, set()).update(l)
            for kk, c in d["clk"].items(): clk[kk] = clk.get(kk, 0) + c
            daily.append((k[5:], sum(d["pv"].values()), len(set().union(*[set(v) for v in d["u"].values()]) if d["u"] else [])))
        e = discord.Embed(title=f"📊 สถิติเว็บบ้านโมชิ · {label}", color=0xFF6EC7, timestamp=datetime.now(timezone.utc))
        if not pv:
            e.description = "ยังไม่มีข้อมูลในช่วงนี้ — เริ่มนับตั้งแต่เปิดใช้เวอร์ชันนี้ (ไม่นับบอท/พรีวิวลิงก์)"
            return await i.response.send_message(embed=e, ephemeral=True)
        e.add_field(name="👥 คนเข้าเว็บ (ไม่ซ้ำ)", value=f"**{len(allu):,}** คน", inline=True)
        e.add_field(name="👁️ เข้าชมทั้งหมด", value=f"**{sum(pv.values()):,}** ครั้ง", inline=True)
        e.add_field(name="\u200b", value="\u200b", inline=True)
        e.add_field(name="📄 แยกตามหน้า", value="\n".join(f"{PAGE_NAME.get(p, p)} — {pv[p]:,} ครั้ง · {len(uq.get(p, ())):,} คน" for p in pv)[:1000], inline=False)
        e.add_field(name="🔗 คนกดมาจากลิงก์ไหน", value="\n".join(f"{SRC_NAME.get(s_, s_)} — {c:,} ครั้ง · {len(srcu.get(s_, ())):,} คน" for s_, c in sorted(src.items(), key=lambda x: -x[1]))[:1000] or "—", inline=False)
        top = sorted(clk.items(), key=lambda x: -x[1])[:10]
        if top:
            e.add_field(name="🔥 คนชอบกดดูอะไรมากสุด", value="\n".join(f"`{k.split('|')[0]}` {k.split('|', 1)[1]} — **{c:,}**" for k, c in top)[:1000], inline=False)
        if 1 < n <= 7 and daily:
            e.add_field(name="📅 รายวัน", value="\n".join(f"`{d}` {v:,} ครั้ง · {u:,} คน" for d, v, u in daily)[:1000], inline=False)
        e.set_footer(text="นับเฉพาะคนจริง · คนเดียวกันนับ 1 คน (เทียบจากอุปกรณ์/เครือข่าย)")
        await i.response.send_message(embed=e, ephemeral=True)

    # ---------- 💬 ห้องคอมเม้น (ฟอรั่ม): คอมเม้นจากเว็บเด้งเข้าฟอรั่ม + แจ้งเจ้าของโพสต์พร้อมลิงก์แกลเลอรี ----------
    cthc = {"v": None}
    cf_locks = {}

    def cth_all():
        if cthc["v"] is None: cthc["v"] = db().get("cthreads", {})
        return cthc["v"]

    def comments_forum():
        cid = db()["site"].get("cforum") or os.getenv("XMAS_COMMENT_FORUM", "")
        try: ch = bot.get_channel(int(cid)) if cid else None
        except Exception: ch = None
        return ch if isinstance(ch, discord.ForumChannel) else None

    def find_item(pid):
        if pid.startswith("t_"):
            p = next((p for p in gp_all() if "t_" + p["id"] == pid), None)
            if not p: return {}
            md = (p.get("media") or [{}])[0]
            th = (md.get("px") or md.get("url") or "") if md.get("t") == "i" else ""
            return {"by": p.get("name", "สมาชิก"), "uid": p.get("uid"), "text": p.get("text", ""), "thumb": th}
        return next((x for x in gal["items"] if x["id"] == pid), {})

    def post_link(pid): return f"{PUBLIC}/gallery?s=cmt#{pid}"

    def safe_txt(v, n): return discord.utils.escape_markdown(str(v or "")[:n]).replace("@", "@\u200b")

    async def cm_forward(pid, rec):
        try:
            forum = comments_forum()
            if not forum: return
            it = find_item(pid)
            if not it: return
            owner = it.get("uid")
            lk = cf_locks.setdefault(pid, asyncio.Lock())
            if len(cf_locks) > 500: cf_locks.clear()
            async with lk:
                th = None; tid = cth_all().get(pid)
                if tid:
                    try: th = bot.get_channel(int(tid)) or await bot.fetch_channel(int(tid))
                    except discord.NotFound: th = None
                if not th:
                    emb = discord.Embed(title=f"📸 โพสต์ของ {it.get('by', 'สมาชิก')}"[:250], color=0xFF6EC7, url=post_link(pid),
                                        description=(safe_txt(it.get("text"), 400) or "(โพสต์รูปภาพ)"))
                    if it.get("thumb"): emb.set_image(url=it["thumb"])
                    emb.set_footer(text="ห้องคอมเม้นของโพสต์นี้ · ตอบคอมเม้นได้ที่เว็บบ้านโมชิ")
                    v0 = discord.ui.View(timeout=None); v0.add_item(discord.ui.Button(label="🖼️ เปิดโพสต์บนเว็บ", url=post_link(pid)))
                    title = f"💬 {it.get('by', 'สมาชิก')} · {(it.get('text') or 'รูปภาพ')}"[:95]
                    twm = await forum.create_thread(name=title, content=f"💬 ห้องคอมเม้นของโพสต์ **{safe_txt(it.get('by', 'สมาชิก'), 40)}**", embed=emb, view=v0, allowed_mentions=NONE_MENT)
                    th = twm.thread
                    async with lock:
                        cth_all()[pid] = th.id; d = db(); d["cthreads"] = cth_all(); save_json(DATA, d)
                lines = []
                if owner and int(owner) != int(rec.get("uid", 0)): lines.append(f"🔔 <@{owner}> มีคนคอมเม้นที่โพสต์ของคุณ")
                lines.append(f"💬 **{safe_txt(rec.get('name'), 40)}**: {safe_txt(rec.get('text'), 300)}")
                v = discord.ui.View(timeout=None); v.add_item(discord.ui.Button(label="💬 ไปตอบคอมเม้นบนเว็บ", url=post_link(pid)))
                am = discord.AllowedMentions(users=[discord.Object(id=int(owner))]) if owner else NONE_MENT
                msg = await th.send("\n".join(lines), view=v, allowed_mentions=am)
                async with lock:
                    rec["fm"], rec["ft"] = msg.id, th.id
                    d = db(); d["gcomments"] = cm_all(); save_json(DATA, d)
        except Exception as e:
            print(f"   ✖ ส่งคอมเม้นเข้าห้องฟอรั่มไม่สำเร็จ: {type(e).__name__}: {e}")

    async def cm_unforward(hit):
        if not (hit.get("fm") and hit.get("ft")): return
        try:
            th = bot.get_channel(int(hit["ft"])) or await bot.fetch_channel(int(hit["ft"]))
            await th.get_partial_message(int(hit["fm"])).delete()
        except Exception: pass

    # ---------- 👋 คนเข้า / ออก: DM ลิงก์เว็บบ้านโมชิ + (ตอนออก) แบบฟอร์ม "ทำไมถึงออก" ----------
    dm_recent, dm_last = [], {}

    def dm_ok(kind, uid):
        now = time.time()
        if now - dm_last.get((kind, uid), 0) < 6 * 3600: return False
        dm_recent[:] = [t for t in dm_recent if now - t < 60]
        if len(dm_recent) >= 12: return False      # กันเข้า/ออกรัวๆ (เช่น โดนบอทบุก) ไม่ให้บอทโดนจำกัด
        dm_recent.append(now); dm_last[(kind, uid)] = now
        if len(dm_last) > 2000: dm_last.clear()
        return True

    def home_url(src): return f"{PUBLIC}/?s={src}"
    def gal_url(src): return f"{PUBLIC}/gallery?s={src}"

    def promo_line():
        t = now_th()
        if t.month == 12 and t.day <= 25: return f"🎄 วันนี้วันที่ {t.day} ของปฏิทินรับดาว — เข้าเว็บไปรับดาววันนี้ได้เลย!"
        return "🎄 ที่เว็บมีกิจกรรมคริสต์มาส 25 วัน · ปฏิทินรับดาว · Secret Santa และแกลเลอรีรูป"

    def leave_channel():
        cid = db()["site"].get("leave") or os.getenv("XMAS_LEAVE_CHANNEL", "")
        try: return bot.get_channel(int(cid)) if cid else None
        except Exception: return None

    def invite_link(): return db()["site"].get("invite") or ""

    def link_row(view, pairs):
        for lab, url in pairs:
            if url: view.add_item(discord.ui.Button(label=lab, url=url))
        return view

    def join_payload(name):
        e = discord.Embed(title=f"🎄 ยินดีต้อนรับสู่ MOCHI HOUSE, {name}!"[:250], color=0xFF6EC7,
                          description=f"บ้านโมชิดีใจที่เธอมาอยู่ด้วยกัน 💖\n{promo_line()}\n\nกดปุ่มด้านล่างเพื่อเข้าเว็บบ้านโมชิ แล้วมาเล่นด้วยกันนะ")
        e.set_footer(text="MOCHI HOUSE · Merry Christmas 2026")
        return e, link_row(discord.ui.View(timeout=None), [("🌐 เข้าเว็บบ้านโมชิ", home_url("join")), ("🖼️ ดูแกลเลอรี", gal_url("join"))])

    def leave_links():
        return [("🌐 เว็บบ้านโมชิ", home_url("leave")), ("💬 กลับเข้าบ้านโมชิ", invite_link())]

    class LeaveModal(discord.ui.Modal, title="ทำไมถึงออกจากบ้านโมชิ"):
        reason = discord.ui.TextInput(label="เหตุผลหลักที่ออก", placeholder="เช่น เซิร์ฟเงียบ / ไม่ค่อยมีเวลา / ไม่ถูกกับบรรยากาศ", max_length=150, required=True)
        better = discord.ui.TextInput(label="อยากให้บ้านโมชิปรับปรุงอะไร (ไม่บังคับ)", style=discord.TextStyle.paragraph, max_length=600, required=False)

        async def on_submit(self, i: discord.Interaction):
            q = db().get("leaveq", {}); e0 = q.get(str(i.user.id))
            if not e0 or e0.get("done"): return await i.response.send_message("ฟอร์มนี้ส่งไปแล้ว ขอบคุณนะ 💖", ephemeral=True)
            emb = discord.Embed(title="📝 ทำไมถึงออกจากบ้านโมชิ", color=0xFF6EC7, timestamp=datetime.now(timezone.utc))
            emb.set_author(name=f"{e0.get('name', '?')} ({e0.get('tag', '')})"[:250], icon_url=e0.get("av") or None)
            emb.add_field(name="💬 เหตุผลหลัก", value=self.reason.value[:1000] or "—", inline=False)
            if self.better.value.strip(): emb.add_field(name="💡 อยากให้ปรับปรุง", value=self.better.value[:1000], inline=False)
            emb.add_field(name="🕒 อยู่ในเซิร์ฟ", value=e0.get("stay") or "—", inline=True)
            emb.set_footer(text=f"User ID {i.user.id}" + (" · 🧪 ทดสอบ" if e0.get("test") else ""))
            ch = leave_channel()
            if ch:
                try: await ch.send(embed=emb, allowed_mentions=NONE_MENT)
                except Exception as ex: print(f"   ✖ ส่งคำตอบ 'ทำไมถึงออก' เข้าห้องไม่ได้: {ex}")
            async with lock:
                d = db(); d.setdefault("leaveq", {}).setdefault(str(i.user.id), {})["done"] = True; save_json(DATA, d)
            thanks = discord.Embed(title="💖 ขอบคุณที่บอกเรานะ", color=0xFF6EC7, description="เราจะเอาไปปรับปรุงบ้านโมชิให้ดีขึ้น · กลับมาเมื่อไหร่ก็ได้เลย")
            try: await i.response.edit_message(embed=thanks, view=link_row(discord.ui.View(timeout=None), leave_links()))
            except Exception: await i.response.send_message("💖 ขอบคุณที่บอกเรานะ", ephemeral=True)

        async def on_error(self, i: discord.Interaction, error: Exception):
            print(f"   ✖ LeaveModal: {type(error).__name__}: {error}")
            try: await i.response.send_message("⚠️ ส่งไม่สำเร็จ ลองใหม่อีกครั้งนะ", ephemeral=True)
            except Exception: pass

    class LeaveView(discord.ui.View):
        def __init__(self, links=None):
            super().__init__(timeout=None)
            link_row(self, links or [])

        @discord.ui.button(label="📝 กรอกแบบฟอร์ม", style=discord.ButtonStyle.primary, custom_id="xmasleave:form")
        async def form_btn(self, i: discord.Interaction, b: discord.ui.Button):
            e0 = db().get("leaveq", {}).get(str(i.user.id))
            if not e0 or e0.get("done"): return await i.response.send_message("ฟอร์มนี้ส่งไปแล้วหรือหมดอายุแล้ว ขอบคุณนะ 💖", ephemeral=True)
            await i.response.send_modal(LeaveModal())

        @discord.ui.button(label="🙅 ขอไม่ตอบ", style=discord.ButtonStyle.secondary, custom_id="xmasleave:skip")
        async def skip_btn(self, i: discord.Interaction, b: discord.ui.Button):
            e0 = db().get("leaveq", {}).get(str(i.user.id))
            if not e0 or e0.get("done"): return await i.response.send_message("เรียบร้อยแล้วนะ 💖", ephemeral=True)
            async with lock:
                d = db(); d.setdefault("leaveq", {}).setdefault(str(i.user.id), {})["done"] = True; save_json(DATA, d)
            ch = leave_channel()
            if ch:
                emb = discord.Embed(color=0x99AAB5, timestamp=datetime.now(timezone.utc),
                                    description=f"⚠️ ผู้ใช้ชื่อ **{discord.utils.escape_markdown(str(e0.get('name', '?')))}** ({discord.utils.escape_markdown(str(e0.get('tag', '')))}) ไม่ต้องการให้คำตอบว่าทำไมถึงออก")
                emb.set_footer(text=f"User ID {i.user.id}" + (" · 🧪 ทดสอบ" if e0.get("test") else ""))
                try: await ch.send(embed=emb, allowed_mentions=NONE_MENT)
                except Exception as ex: print(f"   ✖ ส่งแจ้งเตือน 'ไม่ตอบ' เข้าห้องไม่ได้: {ex}")
            bye = discord.Embed(title="ได้เลย ไม่เป็นไรนะ 💖", color=0xFF6EC7, description="ขอบคุณที่เคยอยู่ด้วยกัน · ประตูบ้านโมชิเปิดให้เสมอ")
            try: await i.response.edit_message(embed=bye, view=link_row(discord.ui.View(timeout=None), leave_links()))
            except Exception: await i.response.send_message("ได้เลย ไม่เป็นไรนะ 💖", ephemeral=True)

    def leave_payload(name, with_form):
        desc = ("ขอบคุณที่เคยเป็นส่วนหนึ่งของ **MOCHI HOUSE** 💖\n" + promo_line() + "\nกลับมาเมื่อไหร่ก็ได้นะ — บ้านโมชิยังมีเพื่อนใหม่รออยู่เสมอ")
        if with_form: desc += "\n\n**บอกเราหน่อยได้ไหมว่าทำไมถึงออก?** จะได้ปรับปรุงบ้านให้น่าอยู่ขึ้น 🙏"
        e = discord.Embed(title=f"👋 แล้วเจอกันใหม่นะ {name}"[:250], color=0xFF6EC7, description=desc)
        e.set_footer(text="MOCHI HOUSE · Merry Christmas 2026")
        return e, (LeaveView(leave_links()) if with_form else link_row(discord.ui.View(timeout=None), leave_links()))

    async def leave_note(text):
        ch = leave_channel()
        if ch:
            try: await ch.send(embed=discord.Embed(color=0x99AAB5, description=text), allowed_mentions=NONE_MENT)
            except Exception: pass

    async def xm_on_join(member):
        try:
            gd = guild()
            if member.bot or not gd or member.guild.id != gd.id or not dm_ok("join", member.id): return
            e, v = join_payload(member.display_name)
            await member.send(embed=e, view=v)
        except discord.Forbidden: pass     # ผู้ใช้ปิด DM
        except Exception as ex: print(f"   ⚠ ส่ง DM ต้อนรับไม่สำเร็จ: {type(ex).__name__}: {ex}")

    async def xm_on_remove(member):
        try:
            gd = guild()
            if member.bot or not gd or member.guild.id != gd.id: return
            await asyncio.sleep(3)
            try:                                   # โดนแบน/เตะ = ไม่ส่งแบบฟอร์ม (ออกเองเท่านั้น)
                await gd.fetch_ban(member); return
            except discord.NotFound: pass
            except Exception: pass
            try:
                async for en in gd.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                    if en.target and en.target.id == member.id and (datetime.now(timezone.utc) - en.created_at).total_seconds() < 20: return
            except Exception: pass
            if not dm_ok("leave", member.id): return
            with_form = leave_channel() is not None
            stay = f"{(datetime.now(timezone.utc) - member.joined_at).days} วัน" if member.joined_at else ""
            if with_form:
                async with lock:
                    d = db(); q = d.setdefault("leaveq", {})
                    q[str(member.id)] = {"name": member.display_name, "tag": str(member), "av": str(member.display_avatar.replace(size=64, format="png").url), "stay": stay, "t": int(time.time()), "done": False}
                    if len(q) > 500:
                        for k in sorted(q, key=lambda k: q[k].get("t", 0))[:100]: q.pop(k, None)
                    save_json(DATA, d)
            e, v = leave_payload(member.display_name, with_form)
            try: await member.send(embed=e, view=v)
            except discord.Forbidden:
                await leave_note(f"📭 ส่งข้อความถามเหตุผลให้ **{discord.utils.escape_markdown(member.display_name)}** ไม่ได้ (ปิด DM หรือบอทไม่มีเซิร์ฟร่วมแล้ว)")
        except Exception as ex: print(f"   ⚠ ส่ง DM ตอนออกไม่สำเร็จ: {type(ex).__name__}: {ex}")

    # =====================================================================================
    # 🎛️ ห้องควบคุมเว็บ (เฉพาะแอดมิน) + 🎄 ห้องเมนูเว็บ (ทุกคน) — ทุกอย่างเป็นปุ่ม ไม่ต้องพิมพ์คำสั่ง
    # คำสั่งเดียวที่เหลือ: /xmas (แอดมิน) — สร้าง/ซ่อมห้องทั้งสองให้อัตโนมัติ (ใช้ซ้ำได้ ไม่ทำของเดิมหาย)
    # =====================================================================================
    ensure_done = {"v": False}

    def ensure_ids(d):
        ch = False
        for key in ("banners", "partners", "events", "signups"):
            for it in d[key]:
                if not it.get("id"): it["id"] = secrets.token_urlsafe(4); ch = True
        return ch

    def by_id(rows, rid): return next((x for x in rows if x.get("id") == rid), None)

    async def guard(i):
        if is_admin(i): return True
        await deny(i); return False

    def p_label(p): return f"{'🤝' if p.get('kind') == 'person' else '🌐'} {p.get('name') or '(ใช้ชื่อจากดิสคอร์ด)'}" + (" 📣" if p.get("promo") else "")
    def b_label(b): return f"{'🙈' if b.get('off') else b.get('icon', '🎄')} {b.get('title', '')}"

    async def load_rows(key):
        async with lock:
            d = db(); ch = ensure_ids(d)
            if key == "events" and seed_events(d): ch = True
            if ch: save_json(DATA, d)
            return list(d[key])

    def seed_events(d):
        """ครั้งแรกที่แอดมินเปิดแผงกิจกรรม: คัดลอกตารางจากไฟล์ xmas_config.json มาเป็นของในฐานข้อมูล แล้วแก้ผ่านปุ่มได้เลย"""
        if d.get("events_custom"): return False
        d["events"] = [dict(e) for e in cfg().get("events", []) if isinstance(e, dict)]
        d["events_custom"] = True; ensure_ids(d); return True

    def ti(label, default=None, **kw):
        """TextInput สร้างใหม่ทุกครั้ง (กันค่าปนกันระหว่างแอดมินหลายคน)"""
        d = (default or "")
        if kw.get("max_length"): d = d[:kw["max_length"]]
        return discord.ui.TextInput(label=label[:45], default=d or None, **kw)

    # ---------- ตัวเลือกรายการ (แบ่งหน้าอัตโนมัติถ้าเกิน 25) ----------
    class PickView(discord.ui.View):
        def __init__(self, rows, label_fn, on_pick, placeholder):
            super().__init__(timeout=180)
            self.rows, self.label_fn, self.on_pick, self.ph, self.page = rows, label_fn, on_pick, placeholder, 0
            self.build()

        def build(self):
            self.clear_items()
            per = 25; pages = max(1, (len(self.rows) + per - 1) // per); self.page = max(0, min(self.page, pages - 1))
            chunk = self.rows[self.page * per:(self.page + 1) * per]
            sel = discord.ui.Select(placeholder=self.ph, min_values=1, max_values=1, row=0,
                                    options=[discord.SelectOption(label=f"{self.page * per + k + 1}. {self.label_fn(r)}"[:100], value=r["id"]) for k, r in enumerate(chunk)])
            async def picked(i): await self.on_pick(i, sel.values[0])
            sel.callback = picked; self.add_item(sel)
            if pages > 1:
                prev = discord.ui.Button(label="◀ ก่อนหน้า", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
                nxt = discord.ui.Button(label=f"ถัดไป ▶ ({self.page + 1}/{pages})", style=discord.ButtonStyle.secondary, disabled=self.page >= pages - 1, row=1)
                async def go(i, step): self.page += step; self.build(); await i.response.edit_message(view=self)
                async def p_cb(i): await go(i, -1)
                async def n_cb(i): await go(i, 1)
                prev.callback, nxt.callback = p_cb, n_cb; self.add_item(prev); self.add_item(nxt)

    async def pick(i, key, label_fn, on_pick, ph, empty):
        rows = await load_rows(key)
        if not rows: return await say(i, empty)
        await i.response.send_message("เลือกรายการ 👇", view=PickView(rows, label_fn, on_pick, ph), ephemeral=True)

    class ConfirmView(discord.ui.View):
        def __init__(self, on_yes):
            super().__init__(timeout=60); self.on_yes = on_yes

        @discord.ui.button(label="ยืนยัน", emoji="🗑️", style=discord.ButtonStyle.danger)
        async def yes(self, i: discord.Interaction, b: discord.ui.Button): await self.on_yes(i)

        @discord.ui.button(label="ยกเลิก", style=discord.ButtonStyle.secondary)
        async def no(self, i: discord.Interaction, b: discord.ui.Button): await i.response.edit_message(content="ยกเลิกแล้ว", view=None)

    # ---------- ใส่รูป: อัปโหลดจากเครื่อง (ส่งรูปในห้อง) หรือวางลิงก์ ----------
    class ImageUrlModal(discord.ui.Modal):
        def __init__(self, apply_fn):
            super().__init__(title="ใส่ลิงก์รูป"); self.apply_fn = apply_fn
            self.f = ti("ลิงก์รูป https:// (เว้นว่าง = ล้างรูป)", required=False, max_length=400)
            self.add_item(self.f)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            v = self.f.value.strip()
            if v in ("", "-"): u = ""
            else:
                u = clean_url(v)
                if not u: return await say(i, "⚠️ ลิงก์ต้องขึ้นต้นด้วย `https://`")
            await i.response.send_message(await self.apply_fn(u), ephemeral=True)

    def add_image_buttons(view, apply_fn, row=None, l1="อัปโหลดรูปจากเครื่อง", l2="ใช้ลิงก์รูป", e1="🖼️"):
        b1 = discord.ui.Button(label=l1, emoji=e1, style=discord.ButtonStyle.primary, row=row)
        b2 = discord.ui.Button(label=l2, emoji="🔗", style=discord.ButtonStyle.secondary, row=row)

        async def up_cb(i: discord.Interaction):
            if not await guard(i): return
            await i.response.send_message("📎 ส่งรูป (png / jpg / gif / webp) ในห้องนี้ภายใน 90 วินาที — บอทเก็บรูปแล้วลบข้อความรูปให้เอง", ephemeral=True)
            def chk(m): return m.author.id == i.user.id and m.channel.id == i.channel_id and bool(m.attachments)
            try: m = await bot.wait_for("message", check=chk, timeout=90)
            except asyncio.TimeoutError: return await i.followup.send("⌛ หมดเวลา กดปุ่มอัปโหลดใหม่ได้เลย", ephemeral=True)
            up, err = await save_upload(m.attachments[0])
            try: await m.delete()
            except Exception: pass
            if err: return await i.followup.send("⚠️ " + err, ephemeral=True)
            await i.followup.send(await apply_fn(up), ephemeral=True)

        async def url_cb(i: discord.Interaction):
            if not await guard(i): return
            await i.response.send_modal(ImageUrlModal(apply_fn))

        b1.callback, b2.callback = up_cb, url_cb
        view.add_item(b1); view.add_item(b2)

    # ---------- 🤝 พาร์ทเนอร์ ----------
    def clean_promo(t):
        t = (t or "").replace("\r\n", "\n").replace("\r", "\n")
        t = "\n".join(x.rstrip() for x in t.split("\n")).strip()
        return re.sub(r"\n{3,}", "\n\n", t)[:1500]

    def partner_img_apply(pid, field, what):
        async def apply(path):
            async with lock:
                d2 = db(); q = by_id(d2["partners"], pid)
                if not q: return "⚠️ ไม่พบรายการนี้แล้ว"
                if q.get(field) != path: drop_upload(q.get(field))
                q[field] = path; save_json(DATA, d2); cache["site"] = None
            return f"✅ ตั้ง{what}แล้ว — ขึ้นบนเว็บภายใน ~10 วินาที" if path else f"✅ ล้าง{what}แล้ว"
        return apply

    def partner_img_view(pid, both=True):
        v = discord.ui.View(timeout=300)
        add_image_buttons(v, partner_img_apply(pid, "banner", "แบนเนอร์"), row=0, l1="อัปโหลดแบนเนอร์", l2="ลิงก์แบนเนอร์", e1="🏞️")
        if both: add_image_buttons(v, partner_img_apply(pid, "image", "รูปโปรไฟล์"), row=1, l1="อัปโหลดรูปโปรไฟล์", l2="ลิงก์รูปโปรไฟล์")
        return v

    class PartnerModal(discord.ui.Modal):
        def __init__(self, kind, pid=None, user=None, cur=None):
            sv = kind == "server"; cur = cur or {}
            super().__init__(title="แก้ไขพาร์ทเนอร์" if pid else ("เพิ่มดิสคอร์ดพาร์ทเนอร์" if sv else "เพิ่มพาร์ทเนอร์บุคคล"))
            self.kind, self.pid, self.user = kind, pid, user
            has_uid = bool(user or cur.get("uid"))
            self.f_name = ti("ชื่อดิสคอร์ด" if sv else "ชื่อที่แสดง", cur.get("name") or (user.display_name if user else ""), max_length=48, required=sv or not has_uid)
            self.f_title = ti("ป้ายสั้นๆ เช่น พาร์ทเนอร์หลัก", cur.get("title"), max_length=24, required=False)
            self.f_desc = ti("คำอธิบายสั้นๆ ใต้ชื่อ", cur.get("desc"), max_length=140, required=False)
            self.f_link = ti("ลิงก์เชิญ (https://discord.gg/…)" if sv else "ลิงก์โปรไฟล์ (https://)", cur.get("link"), max_length=400, required=sv)
            self.f_promo = ti("คำโปรโมท (ขึ้นเมื่อกดดูรายละเอียด)", cur.get("promo"), max_length=1500, required=False, style=discord.TextStyle.paragraph,
                              placeholder="แนะนำดิสนี้ได้หลายบรรทัด เช่น มีอะไรบ้าง ห้องไหนเด่น กิจกรรม")
            for x in (self.f_name, self.f_title, self.f_desc, self.f_link, self.f_promo): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            sv = self.kind == "server"
            f, err = clean_partner(self.f_name.value, self.f_title.value, self.f_desc.value, None, self.f_link.value, self.f_promo.value)
            if err: return await say(i, "⚠️ " + err)
            if sv and not (f.get("name") and f.get("link")): return await say(i, "⚠️ ดิสคอร์ดพาร์ทเนอร์ ต้องมีทั้งชื่อและลิงก์เชิญ (https://)")
            async with lock:
                d = db(); ensure_ids(d); rows = d["partners"]
                if self.pid:
                    p = by_id(rows, self.pid)
                    if not p: return await say(i, "⚠️ ไม่พบรายการนี้ (อาจถูกลบไปแล้ว)")
                    if not f.get("name") and not (sv or p.get("uid")): return await say(i, "⚠️ ต้องมีชื่อที่แสดง")
                    p.update(f)
                else:
                    if len(rows) >= MAX_PARTNERS: return await say(i, f"⚠️ มีพาร์ทเนอร์ครบ {MAX_PARTNERS} แล้ว ลบอันเก่าก่อน")
                    if not f.get("name") and not self.user: return await say(i, "⚠️ ใส่ชื่อ หรือเลือกสมาชิกอย่างใดอย่างหนึ่ง")
                    p = {"id": secrets.token_urlsafe(4), "kind": self.kind, "name": "", "title": "", "desc": "", "image": "", "link": "", "promo": "", "uid": 0, "av": ""}
                    p.update(f)
                    if self.user and not sv:
                        p["uid"] = self.user.id; p["av"] = str(self.user.display_avatar.replace(size=128, format="webp").url)
                        if not p["name"]: p["name"] = self.user.display_name
                    rows.append(p)
                save_json(DATA, d); cache["site"] = None; pid = p["id"]

            v = partner_img_view(pid)
            await i.response.send_message(f"✅ {'แก้ไข' if self.pid else 'เพิ่ม'}พาร์ทเนอร์แล้ว: **{p_label(p)}**\nขึ้นบนเว็บภายใน ~10 วินาที"
                                          f"\n-# อยากใส่แบนเนอร์หลังโปรไฟล์ / รูปโปรไฟล์ กดปุ่มด้านล่าง (ไม่ใส่ก็ได้)", view=v, ephemeral=True)

    class PromoModal(discord.ui.Modal):
        def __init__(self, pid, cur):
            super().__init__(title="ตั้งคำโปรโมทของดิสนี้"); self.pid = pid
            self.f = ti("คำโปรโมท (เว้นว่าง = ลบคำโปรโมท)", cur, max_length=1500, required=False, style=discord.TextStyle.paragraph,
                        placeholder="ข้อความนี้จะเด้งขึ้นเมื่อคนกด “ดูรายละเอียด” บนหน้าพาร์ทเนอร์ · ขึ้นบรรทัดใหม่ได้ · วางลิงก์ https:// ได้")
            self.add_item(self.f)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            async with lock:
                d = db(); ensure_ids(d); p = by_id(d["partners"], self.pid)
                if not p: return await say(i, "⚠️ ไม่พบรายการนี้ (อาจถูกลบไปแล้ว)")
                p["promo"] = clean_promo(self.f.value); save_json(DATA, d); cache["site"] = None
            await i.response.send_message(f"✅ {'ตั้ง' if p['promo'] else 'ลบ'}คำโปรโมทของ **{p.get('name') or 'พาร์ทเนอร์'}** แล้ว — ขึ้นบนเว็บภายใน ~10 วินาที", ephemeral=True)

    class MoveModal(discord.ui.Modal):
        def __init__(self, key, rid):
            super().__init__(title="ย้ายลำดับ"); self.key, self.rid = key, rid
            self.f = ti("ลำดับใหม่ (1 = แสดงก่อน)", required=True, max_length=3); self.add_item(self.f)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            try: to = int(self.f.value.strip())
            except ValueError: return await say(i, "⚠️ ใส่เป็นตัวเลข")
            async with lock:
                d = db(); ensure_ids(d); rows = d[self.key]; it = by_id(rows, self.rid)
                if not it or not 1 <= to <= len(rows): return await say(i, "⚠️ ลำดับไม่ถูกต้อง")
                rows.remove(it); rows.insert(to - 1, it); save_json(DATA, d); cache["bn" if self.key == "banners" else "site"] = None
                txt = banner_list_text(rows) if self.key == "banners" else signup_list_text(rows, d["regs"]) if self.key == "signups" else partner_text(rows)
            await i.response.send_message("✅ ย้ายแล้ว\n" + txt, ephemeral=True)

    class PersonStartView(discord.ui.View):
        def __init__(self): super().__init__(timeout=180)

        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="เลือกสมาชิก (ดึงชื่อ + รูปให้อัตโนมัติ)", min_values=1, max_values=1, row=0)
        async def pick_user(self, i: discord.Interaction, s: discord.ui.UserSelect): await i.response.send_modal(PartnerModal("person", user=s.values[0]))

        @discord.ui.button(label="ไม่ผูกสมาชิก · กรอกเอง", style=discord.ButtonStyle.secondary, row=1)
        async def manual(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(PartnerModal("person"))

    async def partner_edit(i, pid):
        p = by_id(db()["partners"], pid)
        if not p: return await say(i, "⚠️ ไม่พบรายการนี้")
        await i.response.send_modal(PartnerModal(p.get("kind", "person"), pid=pid, cur=p))

    async def partner_promo(i, pid):
        p = by_id(db()["partners"], pid)
        if not p: return await say(i, "⚠️ ไม่พบรายการนี้")
        await i.response.send_modal(PromoModal(pid, p.get("promo", "")))

    async def partner_cover(i, pid):
        p = by_id(db()["partners"], pid)
        if not p: return await say(i, "⚠️ ไม่พบรายการนี้")
        await i.response.edit_message(content=f"🏞️ **{p_label(p)}**\nตั้งแบนเนอร์ (รูปปกด้านหลังโปรไฟล์) หรือรูปโปรไฟล์ — ใส่ลิงก์เว้นว่าง = ล้างรูป\n-# แนะนำรูปแนวนอน กว้าง ~3:1", view=partner_img_view(pid))

    async def partner_move(i, pid): await i.response.send_modal(MoveModal("partners", pid))

    async def partner_remove(i, pid):
        p = by_id(db()["partners"], pid)
        if not p: return await say(i, "⚠️ ไม่พบรายการนี้")
        async def yes(i2):
            async with lock:
                d = db(); q = by_id(d["partners"], pid)
                if not q: return await i2.response.edit_message(content="⚠️ ไม่พบรายการนี้แล้ว", view=None)
                d["partners"].remove(q); save_json(DATA, d); cache["site"] = None; drop_upload(q.get("image")); drop_upload(q.get("banner"))
            await i2.response.edit_message(content=f"🗑️ ลบ **{q.get('name') or 'พาร์ทเนอร์'}** แล้ว", view=None)
        await i.response.edit_message(content=f"ลบ **{p_label(p)}** ใช่ไหม?", view=ConfirmView(yes))

    # ---------- 🎞️ แบนเนอร์ ----------
    class BannerModal(discord.ui.Modal):
        def __init__(self, bid=None, cur=None):
            cur = cur or {}
            super().__init__(title="แก้ไขแบนเนอร์" if bid else "เพิ่มแบนเนอร์กิจกรรม"); self.bid = bid
            self.f_title = ti("ชื่อกิจกรรม", cur.get("title"), max_length=48, required=True)
            self.f_desc = ti("คำอธิบายสั้นๆ", cur.get("desc"), max_length=140, required=False)
            self.f_date = ti("วันที่ YYYY-MM-DD (ไม่ใส่ก็ได้)", cur.get("date"), max_length=10, required=False)
            self.f_time = ti("เวลา HH:MM เช่น 20:00 (ไม่ใส่ก็ได้)", cur.get("time"), max_length=5, required=False)
            self.f_link = ti("ลิงก์ปุ่ม (https:// หรือ #signup)", cur.get("link"), max_length=400, required=False)
            for x in (self.f_title, self.f_desc, self.f_date, self.f_time, self.f_link): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            f, err = clean_fields(self.f_title.value, self.f_desc.value, self.f_date.value, self.f_time.value, None, None, None, self.f_link.value, None)
            if err: return await say(i, "⚠️ " + err)
            if not f.get("title"): return await say(i, "⚠️ ต้องใส่ชื่อกิจกรรม")
            async with lock:
                d = db(); ensure_ids(d); rows = d["banners"]
                if self.bid:
                    b = by_id(rows, self.bid)
                    if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้ (อาจถูกลบไปแล้ว)")
                    b.update(f)
                else:
                    if len(rows) >= MAX_BANNERS: return await say(i, f"⚠️ มีแบนเนอร์ครบ {MAX_BANNERS} อันแล้ว ลบอันเก่าก่อน")
                    b = {"id": secrets.token_urlsafe(4), "icon": "🎄", "title": "", "desc": "", "date": "", "time": "", "theme": "pink", "image": "", "link": "", "label": ""}
                    b.update(f); rows.append(b)
                save_json(DATA, d); cache["bn"] = None; bid = b["id"]
            await i.response.send_message(f"✅ {'แก้ไข' if self.bid else 'เพิ่ม'}แบนเนอร์แล้ว: **{b_label(b)}**\nขึ้นบนเว็บภายใน ~1 นาที\n-# ปรับสี / ไอคอน / ปุ่ม / รูปพื้นหลังต่อได้ด้านล่าง · แนะนำรูปแนวนอน 16:9 (เช่น 1280×720) — มือถือจะเห็นแบนเนอร์เต็มทั้งภาพ ไม่โดนตัด",
                                          view=BannerTweakView(bid), ephemeral=True)

    class IconModal(discord.ui.Modal):
        def __init__(self, bid, cur):
            super().__init__(title="ไอคอน / ป้ายเล็ก / ปุ่ม"); self.bid = bid
            self.f_icon = ti("อีโมจิ เช่น 🎤", cur.get("icon"), max_length=8, required=False)
            self.f_label = ti("ป้ายเล็ก เช่น HOT / ใหม่ (ว่าง = นับถอยหลัง)", cur.get("label"), max_length=24, required=False)
            self.f_cta = ti("ข้อความบนปุ่ม (ว่าง = ดูรายละเอียด)", cur.get("cta"), max_length=20, required=False, placeholder="เช่น สมัครเลย · ไปดูเลย")
            self.add_item(self.f_icon); self.add_item(self.f_label); self.add_item(self.f_cta)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            f, err = clean_fields(None, None, None, None, self.f_icon.value, None, None, None, self.f_label.value, self.f_cta.value)
            if err: return await say(i, "⚠️ " + err)
            async with lock:
                d = db(); b = by_id(d["banners"], self.bid)
                if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้")
                b.update(f); save_json(DATA, d); cache["bn"] = None
            await i.response.send_message(f"✅ อัปเดตแล้ว: **{b_label(b)}**", ephemeral=True)

    async def toggle_banner(bid):
        async with lock:
            d = db(); b = by_id(d["banners"], bid)
            if not b: return None
            b["off"] = not b.get("off"); save_json(DATA, d); cache["bn"] = None
            return dict(b)

    def toggle_text(b): return f"{'🙈 ซ่อน' if b.get('off') else '👁️ แสดง'}แบนเนอร์ **{b.get('title', '')}** บนเว็บแล้ว"

    class BannerTweakView(discord.ui.View):
        def __init__(self, bid):
            super().__init__(timeout=300); self.bid = bid
            sel = discord.ui.Select(placeholder="🎨 เลือกสีพื้นหลังแบนเนอร์", row=0, options=[discord.SelectOption(label=v, value=k) for k, v in THEMES.items()])
            async def theme_cb(i: discord.Interaction):
                if not await guard(i): return
                async with lock:
                    d = db(); b = by_id(d["banners"], bid)
                    if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้")
                    b["theme"] = sel.values[0]; save_json(DATA, d); cache["bn"] = None
                await i.response.send_message(f"✅ เปลี่ยนสีเป็น **{THEMES.get(sel.values[0], '')}** แล้ว", ephemeral=True)
            sel.callback = theme_cb; self.add_item(sel)

            async def img(path):
                async with lock:
                    d = db(); b = by_id(d["banners"], bid)
                    if not b: return "⚠️ ไม่พบแบนเนอร์นี้แล้ว"
                    if b.get("image") != path: drop_upload(b.get("image"))
                    b["image"] = path; save_json(DATA, d); cache["bn"] = None
                return "✅ ตั้งรูปแบนเนอร์แล้ว (แนะนำ 16:9 · มือถือเห็นเต็มภาพ)" if path else "✅ ล้างรูปแบนเนอร์แล้ว"
            add_image_buttons(self, img, row=1)
            ib = discord.ui.Button(label="ไอคอน / ป้าย / ปุ่ม", emoji="😀", style=discord.ButtonStyle.secondary, row=1)
            async def icon_cb(i: discord.Interaction):
                if not await guard(i): return
                b = by_id(db()["banners"], bid)
                if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้")
                await i.response.send_modal(IconModal(bid, b))
            ib.callback = icon_cb; self.add_item(ib)
            tg = discord.ui.Button(label="แสดง / ซ่อนบนเว็บ", emoji="👁️", style=discord.ButtonStyle.secondary, row=2)
            async def tg_cb(i: discord.Interaction):
                if not await guard(i): return
                b = await toggle_banner(bid)
                if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้")
                await i.response.send_message("✅ " + toggle_text(b), ephemeral=True)
            tg.callback = tg_cb; self.add_item(tg)

    async def banner_edit(i, bid):
        b = by_id(db()["banners"], bid)
        if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้")
        await i.response.send_modal(BannerModal(bid, b))

    async def banner_move(i, bid): await i.response.send_modal(MoveModal("banners", bid))

    async def banner_remove(i, bid):
        b = by_id(db()["banners"], bid)
        if not b: return await say(i, "⚠️ ไม่พบแบนเนอร์นี้")
        async def yes(i2):
            async with lock:
                d = db(); q = by_id(d["banners"], bid)
                if not q: return await i2.response.edit_message(content="⚠️ ไม่พบแบนเนอร์นี้แล้ว", view=None)
                d["banners"].remove(q); save_json(DATA, d); cache["bn"] = None; drop_upload(q.get("image"))
            await i2.response.edit_message(content=f"🗑️ ลบแบนเนอร์ **{q.get('title', '')}** แล้ว", view=None)
        await i.response.edit_message(content=f"ลบแบนเนอร์ **{b_label(b)}** ใช่ไหม?", view=ConfirmView(yes))

    async def banner_clear(i):
        async def yes(i2):
            async with lock:
                d = db(); n = len(d["banners"])
                for b in d["banners"]: drop_upload(b.get("image"))
                d["banners"] = []; save_json(DATA, d); cache["bn"] = None
            await i2.response.edit_message(content=f"🧹 ล้างแบนเนอร์ {n} อันแล้ว — เว็บจะใช้กิจกรรมจากตารางกิจกรรมแทน", view=None)
        await i.response.send_message("ล้างแบนเนอร์ที่ตั้งเองทั้งหมดใช่ไหม? (เว็บจะกลับไปใช้กิจกรรมจากตารางอัตโนมัติ)", view=ConfirmView(yes), ephemeral=True)

    # ---------- ⚙️ ตั้งค่าหน้าเข้าร่วม ----------
    class SiteModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="ตั้งค่าหน้าเข้าร่วมบนเว็บ"); s = db()["site"]
            self.f_inv = ti("ลิงก์เชิญดิสคอร์ด", s.get("invite"), max_length=100, required=False, placeholder="https://discord.gg/xxxx (เว้นว่าง = ล้าง)")
            self.f_ban = ti("รูป/GIF แบนเนอร์หน้าแรก (https://)", s.get("banner"), max_length=400, required=False, placeholder="เว้นว่าง = ใช้ค่าในไฟล์เว็บ · อัปโหลดจากเครื่องได้หลังกดส่ง")
            self.f_title = ti("หัวข้อใหญ่ในการ์ดเข้าร่วม", s.get("title"), max_length=48, required=False, placeholder="เว้นว่าง = ค่าเริ่มต้น")
            self.f_desc = ti("คำอธิบายใต้หัวข้อ", s.get("desc"), max_length=200, required=False, style=discord.TextStyle.paragraph, placeholder="เว้นว่าง = ค่าเริ่มต้น")
            for x in (self.f_inv, self.f_ban, self.f_title, self.f_desc): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            async with lock:
                d = db(); s = d["site"]; ch = []
                v = self.f_inv.value.strip()
                if v != (s.get("invite") or ""):
                    if v in ("", "-"): s.pop("invite", None); ch.append("ลิงก์เชิญ: ล้างแล้ว")
                    elif INVITE_RE.fullmatch(v): s["invite"] = v; ch.append("ลิงก์เชิญ: อัปเดตแล้ว")
                    else: return await say(i, "⚠️ ลิงก์เชิญต้องเป็น `https://discord.gg/โค้ด`")
                v = self.f_ban.value.strip()
                if v != (s.get("banner") or ""):
                    if v in ("", "-"): drop_upload(s.get("banner")); s.pop("banner", None); ch.append("แบนเนอร์: ล้างแล้ว")
                    elif clean_url(v): s["banner"] = clean_url(v); ch.append("แบนเนอร์: อัปเดตแล้ว")
                    else: return await say(i, "⚠️ ลิงก์แบนเนอร์ต้องขึ้นต้นด้วย `https://`")
                for key, fld, lim, lab in (("title", self.f_title, 48, "หัวข้อ"), ("desc", self.f_desc, 200, "คำอธิบาย")):
                    v = " ".join(fld.value.split())[:lim]
                    if v != (s.get(key) or ""):
                        if v in ("", "-"): s.pop(key, None); ch.append(f"{lab}: กลับเป็นค่าเริ่มต้น")
                        else: s[key] = v; ch.append(f"{lab}: อัปเดตแล้ว")
                if ch: save_json(DATA, d); cache["site"] = None

            async def apply(path):
                async with lock:
                    d2 = db(); s2 = d2["site"]
                    if s2.get("banner") != path: drop_upload(s2.get("banner"))
                    if path: s2["banner"] = path
                    else: s2.pop("banner", None)
                    save_json(DATA, d2); cache["site"] = None
                return "✅ ตั้งรูปแบนเนอร์แล้ว" if path else "✅ ล้างรูปแบนเนอร์แล้ว"
            v2 = discord.ui.View(timeout=300); add_image_buttons(v2, apply)
            await i.response.send_message(("✅ " + " · ".join(ch) if ch else "ℹ️ ไม่มีอะไรเปลี่ยน") + "\n-# เว็บอัปเดตภายใน ~10 วินาที · อยากเปลี่ยนรูปแบนเนอร์จากเครื่อง กดปุ่มด้านล่าง", view=v2, ephemeral=True)

    class IntroModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="ตั้งค่าหน้าโหลดเว็บ (สไลด์แบนเนอร์)"); s = db()["site"]
            self.f_on = ti("เปิดหน้าโหลด? พิมพ์ 1 = เปิด · 0 = ปิด", s.get("intro_on") or "1", max_length=1, required=True)
            self.f_sec = ti("เวลาโหลดรวม วินาที (5-30 · แนะนำ 10)", s.get("intro_sec") or "10", max_length=2, required=True)
            self.f_txt = ti("ข้อความใต้แถบโหลด (ว่าง = ค่าเริ่มต้น)", s.get("intro_text"), max_length=80, required=False)
            for x in (self.f_on, self.f_sec, self.f_txt): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            on = self.f_on.value.strip()
            if on not in ("0", "1"): return await say(i, "⚠️ ช่องเปิด/ปิด ใส่ได้เฉพาะ `1` หรือ `0`")
            try: sec = int(self.f_sec.value.strip())
            except ValueError: return await say(i, "⚠️ วินาทีต้องเป็นตัวเลข")
            if not 5 <= sec <= 30: return await say(i, "⚠️ เวลาโหลดรวมต้องอยู่ระหว่าง 5-30 วินาที")
            async with lock:
                d = db(); st = d["site"]
                st["intro_on"] = on; st["intro_sec"] = str(sec)
                t = " ".join(self.f_txt.value.split())[:80]
                if t: st["intro_text"] = t
                else: st.pop("intro_text", None)
                save_json(DATA, d); cache["site"] = None
            n = len([b for b in db()["banners"] if not b.get("off")]) or len([e for e in events_now() if e.get("date")][:8])
            await i.response.send_message(f"✅ หน้าโหลดเว็บ: **{'เปิด' if on == '1' else 'ปิด'}** · เวลาโหลดรวม **{sec} วินาที**"
                                          f" · แบ่งให้ {n} แบนเนอร์ (อันละอย่างน้อย ~2 วิ)\n-# แสดงครั้งเดียวต่อการเปิดเว็บหนึ่งครั้ง · ทดสอบดูได้ที่ {PUBLIC}/?intro=1", ephemeral=True)

    # ---------- 📍 ตั้งห้อง (รูปภาพ / มีเดีย / คอมเม้น / คนออก) ----------
    ROOMS = {"gallery": ("🖼️ ห้องรูปภาพ (แกลเลอรี)", discord.ChannelType.text, "XMAS_GALLERY_CHANNEL"),
             "media": ("🎬 ห้องมีเดีย", discord.ChannelType.text, "XMAS_MEDIA_CHANNEL"),
             "leave": ("🚪 ห้อง ‘ทำไมถึงออก’", discord.ChannelType.text, "XMAS_LEAVE_CHANNEL"),
             "cforum": ("💬 ห้องคอมเม้น (ฟอรั่ม)", discord.ChannelType.forum, "XMAS_COMMENT_FORUM"),
             "signup": ("📝 ห้องสมัครกิจกรรม", discord.ChannelType.text, "XMAS_SIGNUP_CHANNEL")}
    ROOM_NEED = {"gallery": [("view_channel", "ดูช่อง"), ("read_message_history", "อ่านประวัติข้อความ")],
                 "media": [("view_channel", "ดูช่อง"), ("send_messages", "ส่งข้อความ"), ("attach_files", "แนบไฟล์")],
                 "leave": [("view_channel", "ดูช่อง"), ("send_messages", "ส่งข้อความ"), ("embed_links", "ฝังลิงก์")],
                 "cforum": [("view_channel", "ดูช่อง"), ("create_public_threads", "สร้างโพสต์"), ("send_messages_in_threads", "ส่งข้อความในโพสต์"), ("embed_links", "ฝังลิงก์")],
                 "signup": [("view_channel", "ดูช่อง"), ("send_messages", "ส่งข้อความ"), ("embed_links", "ฝังลิงก์"), ("attach_files", "แนบไฟล์")]}

    def room_now(kind):
        cid = db()["site"].get(kind) or os.getenv(ROOMS[kind][2], "")
        return f"<#{cid}>" if cid else "*ยังไม่ได้ตั้ง*"

    async def room_apply(i, kind, ch_id=None, clear=False):
        warn = ""
        async with lock:
            d = db(); s = d["site"]
            if clear:
                s.pop(kind, None); save_json(DATA, d)
                if kind == "gallery": gal_reset()
                return f"🧹 ยกเลิก{ROOMS[kind][0]}แล้ว"
            ch = i.guild.get_channel(ch_id) if ch_id else None
            if not ch: return "⚠️ ไม่พบห้องนี้ (บอทมองไม่เห็นห้อง)"
            pm = ch.permissions_for(i.guild.me)
            missing = [t for a, t in ROOM_NEED[kind] if not getattr(pm, a, True)]
            if missing: warn = "\n⚠️ บอทยังขาดสิทธิ์ในห้องนี้: " + " · ".join(missing)
            s[kind] = str(ch.id); save_json(DATA, d)
            if kind == "gallery": gal_reset()
        return f"✅ ตั้ง{ROOMS[kind][0]}เป็น {ch.mention} แล้ว" + warn + (f"\n-# หน้าแกลเลอรี: {PUBLIC}/gallery" if kind == "gallery" else "")

    async def make_forum(i):
        cur = comments_forum()
        if cur: return cur, None
        try:
            gch = gal_channel(); me = i.guild.me
            ow = {i.guild.default_role: discord.PermissionOverwrite(view_channel=True, create_public_threads=False, send_messages=False, send_messages_in_threads=False, add_reactions=True),
                  me: discord.PermissionOverwrite(view_channel=True, create_public_threads=True, send_messages=True, send_messages_in_threads=True, embed_links=True, manage_threads=True)}
            forum = await i.guild.create_forum(name="💬│ห้องคอมเม้น", category=(gch.category if gch else None), overwrites=ow,
                topic="💬 ห้องคอมเม้น — คอมเม้นจากแกลเลอรีบนเว็บบ้านโมชิจะเด้งมาที่นี่ และแจ้งเจ้าของโพสต์ให้อัตโนมัติ · ตอบคอมเม้นได้ที่เว็บ", reason="MOCHI HOUSE comments forum")
            return forum, None
        except discord.Forbidden: return None, "⚠️ สร้างห้องไม่ได้ — ให้สิทธิ์บอท **จัดการช่อง (Manage Channels)** หรือสร้างฟอรั่มเองแล้วเลือกจากรายการ"
        except Exception as e: return None, f"⚠️ สร้างห้องไม่สำเร็จ: {type(e).__name__} — ลองสร้างฟอรั่มเองแล้วเลือกจากรายการ"

    class RoomView(discord.ui.View):
        def __init__(self, kind):
            super().__init__(timeout=300)
            sel = discord.ui.ChannelSelect(placeholder="เลือกห้อง…", channel_types=[ROOMS[kind][1]], min_values=1, max_values=1, row=0)
            async def picked(i: discord.Interaction):
                if not await guard(i): return
                await i.response.edit_message(content=await room_apply(i, kind, sel.values[0].id), view=None)
            sel.callback = picked; self.add_item(sel)
            clr = discord.ui.Button(label="ยกเลิกห้องนี้", emoji="🧹", style=discord.ButtonStyle.secondary, row=1)
            async def clr_cb(i: discord.Interaction):
                if not await guard(i): return
                await i.response.edit_message(content=await room_apply(i, kind, clear=True), view=None)
            clr.callback = clr_cb; self.add_item(clr)
            if kind == "cforum":
                mk = discord.ui.Button(label="สร้างฟอรั่มให้อัตโนมัติ", emoji="✨", style=discord.ButtonStyle.success, row=1)
                async def mk_cb(i: discord.Interaction):
                    if not await guard(i): return
                    await i.response.defer(ephemeral=True)
                    forum, err = await make_forum(i)
                    if err: return await i.followup.send(err, ephemeral=True)
                    await i.followup.send(await room_apply(i, "cforum", forum.id) + "\n-# คอมเม้นใหม่จากเว็บจะเด้งเข้าห้องนี้ + แจ้งเจ้าของโพสต์", ephemeral=True)
                mk.callback = mk_cb; self.add_item(mk)

    async def room_open(i, kind):
        await i.response.send_message(f"{ROOMS[kind][0]} ตอนนี้: {room_now(kind)}\nเลือกห้องใหม่ด้านล่าง 👇", view=RoomView(kind), ephemeral=True)

    # ---------- 📣 โพสต์โปรโมทเว็บ ----------
    class PromoPostModal(discord.ui.Modal):
        def __init__(self, ch_id):
            super().__init__(title="โพสต์โปรโมทเว็บ (ว่าง = ค่าเริ่มต้น)"); self.ch_id = ch_id
            self.f_title = ti("หัวข้อโพสต์", required=False, max_length=100)
            self.f_desc = ti("คำอธิบาย", required=False, max_length=1500, style=discord.TextStyle.paragraph)
            self.f_btn = ti("ข้อความบนปุ่ม", required=False, max_length=60)
            self.f_img = ti("ลิงก์รูปแบนเนอร์ (https://)", required=False, max_length=400)
            for x in (self.f_title, self.f_desc, self.f_btn, self.f_img): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            img = self.f_img.value.strip()
            if img and not clean_url(img): return await say(i, "⚠️ ลิงก์รูปต้องขึ้นต้นด้วย `https://`")
            ch = i.guild.get_channel(self.ch_id)
            if not ch: return await say(i, "⚠️ ไม่พบห้องนี้")
            await post_promo(i, clean_url(img) or None, self.f_title.value.strip() or None, self.f_desc.value.strip() or None, self.f_btn.value.strip() or None, ch)

    class PromoChannelView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)

        @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text, discord.ChannelType.news], placeholder="เลือกห้องที่จะโพสต์โปรโมท", min_values=1, max_values=1)
        async def pick_ch(self, i: discord.Interaction, s: discord.ui.ChannelSelect): await i.response.send_modal(PromoPostModal(s.values[0].id))

    # ---------- 📊 สถิติ / 📨 ทดสอบ DM / 📋 ภาพรวม ----------
    class PeriodView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            opts = [("วันนี้", 1), ("7 วันล่าสุด", 7), ("30 วันล่าสุด", 30), ("ทั้งหมด (สูงสุด 90 วัน)", 90)]
            sel = discord.ui.Select(placeholder="เลือกช่วงเวลา", options=[discord.SelectOption(label=a, value=str(b)) for a, b in opts])
            async def cb(i: discord.Interaction):
                if not await guard(i): return
                n = int(sel.values[0]); await visits_send(i, n, dict((str(b), a) for a, b in opts)[sel.values[0]])
            sel.callback = cb; self.add_item(sel)

    async def dm_test(i, kind):
        try:
            if kind == "join": e, v = join_payload(i.user.display_name)
            else:
                async with lock:
                    d = db(); d.setdefault("leaveq", {})[str(i.user.id)] = {"name": i.user.display_name, "tag": str(i.user), "av": str(i.user.display_avatar.replace(size=64, format="png").url), "stay": "ทดสอบ", "t": int(time.time()), "done": False, "test": True}
                    save_json(DATA, d)
                e, v = leave_payload(i.user.display_name, True)
            await i.user.send(embed=e, view=v)
            warn = "" if (kind == "join" or leave_channel()) else "\n⚠️ ยังไม่ได้ตั้งห้องคำตอบ — กดปุ่ม 🚪 ห้องคนออก ที่แผงควบคุมก่อน ไม่งั้นคำตอบจะไม่เด้งเข้าห้อง"
            await i.response.send_message("📨 ส่ง DM ไปให้แล้ว เช็กกล่องข้อความได้เลย" + warn, ephemeral=True)
        except discord.Forbidden:
            await i.response.send_message("⚠️ ส่ง DM หาคุณไม่ได้ — เปิดรับข้อความส่วนตัวจากสมาชิกเซิร์ฟก่อน", ephemeral=True)

    def overview_embed():
        d = db(); s = d["site"]
        e = discord.Embed(title="📋 ค่าตั้งเว็บบ้านโมชิตอนนี้", color=0xF2509F)
        e.add_field(name="🌐 หน้าเข้าร่วม", value=f"• ลิงก์เชิญ: {s.get('invite') or '(ใช้ค่าในไฟล์เว็บ)'}\n• แบนเนอร์: {s.get('banner') or '(ใช้ค่าในไฟล์เว็บ)'}\n• หัวข้อ: {s.get('title') or '(ค่าเริ่มต้น)'}\n• คำอธิบาย: {s.get('desc') or '(ค่าเริ่มต้น)'}"[:1000], inline=False)
        e.add_field(name="📍 ห้องที่ตั้งไว้", value="\n".join(f"{v[0]}: {room_now(k)}" for k, v in ROOMS.items()), inline=False)
        e.add_field(name="🎬 หน้าโหลดเว็บ", value=f"{'ปิด' if s.get('intro_on') == '0' else 'เปิด'} · รวม {s.get('intro_sec') or 10} วินาที", inline=False)
        e.add_field(name="🤝 พาร์ทเนอร์", value=f"{len(d['partners'])} รายการ · มีคำโปรโมท {sum(1 for p in d['partners'] if p.get('promo'))}", inline=True)
        e.add_field(name="🎞️ แบนเนอร์", value=f"{len(d['banners'])} อัน" if d["banners"] else "ใช้จากตารางกิจกรรมอัตโนมัติ", inline=True)
        e.add_field(name="🔗 Redirect URI (ใส่ใน Developer Portal > OAuth2 > Redirects)", value=f"`{PUBLIC}/api/xmas/oauth/callback`" + ("" if OA_SECRET else "\n⚠️ ยังไม่ได้ตั้ง DISCORD_CLIENT_SECRET"), inline=False)
        e.add_field(name="🗓️ กิจกรรมตลอดเทศกาล", value=f"{len(d['events'])} รายการ (แก้ผ่านปุ่ม)" if d.get("events_custom") else "ใช้จากไฟล์ xmas_config.json", inline=True)
        e.add_field(name="📝 สมัครกิจกรรม", value=f"{len(d['signups'])} กิจกรรม · ผู้สมัครรวม {sum(len(v) for v in d['regs'].values())} คน", inline=True)
        e.set_footer(text=f"เว็บ: {PUBLIC}")
        return e

    # ====================================================================================
    # 🗓️ กิจกรรมตลอดเทศกาล : แก้ไขในดิสคอร์ดด้วยปุ่ม (ห้อง 🗓️│จัดการกิจกรรม)
    # ====================================================================================
    MAX_EVENTS = 40

    def e_label(e): return f"{e.get('icon', '🎄')} {e.get('title', '')} · {e.get('date', '')}"

    def events_text(rows):
        if not rows: return "ยังไม่มีกิจกรรม — กด ➕ เพิ่มกิจกรรม"
        rs = sorted(rows, key=lambda e: (e.get("date", ""), e.get("time", "")))
        return "\n".join(f"{e.get('icon', '🎄')} **{e.get('title', '')}** · `{e.get('date', '')}`" + (f" {e['time']}" if e.get("time") else "") for e in rs)[:1900]

    class EventModal(discord.ui.Modal):
        def __init__(self, eid=None, cur=None):
            cur = cur or {}
            super().__init__(title="แก้ไขกิจกรรม" if eid else "เพิ่มกิจกรรมตลอดเทศกาล"); self.eid = eid
            self.f_title = ti("ชื่อกิจกรรม", cur.get("title"), max_length=48, required=True)
            self.f_desc = ti("รายละเอียดสั้นๆ", cur.get("desc"), max_length=140, required=False, style=discord.TextStyle.paragraph)
            self.f_date = ti("วันที่ YYYY-MM-DD เช่น 2026-12-24", cur.get("date"), max_length=10, required=True)
            self.f_time = ti("เวลา HH:MM เช่น 20:00 (ไม่ใส่ก็ได้)", cur.get("time"), max_length=5, required=False)
            self.f_icon = ti("อีโมจิ เช่น 🎤", cur.get("icon"), max_length=8, required=False)
            for x in (self.f_title, self.f_desc, self.f_date, self.f_time, self.f_icon): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            f, err = clean_fields(self.f_title.value, self.f_desc.value, self.f_date.value, self.f_time.value, self.f_icon.value, None, None, None, None)
            if err: return await say(i, "⚠️ " + err)
            if not f.get("title") or not f.get("date"): return await say(i, "⚠️ ต้องใส่ชื่อกิจกรรมและวันที่")
            async with lock:
                d = db(); seed_events(d); ensure_ids(d); rows = d["events"]
                if self.eid:
                    e = by_id(rows, self.eid)
                    if not e: return await say(i, "⚠️ ไม่พบกิจกรรมนี้ (อาจถูกลบไปแล้ว)")
                    e.update(f)
                else:
                    if len(rows) >= MAX_EVENTS: return await say(i, f"⚠️ มีกิจกรรมครบ {MAX_EVENTS} รายการแล้ว ลบอันเก่าก่อน")
                    e = {"id": secrets.token_urlsafe(4), "date": "", "time": "", "icon": "🎄", "title": "", "desc": ""}
                    e.update(f); rows.append(e)
                save_json(DATA, d); events_dirty()
            await i.response.send_message(f"✅ {'แก้ไข' if self.eid else 'เพิ่ม'}กิจกรรมแล้ว: **{e_label(e)}**\nขึ้นบนหน้าเว็บ (ไทม์ไลน์ + ปฏิทิน) ภายในไม่กี่วินาที", ephemeral=True)

    async def event_edit(i, eid):
        e = by_id(db()["events"], eid)
        if not e: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        await i.response.send_modal(EventModal(eid, e))

    async def event_remove(i, eid):
        e = by_id(db()["events"], eid)
        if not e: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        async def yes(i2):
            async with lock:
                d = db(); q = by_id(d["events"], eid)
                if not q: return await i2.response.edit_message(content="⚠️ ไม่พบกิจกรรมนี้แล้ว", view=None)
                d["events"].remove(q); save_json(DATA, d); events_dirty()
            await i2.response.edit_message(content=f"🗑️ ลบกิจกรรม **{q.get('title', '')}** แล้ว", view=None)
        await i.response.edit_message(content=f"ลบกิจกรรม **{e_label(e)}** ใช่ไหม?", view=ConfirmView(yes))

    async def events_reset(i):
        async def yes(i2):
            async with lock:
                d = db(); d["events"] = []; d["events_custom"] = False; save_json(DATA, d); events_dirty()
            await i2.response.edit_message(content="🔄 กลับไปใช้ตารางกิจกรรมจากไฟล์ `xmas_config.json` แล้ว", view=None)
        await i.response.send_message("ทิ้งรายการที่แก้ไว้ทั้งหมด แล้วกลับไปใช้ตารางจากไฟล์ `xmas_config.json` ใช่ไหม?", view=ConfirmView(yes), ephemeral=True)

    class AdminEventView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)

        @discord.ui.button(label="เพิ่มกิจกรรม", emoji="➕", style=discord.ButtonStyle.success, custom_id="xmasa:e_add", row=0)
        async def e_add(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_modal(EventModal())

        @discord.ui.button(label="แก้ไข", emoji="✏️", style=discord.ButtonStyle.secondary, custom_id="xmasa:e_edit", row=0)
        async def e_edit(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "events", e_label, event_edit, "เลือกกิจกรรมที่จะแก้ไข", "ยังไม่มีกิจกรรม — กด ➕ เพิ่มก่อน")

        @discord.ui.button(label="ลบ", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="xmasa:e_del", row=0)
        async def e_del(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "events", e_label, event_remove, "เลือกกิจกรรมที่จะลบ", "ยังไม่มีกิจกรรม")

        @discord.ui.button(label="รายการทั้งหมด", emoji="📋", style=discord.ButtonStyle.secondary, custom_id="xmasa:e_list", row=1)
        async def e_list(self, i: discord.Interaction, b: discord.ui.Button):
            if not await guard(i): return
            rows = await load_rows("events")
            await i.response.send_message("🗓️ **กิจกรรมตลอดเทศกาล** (เรียงตามวันที่)\n" + events_text(rows), ephemeral=True)

        @discord.ui.button(label="รีเซ็ตกลับค่าจากไฟล์", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="xmasa:e_reset", row=1)
        async def e_reset(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await events_reset(i)

    # ====================================================================================
    # 📝 สมัครกิจกรรม : ตั้งค่าได้ทุกอย่างจากดิสคอร์ด · สมัครบนเว็บ → เด้งเข้า "ห้องสมัครกิจกรรม"
    # ====================================================================================
    MAX_SIGNUPS = 30
    SG_NAME = {"open": "🟢 เปิดรับ", "soon": "🕒 เร็วๆ นี้", "full": "🔴 เต็มแล้ว", "ended": "⏰ หมดเวลา", "closed": "🔒 ปิดรับ"}
    SG_ERR = {"soon": "ยังไม่เปิดรับสมัคร", "full": "กิจกรรมนี้เต็มแล้ว", "ended": "หมดเวลารับสมัครแล้ว", "closed": "ปิดรับสมัครแล้ว"}
    THEME_COL = {"pink": 0xF2509F, "purple": 0x8B5CF6, "gold": 0xF0A43A, "blue": 0x3A7BEA, "green": 0x22B58A, "red": 0xE83F5C}
    MTH_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    SG_PUB = ("id", "icon", "title", "desc", "details", "date", "time", "prize", "place", "open", "close", "close_time", "limit", "question", "btn", "label", "theme", "image", "tmin", "tmax", "uid_label", "ask_theme", "ask_banner", "ask_logo")

    def th_date(ds, tm=""):
        try:
            y, m, d = map(int, ds.split("-"))
            return f"{d} {MTH_TH[m - 1]} {y}" + (f" · {tm} น." if tm else "")
        except Exception: return ""

    def parse_dt(s):
        """'YYYY-MM-DD' หรือ 'YYYY-MM-DD HH:MM' → (date, time, error) · ว่าง/'-' = ('', '', None)"""
        s = " ".join((s or "").split())
        if s in ("", "-"): return "", "", None
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?: ([01]\d|2[0-3]):([0-5]\d))?", s)
        if not m: return None, None, "รูปแบบต้องเป็น `YYYY-MM-DD` หรือ `YYYY-MM-DD HH:MM` เช่น `2026-12-20 21:00`"
        try: datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError: return None, None, "วันที่ไม่ถูกต้อง (เช่น เดือน/วันเกินจริง)"
        return m.group(1), (f"{m.group(2)}:{m.group(3)}" if m.group(2) else ""), None

    def sg_state(a, n):
        """open / soon / full / ended / closed"""
        t = now_th(); today, hm = t.strftime("%Y-%m-%d"), t.strftime("%H:%M")
        if a.get("closed"): return "closed"
        if a.get("open") and today < a["open"]: return "soon"
        if a.get("close") and (today, hm) > (a["close"], a.get("close_time") or "23:59"): return "ended"
        if a.get("limit") and n >= a["limit"]: return "full"
        return "open"

    def s_label(a): return f"{a.get('icon', '🎁')} {a.get('title', '')}" + (" 🔒" if a.get("closed") else "") + (" 🙈" if a.get("off") else "")

    def signup_list_text(rows, regs=None):
        regs = db()["regs"] if regs is None else regs
        if not rows: return "ยังไม่มีกิจกรรมให้สมัคร — กด ➕ สร้างกิจกรรมสมัคร"
        L = []
        for n, a in enumerate(rows, 1):
            c = len(regs.get(a["id"], {}))
            L.append(f"**{n}.** {a.get('icon', '🎁')} {a['title']} · {c}" + (f"/{a['limit']}" if a.get("limit") else "") + f" คน · {SG_NAME.get(sg_state(a, c), '')}" + (" · 🙈ซ่อน" if a.get("off") else ""))
        return "\n".join(L)[:1900]

    def signup_room():
        cid = db()["site"].get("signup") or os.getenv("XMAS_SIGNUP_CHANNEL", "")
        try: return bot.get_channel(int(cid)) if cid else None
        except Exception: return None

    # ---------- ข้อความ "สมัครแล้ว" เด้งเข้าห้องสมัครกิจกรรม ----------
    async def post_reg_notice(m, icon, title, theme, n, limit=0, ans="", q="", when="", team=None):
        ch = signup_room()
        if not ch: return 0
        try:
            emb = discord.Embed(color=THEME_COL.get(theme, 0xF2509F), timestamp=datetime.now(timezone.utc),
                                description=f"✅ {m.mention} สมัครกิจกรรม **{icon} {discord.utils.escape_markdown(str(title))}** แล้ว")
            emb.set_author(name=f"{m.display_name} สมัครแล้ว!", icon_url=avatar(m))
            logo = (team or {}).get("logo")
            emb.set_thumbnail(url=(PUBLIC + logo) if logo else str(m.display_avatar.replace(size=128, format="png").url))
            emb.add_field(name="ผู้สมัครคนที่", value=f"**#{n}**" + (f" / {limit}" if limit else ""), inline=True)
            if when: emb.add_field(name="วันจัดกิจกรรม", value=when, inline=True)
            if team and team.get("theme"): emb.add_field(name="🎨 ชื่อธีม", value=esc(team["theme"], 60), inline=False)
            if team and team.get("members"):
                emb.add_field(name=f"👥 ทีม ({len(team['members'])} คน)", value=esc(" · ".join(x["name"] for x in team["members"]), 300), inline=False)
            if ans: emb.add_field(name=(q or "คำตอบ")[:240], value=esc(ans, 300), inline=False)
            if team and team.get("banner"): emb.set_image(url=PUBLIC + team["banner"])
            emb.set_footer(text="MOCHI HOUSE · สมัครผ่านเว็บ")
            v = discord.ui.View(); v.add_item(discord.ui.Button(label="ดูกิจกรรมทั้งหมด", emoji="📝", style=discord.ButtonStyle.link, url=PUBLIC + "/#signup"))
            msg = await ch.send(embed=emb, view=v, allowed_mentions=discord.AllowedMentions.none())
            return msg.id
        except Exception as e:
            print(f"   ✖ ส่งข้อความสมัครกิจกรรมเข้าห้องไม่สำเร็จ: {type(e).__name__}: {e}"); return 0

    async def role_apply(m, a, add=True):
        """ให้/ถอนยศตามที่ตั้งไว้กับกิจกรรม (พลาดก็ไม่เป็นไร ไม่ให้กระทบการสมัคร)"""
        try:
            gd = guild(); role = gd.get_role(int(a.get("role") or 0)) if gd else None
            if not (m and role): return
            if add and role not in m.roles: await m.add_roles(role, reason=f"สมัครกิจกรรม {a.get('title', '')}")
            elif not add and role in m.roles: await m.remove_roles(role, reason=f"ยกเลิกสมัครกิจกรรม {a.get('title', '')}")
        except Exception as e: print(f"   ✖ ให้/ถอนยศไม่สำเร็จ: {type(e).__name__}: {e}")

    async def drop_reg(aid, uid, by=None):
        """ลบผู้สมัคร + แก้ข้อความในห้องเป็น 'ยกเลิก' + ถอนยศ → (activity, reg) · ไม่พบ = (None, None)"""
        async with lock:
            d = db(); a = by_id(d["signups"], aid); r = d["regs"].get(aid, {}).pop(uid, None)
            if not r: return None, None
            save_json(DATA, d)
        for k in ("banner", "logo"): drop_upload((r.get("team") or {}).get(k))
        a = a or {"title": "กิจกรรม", "icon": "🎁"}
        ch = signup_room()
        if ch and r.get("mid"):
            try:
                msg = await ch.fetch_message(int(r["mid"]))
                await msg.edit(embed=discord.Embed(color=0x6B7280, description=f"❌ <@{uid}> {'ถูกแอดมินนำออกจาก' if by else 'ยกเลิกการสมัคร'} **{a.get('icon', '🎁')} {discord.utils.escape_markdown(str(a.get('title', '')))}** แล้ว"), view=None)
            except Exception: pass
        try:
            gd = guild(); m = gd.get_member(int(uid)) if gd else None
            await role_apply(m, a, add=False)
        except Exception: pass
        return a, r

    # ---------- API เว็บ ----------
    SG_UP_MAX = 3 * 1024 * 1024
    sg_owned = {}   # path รูปที่เพิ่งอัปโหลด → (uid, เวลา) ใช้ยืนยันว่าเป็นของคนที่สมัครจริง

    def sg_form(a):
        """ค่าฟอร์มสมัครที่ใช้จริง — กิจกรรมเก่าที่ยังไม่เคยตั้งฟอร์ม ใช้ค่าเริ่มต้นแบบทีม (ชื่อธีม + สมาชิก 1-4 คน + แบนเนอร์/โลโก้)"""
        if "tmax" not in a and "ask_theme" not in a:
            return {"tmin": 1, "tmax": 4, "uid_label": "UID ในเกม", "ask_theme": True, "ask_banner": True, "ask_logo": True}
        try: tmax = max(0, int(a.get("tmax") or 0)); tmin = max(1, int(a.get("tmin") or 1))
        except (TypeError, ValueError): tmax, tmin = 0, 1
        return {"tmin": tmin, "tmax": tmax, "uid_label": a.get("uid_label") or "UID ในเกม", "ask_theme": bool(a.get("ask_theme")), "ask_banner": bool(a.get("ask_banner")), "ask_logo": bool(a.get("ask_logo"))}

    def team_public(t):
        t = t or {}
        return {"theme": t.get("theme", ""), "members": t.get("members", []), "banner": t.get("banner", ""), "logo": t.get("logo", "")}

    async def signups(req):
        s = sess(req); uid = str(s["uid"]) if s else ""
        d, gd, out = db(), guild(), []
        for a in d["signups"]:
            if a.get("off"): continue
            regs = d["regs"].get(a["id"], {}); n = len(regs)
            av = []
            for u, r in sorted(regs.items(), key=lambda kv: kv[1].get("at", 0), reverse=True)[:5]:
                m = gd.get_member(int(u)) if gd else None
                if m: av.append(avatar(m))
            mine = regs.get(uid) if uid else None
            row = {k: a.get(k, "") for k in SG_PUB}
            row.update(sg_form(a))
            row.update({"state": sg_state(a, n), "count": n, "recent": av, "mine": bool(mine), "my_answer": (mine or {}).get("ans", ""), "my_at": (mine or {}).get("at", 0)})
            if mine: row["my"] = {"no": mine.get("no", 0), "at": mine.get("at", 0), "ans": mine.get("ans", ""), "team": team_public(mine.get("team"))}
            out.append(row)
        return js({"ok": True, "items": out, "room": bool(signup_room()), "now": now_th().strftime("%Y-%m-%d %H:%M")})

    async def signup_upload(req):
        """อัปโหลดรูปแบนเนอร์/โลโก้ธีมของผู้สมัคร (ต้องล็อกอิน · ตรวจชนิดไฟล์จากเนื้อไฟล์จริง · ไม่เกิน 3 MB)"""
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อน"}, 401)
        if limited(req, "sgu", 10, 300): return js({"ok": False, "error": "อัปโหลดบ่อยเกินไป รอสักครู่นะ"}, 429)
        try: n = int(req.headers.get("Content-Length") or 0)
        except ValueError: n = 0
        if n > SG_UP_MAX: return js({"ok": False, "error": "รูปใหญ่เกินไป (ไม่เกิน 3 MB)"}, 413)
        buf = bytearray()
        async for c in req.content.iter_chunked(65536):
            buf += c
            if len(buf) > SG_UP_MAX: return js({"ok": False, "error": "รูปใหญ่เกินไป (ไม่เกิน 3 MB)"}, 413)
        kind, ext = sniff(bytes(buf[:32]))
        if kind != "i" or ext not in ("png", "jpg", "gif", "webp"): return js({"ok": False, "error": "รองรับเฉพาะรูป png / jpg / gif / webp"}, 400)
        try:
            os.makedirs(UPL, exist_ok=True)
            name = secrets.token_urlsafe(9) + "." + ext
            with open(os.path.join(UPL, name), "wb") as fh: fh.write(bytes(buf))
        except Exception as e:
            print(f"   ✖ บันทึกรูปผู้สมัครไม่สำเร็จ: {type(e).__name__}: {e}")
            return js({"ok": False, "error": "บันทึกรูปไม่สำเร็จ ลองใหม่อีกครั้ง"}, 500)
        now = time.time()
        for k in [k for k, v in sg_owned.items() if now - v[1] > 10800]:
            sg_owned.pop(k, None)
        sg_owned["/u/" + name] = (str(s["uid"]), now)
        return js({"ok": True, "path": "/u/" + name})

    def sg_clean_team(a, b, uid):
        """ตรวจฟอร์มทีม/ธีม/รูป → (team dict, error)"""
        team = {}; fm = sg_form(a); a = {**a, **fm}; lab = fm["uid_label"]
        mx = fm["tmax"]
        if mx > 0:
            raw = b.get("members"); raw = raw if isinstance(raw, list) else []
            mem = []
            for x in raw[:mx]:
                if not isinstance(x, dict): continue
                nm = " ".join(str(x.get("name") or "").split())[:40]; ud = re.sub(r"\s+", "", str(x.get("uid") or ""))[:32]
                if nm or ud: mem.append({"name": nm, "uid": ud})
            need = max(1, int(a.get("tmin") or 1))
            if len(mem) < need or any(not x["name"] or not x["uid"] for x in mem): return None, f"กรอกชื่อและ {lab} ของสมาชิกให้ครบ (อย่างน้อย {need} คน)"
            if len({x["uid"].lower() for x in mem}) < len(mem): return None, f"{lab} ซ้ำกันในทีม ตรวจอีกครั้งนะ"
            team["members"] = mem
        if a.get("ask_theme"):
            th = " ".join(str(b.get("theme") or "").split())[:48]
            if not th: return None, "กรอกชื่อธีมก่อนนะ"
            team["theme"] = th
        for k, flag in (("banner", "ask_banner"), ("logo", "ask_logo")):
            p = str(b.get(k) or "")
            if p and a.get(flag):
                own = sg_owned.get(p)
                if not (UP_RE.fullmatch(p) and own and own[0] == uid and os.path.isfile(os.path.join(UPL, p[3:]))):
                    return None, "รูปที่อัปโหลดไม่ถูกต้องหรือหมดอายุ อัปโหลดใหม่อีกครั้งนะ"
                team[k] = p
        return team, None

    async def signup_join(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบก่อนสมัคร"}, 401)
        if limited(req, "sgj", 14, 300): return js({"ok": False, "error": "กดบ่อยเกินไป รอสักครู่นะ"}, 429)
        try: b = await req.json()
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        if not isinstance(b, dict): return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        aid = str(b.get("id") or "")[:16]; ans = " ".join(str(b.get("answer") or "").split())[:300]
        gd = guild(); m = gd.get_member(int(s["uid"])) if gd else None
        if not m: return js({"ok": False, "error": "ไม่พบบัญชีของคุณในเซิร์ฟเวอร์ — เข้าร่วมดิสคอร์ดก่อนนะ"}, 403)
        uid = str(s["uid"])
        async with lock:
            d = db(); a = by_id(d["signups"], aid)
            if not a or a.get("off"): return js({"ok": False, "error": "ไม่พบกิจกรรมนี้"}, 404)
            regs = d["regs"].setdefault(aid, {})
            if uid in regs: return js({"ok": False, "error": "คุณสมัครกิจกรรมนี้แล้ว"}, 409)
            st = sg_state(a, len(regs))
            if st != "open": return js({"ok": False, "error": SG_ERR.get(st, "สมัครไม่ได้ตอนนี้")}, 409)
            if a.get("question") and not ans: return js({"ok": False, "error": "ตอบคำถามก่อนสมัครนะ"}, 400)
            team, err = sg_clean_team(a, b, uid)
            if err: return js({"ok": False, "error": err}, 400)
            used = {x["uid"].lower() for r in regs.values() for x in (r.get("team") or {}).get("members", [])}
            dup = next((x["uid"] for x in (team or {}).get("members", []) if x["uid"].lower() in used), None)
            if dup: return js({"ok": False, "error": f"{a.get('uid_label') or 'UID'} {dup} ถูกใช้สมัครกิจกรรมนี้แล้ว"}, 409)
            n = len(regs) + 1
            regs[uid] = {"at": int(time.time()), "ans": ans, "name": m.display_name, "mid": 0, "no": n, "team": team}
            save_json(DATA, d); a = dict(a)
        for k in ("banner", "logo"): sg_owned.pop((team or {}).get(k, ""), None)
        mid = await post_reg_notice(m, a.get("icon", "🎁"), a.get("title", ""), a.get("theme"), n, a.get("limit", 0), ans, a.get("question", ""), th_date(a.get("date", ""), a.get("time", "")), team)
        if mid:
            async with lock:
                d = db(); r = d["regs"].get(aid, {}).get(uid)
                if r: r["mid"] = mid; save_json(DATA, d)
        await role_apply(m, a, add=True)
        return js({"ok": True, "count": n, "limit": a.get("limit", 0), "posted": bool(mid), "no": n})

    async def signup_cancel(req):
        s = sess(req)
        if not s: return js({"ok": False, "error": "กรุณาเข้าสู่ระบบ"}, 401)
        if limited(req, "sgc", 14, 300): return js({"ok": False, "error": "กดบ่อยเกินไป รอสักครู่นะ"}, 429)
        try: aid = str((await req.json()).get("id") or "")[:16]
        except Exception: return js({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}, 400)
        a, r = await drop_reg(aid, str(s["uid"]))
        if not r: return js({"ok": False, "error": "ไม่พบการสมัครของคุณในกิจกรรมนี้"}, 404)
        return js({"ok": True, "count": len(db()["regs"].get(aid, {}))})

    # ---------- ฟอร์มตั้งค่า (3 หน้าต่าง) ----------
    class SignupModal(discord.ui.Modal):
        def __init__(self, aid=None, cur=None):
            cur = cur or {}
            super().__init__(title="แก้ไขข้อมูลกิจกรรมสมัคร" if aid else "สร้างกิจกรรมให้สมัคร"); self.aid = aid
            when = (cur.get("date", "") + (" " + cur["time"] if cur.get("time") else "")).strip()
            self.f_title = ti("ชื่อกิจกรรม", cur.get("title"), max_length=48, required=True)
            self.f_desc = ti("คำอธิบายสั้นๆ (ขึ้นบนการ์ด)", cur.get("desc"), max_length=140, required=False)
            self.f_det = ti("รายละเอียด / กติกา (ขึ้นในหน้าต่างสมัคร)", cur.get("details"), max_length=1200, required=False, style=discord.TextStyle.paragraph,
                            placeholder="ขึ้นบรรทัดใหม่ได้ · วางลิงก์ https:// ได้")
            self.f_when = ti("วัน-เวลาจัดกิจกรรม YYYY-MM-DD HH:MM", when, max_length=16, required=False, placeholder="เช่น 2026-12-20 21:00 (เวลาไม่ใส่ก็ได้)")
            self.f_prize = ti("รางวัล / สิ่งที่ผู้เข้าร่วมจะได้", cur.get("prize"), max_length=100, required=False)
            for x in (self.f_title, self.f_desc, self.f_det, self.f_when, self.f_prize): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            title = " ".join(self.f_title.value.split())[:48]
            if not title: return await say(i, "⚠️ ต้องใส่ชื่อกิจกรรม")
            dt, tm, err = parse_dt(self.f_when.value)
            if err: return await say(i, "⚠️ วัน-เวลาจัดกิจกรรม: " + err)
            f = {"title": title, "desc": " ".join(self.f_desc.value.split())[:140], "details": clean_promo(self.f_det.value)[:1200],
                 "date": dt, "time": tm, "prize": " ".join(self.f_prize.value.split())[:100]}
            async with lock:
                d = db(); ensure_ids(d); rows = d["signups"]
                if self.aid:
                    a = by_id(rows, self.aid)
                    if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้ (อาจถูกลบไปแล้ว)")
                    a.update(f)
                else:
                    if len(rows) >= MAX_SIGNUPS: return await say(i, f"⚠️ มีกิจกรรมสมัครครบ {MAX_SIGNUPS} อันแล้ว ลบอันเก่าก่อน")
                    a = {"id": secrets.token_urlsafe(4), "icon": "🎁", "title": "", "desc": "", "details": "", "date": "", "time": "", "prize": "", "place": "",
                         "open": "", "close": "", "close_time": "", "limit": 0, "question": "", "btn": "", "label": "", "theme": "pink", "image": "", "role": "", "off": False, "closed": False,
                         "tmin": 1, "tmax": 5, "uid_label": "UID ในเกม", "ask_theme": True, "ask_banner": True, "ask_logo": True}
                    a.update(f); rows.append(a)
                save_json(DATA, d); aid = a["id"]
            await i.response.send_message(f"✅ {'แก้ไข' if self.aid else 'สร้าง'}กิจกรรมสมัครแล้ว: **{s_label(a)}**\nขึ้นที่หมวด “สมัครกิจกรรม” บนเว็บภายในไม่กี่วินาที"
                                          f"\n-# ตั้งค่าต่อได้ด้านล่าง: เวลารับสมัคร/จำนวนคน/คำถาม · สี · แบนเนอร์ (แนะนำ 16:9) · ยศอัตโนมัติ", view=SignupTweakView(aid), ephemeral=True)

    class SignupRuleModal(discord.ui.Modal):
        def __init__(self, aid, cur):
            super().__init__(title="ตั้งค่าการรับสมัคร"); self.aid = aid
            close = (cur.get("close", "") + (" " + cur["close_time"] if cur.get("close_time") else "")).strip()
            self.f_open = ti("เปิดรับสมัครวันที่ YYYY-MM-DD (ว่าง=เปิดทันที)", cur.get("open"), max_length=10, required=False)
            self.f_close = ti("ปิดรับสมัคร YYYY-MM-DD HH:MM (ว่าง=ไม่ปิด)", close, max_length=16, required=False, placeholder="เช่น 2026-12-15 21:00 · ไม่ใส่เวลา = ถึงสิ้นวัน")
            self.f_limit = ti("จำนวนที่รับ (ว่าง หรือ 0 = ไม่จำกัด)", str(cur.get("limit") or ""), max_length=4, required=False)
            self.f_q = ti("คำถามให้ผู้สมัครตอบ (ว่าง = ไม่ถาม)", cur.get("question"), max_length=100, required=False, placeholder="เช่น ชื่อในเกม / ช่องทางติดต่อ")
            self.f_btn = ti("ข้อความบนปุ่มสมัคร (ว่าง = สมัครเลย)", cur.get("btn"), max_length=20, required=False)
            for x in (self.f_open, self.f_close, self.f_limit, self.f_q, self.f_btn): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            od, _, e1 = parse_dt(self.f_open.value)
            cd, ct, e2 = parse_dt(self.f_close.value)
            if e1 or e2: return await say(i, "⚠️ " + (e1 or e2))
            if od and cd and cd < od: return await say(i, "⚠️ วันปิดรับสมัครต้องไม่ก่อนวันเปิดรับสมัคร")
            lim = (self.f_limit.value or "").strip()
            try: lim = int(lim) if lim else 0
            except ValueError: return await say(i, "⚠️ จำนวนที่รับต้องเป็นตัวเลข")
            if not 0 <= lim <= 9999: return await say(i, "⚠️ จำนวนที่รับต้องอยู่ระหว่าง 0-9999")
            async with lock:
                d = db(); a = by_id(d["signups"], self.aid)
                if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                a.update({"open": od, "close": cd, "close_time": ct, "limit": lim, "question": " ".join(self.f_q.value.split())[:100], "btn": " ".join(self.f_btn.value.split())[:20]})
                save_json(DATA, d); n = len(d["regs"].get(self.aid, {})); st = sg_state(a, n)
            await i.response.send_message(f"✅ บันทึกการรับสมัคร **{s_label(a)}** แล้ว · ตอนนี้: {SG_NAME.get(st, '')} · ผู้สมัคร {n}" + (f"/{lim}" if lim else "") + " คน", ephemeral=True)

    def is_yes(v): return (v or "").strip().lower() in ("ใช่", "y", "yes", "1", "true", "on", "เปิด", "ถาม")

    class SignupFormModal(discord.ui.Modal):
        def __init__(self, aid, cur):
            super().__init__(title="ฟอร์มสมัคร (ทีม / UID / ธีม)"); self.aid = aid
            self.f_max = ti("สมาชิกทีมสูงสุด (0 = ไม่ถามสมาชิก)", str(cur.get("tmax") or 0), max_length=2, required=True)
            self.f_min = ti("สมาชิกขั้นต่ำ (ว่าง = 1)", str(cur.get("tmin") or ""), max_length=2, required=False)
            self.f_uid = ti("ชื่อช่อง UID (ว่าง = UID ในเกม)", cur.get("uid_label"), max_length=20, required=False)
            self.f_theme = ti("ถามชื่อธีม? พิมพ์ ใช่ / ไม่", "ใช่" if cur.get("ask_theme") else "ไม่", max_length=3, required=True)
            self.f_img = ti("ให้อัปโหลดแบนเนอร์/โลโก้ธีม? ใช่ / ไม่ (ไม่บังคับ)", "ใช่" if (cur.get("ask_banner") or cur.get("ask_logo")) else "ไม่", max_length=3, required=True)
            for x in (self.f_max, self.f_min, self.f_uid, self.f_theme, self.f_img): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            try:
                mx = int(self.f_max.value.strip() or 0); mn = int(self.f_min.value.strip() or 1)
            except ValueError: return await say(i, "⚠️ จำนวนสมาชิกต้องเป็นตัวเลข")
            if not 0 <= mx <= 15 or not 1 <= mn <= 15: return await say(i, "⚠️ จำนวนสมาชิกต้องอยู่ระหว่าง 0-15 (ขั้นต่ำอย่างน้อย 1)")
            if mx and mn > mx: return await say(i, "⚠️ ขั้นต่ำต้องไม่มากกว่าจำนวนสูงสุด")
            img = is_yes(self.f_img.value)
            async with lock:
                d = db(); a = by_id(d["signups"], self.aid)
                if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                a.update({"tmax": mx, "tmin": mn, "uid_label": " ".join(self.f_uid.value.split())[:20] or "UID ในเกม", "ask_theme": is_yes(self.f_theme.value), "ask_banner": img, "ask_logo": img}); save_json(DATA, d)
            await i.response.send_message(f"✅ ตั้งฟอร์มสมัคร **{s_label(a)}** แล้ว\n• สมาชิก: " + (f"{mn}-{mx} คน (ชื่อ + {a['uid_label']})" if mx else "ไม่ถาม") + f"\n• ชื่อธีม: {'ถาม (บังคับ)' if a['ask_theme'] else 'ไม่ถาม'}\n• แบนเนอร์/โลโก้ธีม: {'ให้อัปโหลดได้ (ไม่บังคับ)' if img else 'ไม่มี'}", ephemeral=True)

    async def signup_form(i, aid):
        a = by_id(db()["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        await i.response.send_modal(SignupFormModal(aid, {**a, **sg_form(a)}))

    class SignupIconModal(discord.ui.Modal):
        def __init__(self, aid, cur):
            super().__init__(title="ไอคอน / ป้ายเล็ก / สถานที่"); self.aid = aid
            self.f_icon = ti("อีโมจิ เช่น 🎤", cur.get("icon"), max_length=8, required=False)
            self.f_label = ti("ป้ายเล็กบนการ์ด เช่น HOT / ใหม่", cur.get("label"), max_length=24, required=False)
            self.f_place = ti("สถานที่ / ห้องที่จัด", cur.get("place"), max_length=60, required=False, placeholder="เช่น ห้องเสียง Party · ห้องแกลเลอรี")
            for x in (self.f_icon, self.f_label, self.f_place): self.add_item(x)

        async def on_submit(self, i: discord.Interaction):
            if not await guard(i): return
            async with lock:
                d = db(); a = by_id(d["signups"], self.aid)
                if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                a.update({"icon": self.f_icon.value.strip()[:8] or "🎁", "label": " ".join(self.f_label.value.split())[:24], "place": " ".join(self.f_place.value.split())[:60]}); save_json(DATA, d)
            await i.response.send_message(f"✅ อัปเดตแล้ว: **{s_label(a)}**", ephemeral=True)

    class SignupTweakView(discord.ui.View):
        def __init__(self, aid):
            super().__init__(timeout=300); self.aid = aid
            sel = discord.ui.Select(placeholder="🎨 เลือกสีการ์ดกิจกรรม", row=0, options=[discord.SelectOption(label=v, value=k) for k, v in THEMES.items()])
            async def theme_cb(i: discord.Interaction):
                if not await guard(i): return
                async with lock:
                    d = db(); a = by_id(d["signups"], aid)
                    if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                    a["theme"] = sel.values[0]; save_json(DATA, d)
                await i.response.send_message(f"✅ เปลี่ยนสีเป็น **{THEMES.get(sel.values[0], '')}** แล้ว", ephemeral=True)
            sel.callback = theme_cb; self.add_item(sel)

            rs = discord.ui.RoleSelect(placeholder="🏷️ ยศที่ให้อัตโนมัติเมื่อสมัคร (ไม่เลือก = ไม่ให้)", min_values=0, max_values=1, row=1)
            async def role_cb(i: discord.Interaction):
                if not await guard(i): return
                role = rs.values[0] if rs.values else None
                if role and (role.is_default() or role.managed or role >= i.guild.me.top_role):
                    return await say(i, "⚠️ บอทให้ยศนี้ไม่ได้ — ยศต้องอยู่ต่ำกว่ายศของบอท และไม่ใช่ยศบอท/@everyone")
                async with lock:
                    d = db(); a = by_id(d["signups"], aid)
                    if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                    a["role"] = str(role.id) if role else ""; save_json(DATA, d)
                await i.response.send_message(f"✅ ยศอัตโนมัติ: {role.mention if role else 'ไม่ให้ยศ'}" + ("\n-# ผู้ที่สมัครต่อจากนี้จะได้ยศทันที (ยกเลิกสมัคร = ถอนยศ)" if role else ""), ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            rs.callback = role_cb; self.add_item(rs)

            b1 = discord.ui.Button(label="เวลา / จำนวนคน / คำถาม", emoji="⚙️", style=discord.ButtonStyle.primary, row=2)
            async def b1_cb(i: discord.Interaction):
                if not await guard(i): return
                a = by_id(db()["signups"], aid)
                if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                await i.response.send_modal(SignupRuleModal(aid, a))
            b1.callback = b1_cb; self.add_item(b1)
            b3 = discord.ui.Button(label="ฟอร์มสมัคร (ทีม/UID/ธีม)", emoji="🧩", style=discord.ButtonStyle.primary, row=2)
            async def b3_cb(i: discord.Interaction):
                if not await guard(i): return
                a = by_id(db()["signups"], aid)
                if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                await i.response.send_modal(SignupFormModal(aid, {**a, **sg_form(a)}))
            b3.callback = b3_cb; self.add_item(b3)
            b2 = discord.ui.Button(label="ไอคอน / ป้าย / สถานที่", emoji="😀", style=discord.ButtonStyle.secondary, row=2)
            async def b2_cb(i: discord.Interaction):
                if not await guard(i): return
                a = by_id(db()["signups"], aid)
                if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
                await i.response.send_modal(SignupIconModal(aid, a))
            b2.callback = b2_cb; self.add_item(b2)

            async def img(path):
                async with lock:
                    d = db(); a = by_id(d["signups"], aid)
                    if not a: return "⚠️ ไม่พบกิจกรรมนี้แล้ว"
                    if a.get("image") != path: drop_upload(a.get("image"))
                    a["image"] = path; save_json(DATA, d)
                return "✅ ตั้งแบนเนอร์กิจกรรมแล้ว (แนะนำ 16:9 · มือถือเห็นเต็มภาพ)" if path else "✅ ล้างแบนเนอร์แล้ว"
            add_image_buttons(self, img, row=3, l1="อัปโหลดแบนเนอร์", l2="ลิงก์แบนเนอร์", e1="🏞️")

    async def signup_edit(i, aid):
        a = by_id(db()["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        await i.response.send_modal(SignupModal(aid, a))

    async def signup_rules(i, aid):
        a = by_id(db()["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        await i.response.send_modal(SignupRuleModal(aid, a))

    async def signup_style(i, aid):
        a = by_id(db()["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        await i.response.edit_message(content=f"🎨 **{s_label(a)}**\nตั้งสี · แบนเนอร์ · ไอคอน · ยศอัตโนมัติ · เวลา/จำนวนคน\n-# แบนเนอร์แนะนำรูปแนวนอน 16:9 (เช่น 1280×720) — มือถือจะเห็นเต็มภาพ ไม่โดนตัด", view=SignupTweakView(aid))

    async def signup_closed_toggle(i, aid):
        async with lock:
            d = db(); a = by_id(d["signups"], aid)
            if not a: return await i.response.edit_message(content="⚠️ ไม่พบกิจกรรมนี้", view=None)
            a["closed"] = not a.get("closed"); save_json(DATA, d); a = dict(a)
        await i.response.edit_message(content=f"{'🔒 ปิดรับสมัคร' if a['closed'] else '🔓 เปิดรับสมัคร'} **{s_label(a)}** แล้ว", view=None)

    async def signup_off_toggle(i, aid):
        async with lock:
            d = db(); a = by_id(d["signups"], aid)
            if not a: return await i.response.edit_message(content="⚠️ ไม่พบกิจกรรมนี้", view=None)
            a["off"] = not a.get("off"); save_json(DATA, d); a = dict(a)
        await i.response.edit_message(content=f"{'🙈 ซ่อน' if a['off'] else '👁️ แสดง'} **{a.get('icon', '🎁')} {a.get('title', '')}** บนเว็บแล้ว", view=None)

    async def signup_roster(i, aid):
        d = db(); a = by_id(d["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        regs = d["regs"].get(aid, {}); L = []
        for n, (u, r) in enumerate(sorted(regs.items(), key=lambda kv: kv[1].get("at", 0)), 1):
            L.append(f"`{n:02d}` <@{u}> · {datetime.fromtimestamp(r.get('at', 0), TH).strftime('%d/%m %H:%M')}" + (f" — {esc(r['ans'], 80)}" if r.get("ans") else ""))
            t = r.get("team") or {}
            if t.get("theme") or t.get("members"):
                L.append("　🎨 " + esc(t.get("theme", "—"), 40) + " · 👥 " + esc(", ".join(f"{x['name']} ({x['uid']})" for x in t.get("members", [])), 200))
        text = "\n".join(L) or "ยังไม่มีผู้สมัคร"
        if len(text) > 3800: text = text[:3800] + "\n…"
        e = discord.Embed(title=f"👥 ผู้สมัคร · {a.get('icon', '🎁')} {a.get('title', '')}", description=text, color=THEME_COL.get(a.get("theme"), 0xF2509F))
        e.set_footer(text=f"{len(regs)}" + (f"/{a['limit']}" if a.get("limit") else "") + f" คน · {SG_NAME.get(sg_state(a, len(regs)), '')}")
        await i.response.send_message(embed=e, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    async def signup_kick(i, aid):
        d = db(); a = by_id(d["signups"], aid); regs = d["regs"].get(aid, {})
        if not a or not regs: return await say(i, "ยังไม่มีผู้สมัครในกิจกรรมนี้")
        rows = [{"id": u, "name": r.get("name") or u} for u, r in sorted(regs.items(), key=lambda kv: kv[1].get("at", 0))]
        async def on_pick(i2, uid):
            row = next((x for x in rows if x["id"] == uid), {"name": uid})
            async def yes(i3):
                _, r = await drop_reg(aid, uid, by="admin")
                await i3.response.edit_message(content=f"🗑️ นำ **{row['name']}** ออกจาก **{a.get('title', '')}** แล้ว" if r else "⚠️ ไม่พบผู้สมัครคนนี้แล้ว", view=None)
            await i2.response.edit_message(content=f"นำ **{row['name']}** ออกจากกิจกรรม **{a.get('title', '')}** ใช่ไหม?", view=ConfirmView(yes))
        await i.response.edit_message(content="เลือกคนที่จะนำออก 👇", view=PickView(rows, lambda r: r["name"], on_pick, "เลือกผู้สมัคร"))

    async def signup_announce(i, aid):
        a = by_id(db()["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        ch = signup_room()
        if not ch: return await say(i, "⚠️ ยังไม่ได้ตั้งห้องสมัครกิจกรรม — กดปุ่ม 📝 ห้องสมัครกิจกรรม ที่แผงตั้งค่าเว็บ หรือสั่ง `/xmas` ใหม่")
        await i.response.defer(ephemeral=True)
        regs = db()["regs"].get(aid, {}); n = len(regs)
        emb = discord.Embed(title=f"{a.get('icon', '🎁')} {a.get('title', '')}", url=f"{PUBLIC}/#signup-{aid}", color=THEME_COL.get(a.get("theme"), 0xF2509F),
                            description=((a.get("desc") or "") + ("\n\n" + a["details"][:500] + ("…" if len(a["details"]) > 500 else "") if a.get("details") else "")).strip() or None)
        if a.get("date"): emb.add_field(name="📅 วันจัดกิจกรรม", value=th_date(a["date"], a.get("time", "")), inline=True)
        if a.get("close"): emb.add_field(name="⏳ ปิดรับสมัคร", value=th_date(a["close"], a.get("close_time", "")), inline=True)
        emb.add_field(name="👥 ผู้สมัคร", value=f"{n}" + (f" / {a['limit']}" if a.get("limit") else " คน"), inline=True)
        if a.get("place"): emb.add_field(name="📍 สถานที่", value=esc(a["place"], 60), inline=True)
        if a.get("prize"): emb.add_field(name="🎁 รางวัล", value=esc(a["prize"], 100), inline=True)
        emb.set_footer(text=f"MOCHI HOUSE · {SG_NAME.get(sg_state(a, n), '')}")
        kw, img = {}, a.get("image") or ""
        if UP_RE.fullmatch(img) and os.path.isfile(os.path.join(UPL, img[3:])):
            kw["file"] = discord.File(os.path.join(UPL, img[3:]), filename=img[3:]); emb.set_image(url="attachment://" + img[3:])
        elif img.startswith("https://"): emb.set_image(url=img)
        v = discord.ui.View(); v.add_item(discord.ui.Button(label=a.get("btn") or "สมัครเลยบนเว็บ", emoji="📝", style=discord.ButtonStyle.link, url=f"{PUBLIC}/#signup-{aid}"))
        try: await ch.send(embed=emb, view=v, **kw)
        except discord.Forbidden: return await i.followup.send(f"⚠️ บอทส่งข้อความใน {ch.mention} ไม่ได้ — ให้สิทธิ์ ส่งข้อความ · ฝังลิงก์ · แนบไฟล์", ephemeral=True)
        await i.followup.send(f"✅ ประกาศ **{a.get('title', '')}** ใน {ch.mention} แล้ว", ephemeral=True)

    async def signup_remove(i, aid):
        a = by_id(db()["signups"], aid)
        if not a: return await say(i, "⚠️ ไม่พบกิจกรรมนี้")
        n = len(db()["regs"].get(aid, {}))
        async def yes(i2):
            async with lock:
                d = db(); q = by_id(d["signups"], aid)
                if not q: return await i2.response.edit_message(content="⚠️ ไม่พบกิจกรรมนี้แล้ว", view=None)
                d["signups"].remove(q); d["regs"].pop(aid, None); save_json(DATA, d); drop_upload(q.get("image"))
            await i2.response.edit_message(content=f"🗑️ ลบกิจกรรม **{q.get('title', '')}** พร้อมรายชื่อผู้สมัครแล้ว", view=None)
        await i.response.edit_message(content=f"ลบกิจกรรม **{s_label(a)}** ใช่ไหม? (ผู้สมัคร {n} คนจะถูกลบด้วย)", view=ConfirmView(yes))

    async def signup_move(i, aid): await i.response.send_modal(MoveModal("signups", aid))

    class AdminSignupView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)

        async def _pick(self, i, fn, ph):
            if await guard(i): await pick(i, "signups", s_label, fn, ph, "ยังไม่มีกิจกรรมสมัคร — กด ➕ สร้างก่อน")

        @discord.ui.button(label="สร้างกิจกรรมสมัคร", emoji="➕", style=discord.ButtonStyle.success, custom_id="xmasa:r_add", row=0)
        async def r_add(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_modal(SignupModal())

        @discord.ui.button(label="แก้ไขข้อมูล", emoji="✏️", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_edit", row=0)
        async def r_edit(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_edit, "เลือกกิจกรรมที่จะแก้ไข")

        @discord.ui.button(label="เวลา / จำนวนคน / คำถาม", emoji="⚙️", style=discord.ButtonStyle.primary, custom_id="xmasa:r_rules", row=0)
        async def r_rules(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_rules, "เลือกกิจกรรมที่จะตั้งค่าการรับสมัคร")

        @discord.ui.button(label="ฟอร์มสมัคร (ทีม/UID/ธีม)", emoji="🧩", style=discord.ButtonStyle.primary, custom_id="xmasa:r_form", row=0)
        async def r_form(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_form, "เลือกกิจกรรมที่จะตั้งฟอร์มสมัคร")

        @discord.ui.button(label="แบนเนอร์ / สี / ยศ", emoji="🏞️", style=discord.ButtonStyle.primary, custom_id="xmasa:r_style", row=0)
        async def r_style(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_style, "เลือกกิจกรรมที่จะตั้งแบนเนอร์/สี/ยศ")

        @discord.ui.button(label="เปิด / ปิดรับสมัคร", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_close", row=1)
        async def r_close(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_closed_toggle, "เลือกกิจกรรมที่จะเปิด/ปิดรับสมัคร")

        @discord.ui.button(label="แสดง / ซ่อนบนเว็บ", emoji="👁️", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_off", row=1)
        async def r_off(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_off_toggle, "เลือกกิจกรรมที่จะแสดง/ซ่อน")

        @discord.ui.button(label="ดูรายชื่อผู้สมัคร", emoji="👥", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_roster", row=1)
        async def r_roster(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_roster, "เลือกกิจกรรมที่จะดูรายชื่อ")

        @discord.ui.button(label="ประกาศในห้องสมัคร", emoji="📣", style=discord.ButtonStyle.primary, custom_id="xmasa:r_post", row=1)
        async def r_post(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_announce, "เลือกกิจกรรมที่จะประกาศ")

        @discord.ui.button(label="นำผู้สมัครออก", emoji="🚫", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_kick", row=2)
        async def r_kick(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_kick, "เลือกกิจกรรมที่จะนำผู้สมัครออก")

        @discord.ui.button(label="ย้ายลำดับ", emoji="↕️", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_move", row=2)
        async def r_move(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_move, "เลือกกิจกรรมที่จะย้าย")

        @discord.ui.button(label="ลบกิจกรรม", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="xmasa:r_del", row=2)
        async def r_del(self, i: discord.Interaction, b: discord.ui.Button): await self._pick(i, signup_remove, "เลือกกิจกรรมที่จะลบ")

        @discord.ui.button(label="รายการทั้งหมด", emoji="📋", style=discord.ButtonStyle.secondary, custom_id="xmasa:r_list", row=2)
        async def r_list(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i):
                rows = await load_rows("signups")
                await i.response.send_message("📝 **กิจกรรมที่เปิดให้สมัคร**\n" + signup_list_text(rows), ephemeral=True)

    async def refresh_panel(ch, key, embed, view):
        """แก้ข้อความแผงเดิมในห้อง (ไม่ลบข้อความ 'สมัครแล้ว' ของคนอื่น) · ไม่มีก็ส่งใหม่"""
        mid = db()["site"].get(key)
        if mid:
            try:
                msg = await ch.fetch_message(int(mid)); await msg.edit(embed=embed, view=view); return
            except Exception: pass
        msg = await ch.send(embed=embed, view=view)
        async with lock:
            d = db(); d["site"][key] = str(msg.id); save_json(DATA, d)

    # ---------- 🔑 / 🎁 ปุ่มของทุกคน ----------
    class GiftModal(discord.ui.Modal):
        def __init__(self, target, private, anon):
            super().__init__(title="เขียนข้อความบนของขวัญ"); self.target, self.private, self.anon = target, private, anon
            self.f_msg = ti("ข้อความตัวใหญ่ (แทน MERRY CHRISTMAS)", "MERRY CHRISTMAS", max_length=60, required=False)
            self.f_note = ti("ข้อความเล็กใต้ข้อความหลัก (ไม่ใส่ก็ได้)", max_length=120, required=False, style=discord.TextStyle.paragraph)
            self.add_item(self.f_msg); self.add_item(self.f_note)

        async def on_submit(self, i: discord.Interaction):
            user = (i.guild.get_member(self.target.id) if i.guild else None) or self.target
            await do_gift(i, user, self.f_msg.value or "MERRY CHRISTMAS", self.f_note.value or None, self.private, self.anon)

    class GiftView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=300); self.target = None; self.private = False; self.anon = False

        def status(self):
            return (f"🎁 **ส่งของขวัญ**\n• ผู้รับ: {self.target.mention if self.target else '— ยังไม่ได้เลือก —'}\n"
                    f"• ส่งเป็น DM: {'เปิด' if self.private else 'ปิด (โพสต์ในห้องนี้)'}\n• ซ่อนชื่อผู้ให้: {'เปิด (ซานต้าลึกลับ)' if self.anon else 'ปิด'}")

        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="🎁 เลือกเพื่อนที่จะส่งให้", min_values=1, max_values=1, row=0)
        async def pick_user(self, i: discord.Interaction, s: discord.ui.UserSelect):
            self.target = s.values[0]; await i.response.edit_message(content=self.status(), view=self)

        @discord.ui.button(label="ส่งเป็น DM", emoji="🔒", style=discord.ButtonStyle.secondary, row=1)
        async def t_private(self, i: discord.Interaction, b: discord.ui.Button):
            self.private = not self.private; b.style = discord.ButtonStyle.primary if self.private else discord.ButtonStyle.secondary
            await i.response.edit_message(content=self.status(), view=self)

        @discord.ui.button(label="ซ่อนชื่อผู้ให้", emoji="🎭", style=discord.ButtonStyle.secondary, row=1)
        async def t_anon(self, i: discord.Interaction, b: discord.ui.Button):
            self.anon = not self.anon; b.style = discord.ButtonStyle.primary if self.anon else discord.ButtonStyle.secondary
            await i.response.edit_message(content=self.status(), view=self)

        @discord.ui.button(label="เขียนข้อความและส่ง", emoji="✍️", style=discord.ButtonStyle.success, row=2)
        async def go(self, i: discord.Interaction, b: discord.ui.Button):
            if not self.target: return await i.response.send_message("เลือกเพื่อนที่จะส่งให้ก่อนนะ 👆", ephemeral=True)
            await i.response.send_modal(GiftModal(self.target, self.private, self.anon))

    # ---------- แผงปุ่ม (ถาวร — ใช้ได้แม้บอทรีสตาร์ท) ----------
    class AdminPartnerView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)

        @discord.ui.button(label="ดิสคอร์ดพาร์ทเนอร์", emoji="➕", style=discord.ButtonStyle.success, custom_id="xmasa:p_add_sv", row=0)
        async def p_add_sv(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_modal(PartnerModal("server"))

        @discord.ui.button(label="พาร์ทเนอร์บุคคล", emoji="➕", style=discord.ButtonStyle.success, custom_id="xmasa:p_add_pe", row=0)
        async def p_add_pe(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_message("เลือกสมาชิกที่จะเป็นพาร์ทเนอร์ (หรือกรอกเอง) 👇", view=PersonStartView(), ephemeral=True)

        @discord.ui.button(label="ตั้งคำโปรโมท", emoji="📣", style=discord.ButtonStyle.primary, custom_id="xmasa:p_promo", row=0)
        async def p_promo(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "partners", p_label, partner_promo, "เลือกพาร์ทเนอร์ที่จะตั้งคำโปรโมท", "ยังไม่มีพาร์ทเนอร์ — กด ➕ เพิ่มก่อน")

        @discord.ui.button(label="ตั้งแบนเนอร์ / รูป", emoji="🏞️", style=discord.ButtonStyle.primary, custom_id="xmasa:p_cover", row=0)
        async def p_cover(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "partners", p_label, partner_cover, "เลือกพาร์ทเนอร์ที่จะตั้งแบนเนอร์", "ยังไม่มีพาร์ทเนอร์ — กด ➕ เพิ่มก่อน")

        @discord.ui.button(label="แก้ไข", emoji="✏️", style=discord.ButtonStyle.secondary, custom_id="xmasa:p_edit", row=1)
        async def p_edit(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "partners", p_label, partner_edit, "เลือกพาร์ทเนอร์ที่จะแก้ไข", "ยังไม่มีพาร์ทเนอร์")

        @discord.ui.button(label="ย้ายลำดับ", emoji="↕️", style=discord.ButtonStyle.secondary, custom_id="xmasa:p_move", row=1)
        async def p_move(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "partners", p_label, partner_move, "เลือกพาร์ทเนอร์ที่จะย้าย", "ยังไม่มีพาร์ทเนอร์")

        @discord.ui.button(label="ลบ", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="xmasa:p_del", row=1)
        async def p_del(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "partners", p_label, partner_remove, "เลือกพาร์ทเนอร์ที่จะลบ", "ยังไม่มีพาร์ทเนอร์")

        @discord.ui.button(label="รายการทั้งหมด", emoji="📋", style=discord.ButtonStyle.secondary, custom_id="xmasa:p_list", row=1)
        async def p_list(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_message("🤝 **พาร์ทเนอร์บนเว็บ**  (📣 = มีคำโปรโมท)\n" + partner_text(db()["partners"]), ephemeral=True)

    class AdminBannerView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)

        @discord.ui.button(label="เพิ่มแบนเนอร์", emoji="➕", style=discord.ButtonStyle.success, custom_id="xmasa:b_add", row=0)
        async def b_add(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_modal(BannerModal())

        @discord.ui.button(label="แก้ไข", emoji="✏️", style=discord.ButtonStyle.secondary, custom_id="xmasa:b_edit", row=0)
        async def b_edit(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "banners", b_label, banner_edit, "เลือกแบนเนอร์ที่จะแก้ไข", "ยังไม่มีแบนเนอร์ที่ตั้งเอง — กด ➕ เพิ่มก่อน")

        @discord.ui.button(label="ย้ายลำดับ", emoji="↕️", style=discord.ButtonStyle.secondary, custom_id="xmasa:b_move", row=0)
        async def b_move(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "banners", b_label, banner_move, "เลือกแบนเนอร์ที่จะย้าย", "ยังไม่มีแบนเนอร์ที่ตั้งเอง")

        @discord.ui.button(label="ลบ", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="xmasa:b_del", row=0)
        async def b_del(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await pick(i, "banners", b_label, banner_remove, "เลือกแบนเนอร์ที่จะลบ", "ยังไม่มีแบนเนอร์ที่ตั้งเอง")

        @discord.ui.button(label="รายการ", emoji="📋", style=discord.ButtonStyle.secondary, custom_id="xmasa:b_list", row=1)
        async def b_list(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_message("🎞️ **แบนเนอร์บนเว็บ**\n" + banner_list_text(db()["banners"]), ephemeral=True)

        @discord.ui.button(label="ล้างทั้งหมด", emoji="🧹", style=discord.ButtonStyle.danger, custom_id="xmasa:b_clear", row=1)
        async def b_clear(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await banner_clear(i)

        @discord.ui.button(label="แสดง / ซ่อน", emoji="👁️", style=discord.ButtonStyle.secondary, custom_id="xmasa:b_toggle", row=1)
        async def b_toggle(self, i: discord.Interaction, b: discord.ui.Button):
            async def go(i2, bid):
                bb = await toggle_banner(bid)
                await i2.response.edit_message(content=("✅ " + toggle_text(bb)) if bb else "⚠️ ไม่พบแบนเนอร์นี้", view=None)
            if await guard(i): await pick(i, "banners", b_label, go, "เลือกแบนเนอร์ที่จะแสดง/ซ่อน", "ยังไม่มีแบนเนอร์ที่ตั้งเอง — กด ➕ เพิ่มก่อน")

    class AdminSiteView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)

        @discord.ui.button(label="หน้าเข้าร่วม", emoji="⚙️", style=discord.ButtonStyle.primary, custom_id="xmasa:s_site", row=0)
        async def s_site(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_modal(SiteModal())

        @discord.ui.button(label="หน้าโหลดเว็บ (สไลด์แบนเนอร์)", emoji="🎬", style=discord.ButtonStyle.primary, custom_id="xmasa:s_intro", row=0)
        async def s_intro(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_modal(IntroModal())

        @discord.ui.button(label="ห้องรูปภาพ", emoji="🖼️", style=discord.ButtonStyle.secondary, custom_id="xmasa:s_gal", row=1)
        async def s_gal(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await room_open(i, "gallery")

        @discord.ui.button(label="ห้องมีเดีย", emoji="🎬", style=discord.ButtonStyle.secondary, custom_id="xmasa:s_media", row=1)
        async def s_media(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await room_open(i, "media")

        @discord.ui.button(label="ห้องคอมเม้น", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="xmasa:s_cm", row=1)
        async def s_cm(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await room_open(i, "cforum")

        @discord.ui.button(label="ห้องคนออก", emoji="🚪", style=discord.ButtonStyle.secondary, custom_id="xmasa:s_leave", row=1)
        async def s_leave(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await room_open(i, "leave")

        @discord.ui.button(label="ห้องสมัครกิจกรรม", emoji="📝", style=discord.ButtonStyle.secondary, custom_id="xmasa:s_signup", row=1)
        async def s_signup(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await room_open(i, "signup")

    class AdminToolsView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)

        @discord.ui.button(label="โพสต์โปรโมทเว็บ", emoji="📣", style=discord.ButtonStyle.primary, custom_id="xmasa:t_promo", row=0)
        async def t_promo(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_message("เลือกห้องที่จะโพสต์ 👇", view=PromoChannelView(), ephemeral=True)

        @discord.ui.button(label="สถิติเข้าเว็บ", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="xmasa:t_stats", row=0)
        async def t_stats(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_message("เลือกช่วงเวลา 👇", view=PeriodView(), ephemeral=True)

        @discord.ui.button(label="ดูค่าตั้งทั้งหมด", emoji="📋", style=discord.ButtonStyle.secondary, custom_id="xmasa:t_over", row=0)
        async def t_over(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await i.response.send_message(embed=overview_embed(), ephemeral=True)

        @discord.ui.button(label="ทดสอบ DM คนเข้าใหม่", emoji="📨", style=discord.ButtonStyle.secondary, custom_id="xmasa:t_dmj", row=1)
        async def t_dmj(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await dm_test(i, "join")

        @discord.ui.button(label="ทดสอบ DM คนออก", emoji="📨", style=discord.ButtonStyle.secondary, custom_id="xmasa:t_dml", row=1)
        async def t_dml(self, i: discord.Interaction, b: discord.ui.Button):
            if await guard(i): await dm_test(i, "leave")

    class PublicView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(discord.ui.Button(label="เข้าเว็บบ้านโมชิ", emoji="🌐", style=discord.ButtonStyle.link, url=PUBLIC, row=1))
            self.add_item(discord.ui.Button(label="แกลเลอรี", emoji="🖼️", style=discord.ButtonStyle.link, url=PUBLIC + "/gallery", row=1))
            self.add_item(discord.ui.Button(label="สมัครกิจกรรม", emoji="📝", style=discord.ButtonStyle.link, url=PUBLIC + "/#signup", row=1))

        @discord.ui.button(label="รับโค้ดเข้าเว็บ", emoji="🔑", style=discord.ButtonStyle.success, custom_id="xmasp:code", row=0)
        async def p_code(self, i: discord.Interaction, b: discord.ui.Button): await give_code(i)

        @discord.ui.button(label="ส่งของขวัญให้เพื่อน", emoji="🎁", style=discord.ButtonStyle.primary, custom_id="xmasp:gift", row=0)
        async def p_gift(self, i: discord.Interaction, b: discord.ui.Button):
            v = GiftView(); await i.response.send_message(v.status(), view=v, ephemeral=True)

    # ---------- สร้าง/ซ่อมห้อง + โพสต์แผงปุ่ม ----------
    async def ensure_room(gd, key, name, topic, ow, cat):
        cid = db()["site"].get(key)
        try: ch = gd.get_channel(int(cid)) if cid else None
        except Exception: ch = None
        if isinstance(ch, discord.TextChannel): return ch
        ch = await gd.create_text_channel(name=name, category=cat, overwrites=ow, topic=topic, reason="MOCHI HOUSE web panel")
        async with lock:
            d = db(); d["site"][key] = str(ch.id); save_json(DATA, d)
        return ch

    async def wipe_mine(ch):
        try: await asyncio.wait_for(ch.purge(limit=60, check=lambda m: m.author.id == bot.user.id), 20)
        except Exception: pass

    def panel_embed(title, desc):
        return discord.Embed(title=title, description=desc, color=0xF2509F)

    @bot.tree.command(name="xmas", description="แอดมิน: สร้าง/ซ่อมห้องควบคุมเว็บ + ห้องเมนูเว็บ (ทุกอย่างเป็นปุ่ม ไม่ต้องพิมพ์คำสั่งอื่นอีก)")
    @discord.app_commands.guild_only()
    @discord.app_commands.default_permissions(administrator=True)
    async def xmas_cmd(i: discord.Interaction):
        if not is_admin(i): return await deny(i)
        await i.response.defer(ephemeral=True)
        try:   # ไม่ว่าจะพลาดตรงไหน ต้องตอบกลับเสมอ (เดิมถ้าเกิด error จะค้าง "กำลังคิด..." ไม่จบ)
            await asyncio.wait_for(xmas_run(i), 240)
        except asyncio.TimeoutError:
            await i.followup.send("⏳ ใช้เวลานานเกินไป (ดิสคอร์ดอาจจำกัดอัตราการลบ/สร้างข้อความ) — รอสัก 1-2 นาทีแล้วสั่ง `/xmas` ใหม่ได้เลย ห้องที่สร้างไปแล้วไม่หาย", ephemeral=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            try: await i.followup.send(f"⚠️ /xmas ไม่สำเร็จ: `{type(e).__name__}: {str(e)[:300]}`\nส่งข้อความนี้ให้ผู้ดูแลบอทได้เลย", ephemeral=True)
            except Exception: pass

    async def xmas_run(i: discord.Interaction):
        gd, me = i.guild, i.guild.me
        gch = gal_channel(); cat = gch.category if gch else None
        bot_ow = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, read_message_history=True, attach_files=True, manage_messages=True)
        try:
            ow_admin = {gd.default_role: discord.PermissionOverwrite(view_channel=False), me: bot_ow}
            ow_pub = {gd.default_role: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=False, add_reactions=False, create_public_threads=False, create_private_threads=False, send_messages_in_threads=False), me: bot_ow}
            ach = await ensure_room(gd, "panel_admin", "🎛️│ควบคุมเว็บ", "🎛️ ห้องควบคุมเว็บบ้านโมชิ — กดปุ่มได้เลย ไม่ต้องพิมพ์คำสั่ง (เห็นเฉพาะแอดมิน)", ow_admin, cat)
            pch = await ensure_room(gd, "panel_public", "🎄│เมนูเว็บบ้านโมชิ", "🎄 รับโค้ดเข้าเว็บ · ส่งของขวัญให้เพื่อน — กดปุ่มด้านล่าง", ow_pub, cat)
        except discord.Forbidden:
            return await i.followup.send("⚠️ สร้างห้องไม่ได้ — ให้สิทธิ์บอท **จัดการช่อง (Manage Channels)** ก่อน แล้วสั่ง `/xmas` ใหม่", ephemeral=True)
        except Exception as e:
            return await i.followup.send(f"⚠️ สร้างห้องไม่สำเร็จ: {type(e).__name__}: {e}", ephemeral=True)
        try:
            await wipe_mine(ach)
            await ach.send(embed=panel_embed("🎛️ ห้องควบคุมเว็บ MOCHI HOUSE", "กดปุ่มด้านล่างจัดการเว็บได้ทั้งหมด **ไม่ต้องพิมพ์คำสั่ง**\nเห็นและกดได้เฉพาะแอดมิน · ผลขึ้นบนเว็บภายในไม่กี่วินาที\n\n"
                                          "**🤝 พาร์ทเนอร์** — เพิ่ม/แก้ไข/ลบ/ย้าย · **📣 ตั้งคำโปรโมท** = ข้อความที่เด้งเมื่อคนกด “ดูรายละเอียด” · **🏞️ ตั้งแบนเนอร์** = รูปปกด้านหลังโปรไฟล์ (ดิสและบุคคล)"), view=AdminPartnerView())
            await ach.send(embed=panel_embed("🎞️ แบนเนอร์กิจกรรม", "แบนเนอร์/ไฮไลต์เลื่อนบนหน้าแรกของเว็บ · **รูปแนะนำ 16:9 (1280×720)** — มือถือแสดงเต็มทั้งภาพไม่โดนตัด\n🎨 สี · 🖼️ รูป · 😀 ไอคอน/ป้าย/ข้อความปุ่ม · 👁️ ซ่อน-แสดง · ใส่ลิงก์ `#signup` เพื่อให้ปุ่มพาไปหมวดสมัครกิจกรรม\nไม่มีแบนเนอร์ที่ตั้งเอง = ดึงจากตารางกิจกรรมอัตโนมัติ"), view=AdminBannerView())
            await ach.send(embed=panel_embed("⚙️ ตั้งค่าเว็บ + ห้องต่างๆ", "หน้าเข้าร่วม · 🎬 หน้าโหลดเว็บ (สไลด์แบนเนอร์ไฮไลต์ + ตั้งเวลารวม) · ห้องรูปภาพ (แกลเลอรี) · ห้องมีเดีย · ห้องคอมเม้น · ห้องที่รับคำตอบ “ทำไมถึงออก” · 📝 ห้องสมัครกิจกรรม (ที่ข้อความ “สมัครแล้ว” จะเด้ง)"), view=AdminSiteView())
            await ach.send(embed=panel_embed("🧰 เครื่องมือ", "โพสต์โปรโมทเว็บ · สถิติคนเข้าเว็บ · ทดสอบ DM · ดูค่าตั้งทั้งหมด"), view=AdminToolsView())
            await wipe_mine(pch)
            pe = panel_embed("🎄 เมนูเว็บบ้านโมชิ", "🔑 **รับโค้ดเข้าเว็บ** — โค้ด 6 ตัว ใช้ล็อกอินบนเว็บ (หมดอายุ 5 นาที · ใช้ได้ครั้งเดียว)\n🎁 **ส่งของขวัญให้เพื่อน** — ต้นคริสต์มาสพร้อมข้อความของคุณจะขึ้นในบัญชีเขาบนเว็บ\n\nกดปุ่มด้านล่างได้เลย 👇")
            pe.url = PUBLIC; pe.set_footer(text="MOCHI HOUSE · Merry Christmas 2026")
            await pch.send(embed=pe, view=PublicView())
        except discord.Forbidden:
            return await i.followup.send(f"⚠️ บอทส่งข้อความใน {ach.mention} / {pch.mention} ไม่ได้ — ให้สิทธิ์ **ส่งข้อความ · ฝังลิงก์** แล้วสั่ง `/xmas` ใหม่", ephemeral=True)
        except discord.HTTPException as e:
            return await i.followup.send(f"⚠️ ส่งแผงปุ่มไม่สำเร็จ: `{e.status} {str(e.text)[:300]}`", ephemeral=True)
        # ---- 🗓️ ห้องจัดการกิจกรรม (แอดมิน) + 📝 ห้องสมัครกิจกรรม (ทุกคนอ่านได้) ----
        try:
            ech = await ensure_room(gd, "panel_events", "🗓️│จัดการกิจกรรม", "🗓️ จัดการกิจกรรมตลอดเทศกาล + สมัครกิจกรรม — กดปุ่มได้เลย ไม่ต้องพิมพ์คำสั่ง (เห็นเฉพาะแอดมิน)", ow_admin, cat)
            sch = await ensure_room(gd, "signup", "📝│สมัครกิจกรรม", "📝 คนที่สมัครกิจกรรมบนเว็บบ้านโมชิจะเด้งขึ้นที่นี่ทันที — สมัครได้ที่เว็บ เมนูขีดสามขีด → สมัครกิจกรรม", ow_pub, cat)
            await wipe_mine(ech)
            await ech.send(embed=panel_embed("🗓️ กิจกรรมตลอดเทศกาล", "แก้ตารางกิจกรรมที่ขึ้นบนเว็บ (ไทม์ไลน์ + ปฏิทิน + ไฮไลต์อัตโนมัติ) ด้วยปุ่มได้เลย\n"
                                                              "➕ เพิ่ม · ✏️ แก้ไข · 🗑️ ลบ · 🔄 รีเซ็ตกลับค่าจากไฟล์ `xmas_config.json`\n-# ครั้งแรกที่กด บอทจะคัดลอกตารางจากไฟล์มาให้แก้ต่ออัตโนมัติ"), view=AdminEventView())
            await ech.send(embed=panel_embed("📝 สมัครกิจกรรม (หมวดในเมนูขีดสามขีดบนเว็บ)", "สร้างกิจกรรมให้คนสมัครบนเว็บ ตั้งค่าได้ทุกอย่าง:\n"
                                                              "• ชื่อ/คำอธิบาย/กติกา/รางวัล/สถานที่/วันเวลา · 🏞️ **แบนเนอร์ (แนะนำ 16:9 — มือถือเห็นเต็มภาพ)** · 🎨 สี\n"
                                                              "• ⚙️ วันเปิด-ปิดรับสมัคร · จำนวนที่รับ (เต็มแล้วปิดเอง) · คำถามให้ตอบ · ข้อความบนปุ่ม · 🏷️ ยศอัตโนมัติ\n"
                                                              "• 🧩 ฟอร์มสมัคร: ทีม (ชื่อ + UID ในเกมของสมาชิก) · ชื่อธีม · อัปโหลดแบนเนอร์/โลโก้ธีม (ไม่บังคับ) — ผู้สมัครเห็นใบสมัครของตัวเองบนเว็บ\n"
                                                              "• 👥 ดูรายชื่อ · 🚫 นำผู้สมัครออก · 📣 ประกาศในห้องสมัคร · 🔒 เปิด/ปิด · 👁️ ซ่อน/แสดง\n"
                                                              f"เมื่อมีคนสมัครบนเว็บ ข้อความ **“สมัครแล้ว”** จะเด้งเข้า {sch.mention} ทันที"), view=AdminSignupView())
            pe2 = panel_embed("📝 สมัครกิจกรรม MOCHI HOUSE", "สมัครกิจกรรมได้ที่เว็บ — กดปุ่มด้านล่าง หรือเมนูขีดสามขีด → **สมัครกิจกรรม**\n"
                                                           "ใครสมัครแล้วจะมีข้อความ **✅ สมัครแล้ว** เด้งขึ้นที่ห้องนี้ให้ทุกคนเห็นทันที\n\n🔑 ล็อกอินด้วยโค้ดจากปุ่ม **รับโค้ดเข้าเว็บ** ในห้องเมนูเว็บ")
            pe2.url = PUBLIC + "/#signup"; pe2.set_footer(text="MOCHI HOUSE · Merry Christmas 2026")
            pv2 = discord.ui.View(); pv2.add_item(discord.ui.Button(label="ไปสมัครกิจกรรมบนเว็บ", emoji="📝", style=discord.ButtonStyle.link, url=PUBLIC + "/#signup"))
            await refresh_panel(sch, "signup_panel", pe2, pv2)
        except discord.Forbidden:
            return await i.followup.send("⚠️ สร้าง/ส่งข้อความในห้องกิจกรรมไม่ได้ — ให้สิทธิ์บอท **จัดการช่อง · ส่งข้อความ · ฝังลิงก์** แล้วสั่ง `/xmas` ใหม่", ephemeral=True)
        except Exception as e:
            return await i.followup.send(f"⚠️ สร้างห้องกิจกรรมไม่สำเร็จ: {type(e).__name__}: {e}", ephemeral=True)
        await i.followup.send(f"✅ พร้อมใช้งานแล้ว\n🎛️ ห้องควบคุม (เฉพาะแอดมิน): {ach.mention}\n🗓️ ห้องจัดการกิจกรรม (เฉพาะแอดมิน): {ech.mention}\n🎄 ห้องเมนูเว็บ (ทุกคน): {pch.mention}\n📝 ห้องสมัครกิจกรรม (ทุกคน · ข้อความ “สมัครแล้ว” เด้งที่นี่): {sch.mention}\n🔗 Redirect URI สำหรับล็อกอิน Discord: `{PUBLIC}/api/xmas/oauth/callback`\n-# ต่อจากนี้ไม่ต้องพิมพ์คำสั่งอีก — สั่ง `/xmas` ซ้ำได้เมื่ออยากรีเฟรชแผงปุ่ม", ephemeral=True)

    views_done = {"v": False}
    async def xm_views():
        if views_done["v"]: return
        views_done["v"] = True
        for V in (AdminPartnerView, AdminBannerView, AdminSiteView, AdminToolsView, PublicView, AdminEventView, AdminSignupView):
            try: bot.add_view(V())
            except Exception as ex: print(f"   ✖ ลงทะเบียนแผงปุ่ม {V.__name__} ไม่สำเร็จ: {ex}")
        try: bot.add_view(LeaveView())
        except Exception as ex: print(f"   ✖ ลงทะเบียนปุ่มแบบฟอร์มตอนออกไม่สำเร็จ: {ex}")

    # ---- 🚫 เตะคนที่กด F2 / F12 / Ctrl+U / Ctrl+Shift+I,J,C ดูข้อมูลเว็บ ----
    # หน้าเว็บส่ง POST /api/xmas/kick มา → แบน IP นั้นชั่วคราว (XMAS_KICK_MIN นาที, 0 = ปิดระบบ)
    KICK_MIN = float(os.getenv("XMAS_KICK_MIN", "10") or 0)
    kicked = {}
    KICK_HTML = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>🚫 ถูกเตะออก</title>"
                 "<body style='margin:0;min-height:100vh;display:grid;place-items:center;background:#150A30;color:#FFE0F4;font:600 20px/1.6 system-ui,sans-serif;text-align:center;padding:24px'>"
                 "<div><div style='font-size:56px'>🚫</div>ตรวจพบการเปิดดูข้อมูลเว็บ (F2 / F12)<br><span style='font-weight:400;font-size:15px;opacity:.8'>คุณถูกเตะออกจากเว็บชั่วคราว ลองใหม่ภายหลัง</span></div>")
    def is_kicked(req):
        if not KICK_MIN: return False
        ip = req_ip(req); t = kicked.get(ip)
        if not t: return False
        if t < time.time(): kicked.pop(ip, None); return False
        return True

    async def kick(req):
        if KICK_MIN and not limited(req, "kick", 20, 60):
            if len(kicked) > 5000: kicked.clear()
            kicked[req_ip(req)] = time.time() + KICK_MIN * 60
        return web.Response(status=204)

    # ---- 💓 จุดให้ UptimeRobot ยิง Ping (รองรับทั้ง GET และ HEAD) ไม่เข้าสถิติ ไม่แตะฐานข้อมูล ----
    async def ping(req):
        return web.Response(text="ok", content_type="text/plain")

    @web.middleware
    async def mw(req, handler):
        if req.method == "OPTIONS": resp = web.Response()
        elif req.path not in ("/ping", "/healthz") and is_kicked(req):
            resp = web.Response(status=403, text=KICK_HTML, content_type="text/html", charset="utf-8")
        else:
            try: resp = await handler(req)
            except web.HTTPException as ex: resp = ex
        if ORIGIN:
            resp.headers["Access-Control-Allow-Origin"] = ORIGIN
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Cache-Control"] = "public, max-age=86400" if req.path.startswith("/u/") else "no-store" if req.path in ("/ping", "/healthz") or req.path.startswith(("/api/xmas/me", "/api/xmas/gifts", "/api/xmas/gallery", "/api/xmas/signup")) or req.method == "POST" else "public, max-age=10"
        return resp

    started = {"v": False, "w": False}
    async def _serve():
        """เปิดเว็บเซิร์ฟเวอร์ทันทีที่บอทเริ่มรัน (ไม่รอล็อกอินดิสคอร์ด) → Render เห็นพอร์ตเปิดเร็ว ไม่ขึ้น 'No open ports detected'"""
        if started["v"]: return
        started["v"] = True
        try:
            app = web.Application(middlewares=[mw], client_max_size=8192)
            app.add_routes([web.get("/", index), web.get("/ping", ping), web.get("/healthz", ping), web.post("/api/xmas/kick", kick), web.get("/api/xmas/stats", stats), web.get("/api/xmas/members", members), web.get("/api/xmas/info", info),
                web.post("/api/xmas/login", login), web.get("/api/xmas/oauth/start", oauth_start), web.get("/api/xmas/oauth/callback", oauth_callback), web.get("/api/xmas/oauth/status", oauth_status), web.get("/api/xmas/me", me),
                web.post("/api/xmas/claim", claim), web.post("/api/xmas/santa", santa),
                web.get("/api/xmas/gifts", gifts), web.post("/api/xmas/gifts/seen", gift_seen), web.post("/api/xmas/gifts/delete", gift_delete),
                web.get("/api/xmas/banners", banners), web.get("/api/xmas/signups", signups), web.post("/api/xmas/signup", signup_join), web.post("/api/xmas/signup/upload", signup_upload), web.post("/api/xmas/signup/cancel", signup_cancel), web.get("/api/xmas/site", site), web.post("/api/xmas/report", report), web.post("/api/xmas/partner-apply", partner_apply), web.get("/{name:og\\.(?:gif|jpg)}", og_file),
                web.get("/gift/{gid}", gift_redirect), web.get("/gallery", gallery_page), web.get("/u/{name}", upload_file), web.post("/api/xmas/track", track), web.get("/api/xmas/gallery", gallery), web.post("/api/xmas/gallery/comment", gal_comment), web.post("/api/xmas/gallery/comment/delete", gal_cdel), web.post("/api/xmas/gallery/like", gal_like), web.post("/api/xmas/gallery/post", gal_post), web.post("/api/xmas/gallery/post/delete", gal_post_del)])
            runner = web.AppRunner(app, access_log=None); await runner.setup()
            await web.TCPSite(runner, HOST, PORT).start()
            print(f"   ✔ เว็บคริสต์มาส MOCHI HOUSE พร้อมที่ {PUBLIC} (พอร์ต {PORT})")
        except Exception as e:
            started["v"] = False
            print(f"   ✖ เว็บคริสต์มาสเริ่มไม่ได้ (บอทปกติ): {type(e).__name__}: {e}")

    async def self_ping():
        """สำรอง: ยิง /ping ใส่ลิงก์ตัวเองทุก 10 นาที กัน Render ฟรีหลับ (ปิดได้ด้วย XMAS_SELF_PING=0)"""
        url = fix_url(os.getenv("RENDER_EXTERNAL_URL") or "")
        if not url or os.getenv("XMAS_SELF_PING", "1") == "0": return
        await asyncio.sleep(60)
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=15)) as cs:
                    async with cs.get(url + "/ping") as r: await r.read()
            except Exception: pass
            await asyncio.sleep(600)

    async def _start():
        await _serve()
        if started["w"]: return
        started["w"] = True
        asyncio.create_task(gl_worker()); asyncio.create_task(xt_flush_loop()); asyncio.create_task(self_ping())

    # เปิดเว็บตั้งแต่ setup_hook (ก่อนล็อกอินดิสคอร์ด) · ถ้า hook ใช้ไม่ได้ ก็ยังมี on_ready เป็นตัวสำรอง
    _old_hook = bot.setup_hook
    async def _hook():
        try: await _old_hook()
        finally: await _serve()
    try: bot.setup_hook = _hook
    except Exception: pass
    bot.add_listener(_start, "on_ready")
    bot.add_listener(gal_on_message, "on_message")
    bot.add_listener(gal_on_delete, "on_raw_message_delete")
    bot.add_listener(gp_on_delete, "on_raw_message_delete")
    bot.add_listener(gl_on_delete, "on_raw_message_delete")
    bot.add_listener(xm_on_join, "on_member_join")
    bot.add_listener(xm_on_remove, "on_member_remove")
    bot.add_listener(xm_views, "on_ready")
    bot.add_listener(gd_on_add, "on_raw_reaction_add")
    bot.add_listener(gd_on_remove, "on_raw_reaction_remove")
    print("   ✔ โหลดระบบเว็บคริสต์มาสแล้ว")