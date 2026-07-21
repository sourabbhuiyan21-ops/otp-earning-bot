import logging
import re
import httpx
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

# ================== CREDENTIALS ==================
TOKEN = "8870078495:AAESL6GUbWfuR_OwUD6Pi7cdlgNBc3NiF2Y"
API_KEY = "MURAD_12B9CA6C873901539718ACB1"

UPDATE_CHANNEL = "@META_FIRE_UPDATE"
OTP_CHANNEL = "@META_FIRE_OTP"

active_otp_tasks = {}
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP")]
], resize_keyboard=True, is_persistent=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================== API CALL ==================
async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=12.0) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload, headers=headers)
            return r.json() if r.status_code == 200 else None
    except Exception as e:
        logging.error(f"API Error: {e}")
        return None

async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except:
        return False

# শুধুমাত্র রেঞ্জ থেকে প্রিফিক্স দেখাবে (কোনো ভুয়া দেশ নয়)
def get_range_display(range_str):
    clean = re.sub(r'\D', '', str(range_str))
    return f"+{clean[:3]}..."

# ================== START ==================
async def start(update: Update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Update Channel", url="https://t.me/META_FIRE_UPDATE")],
            [InlineKeyboardButton("📢 Join OTP Channel", url="https://t.me/META_FIRE_OTP")],
            [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]
        ]
        await update.message.reply_text(f"🌟 **SUPER FIRE OTP**\n\nস্বাগতম {user_name}!\nচ্যানেলে জয়েন করে ভেরিফাই করুন।", 
                                      reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"🎉 স্বাগতম {user_name}!\n🌟 SUPER FIRE OTP", reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)

# ================== CALLBACK ==================
async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text="✅ ভেরিফাই সফল!", reply_markup=main_keyboard)
        else:
            await query.answer("❗ চ্যানেলে জয়েন করুন!", show_alert=True)

    elif query.data.startswith("service_"):
        await query.message.delete()
        await show_ranges(query.message, query.data.split("_")[1])

    elif query.data.startswith("range_") or query.data.startswith("chgnum_"):
        parts = query.data.split("_")
        if query.message.chat_id in active_otp_tasks:
            active_otp_tasks[query.message.chat_id].cancel()
        
        status = await query.message.edit_text("⚡ নাম্বার অ্যালোকেট করা হচ্ছে...")
        res = await call_website_api_async("getnum", "POST", {"range": parts[2]})
        
        if res and res.get("meta", {}).get("status") == "ok":
            num = res["data"].get("full_number") or res["data"].get("number")
            btn = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{parts[1]}_{parts[2]}")]]
            await status.edit_text(f"🚀 **NUMBER ALLOCATED**\n📱 `+{re.sub(r'\D', '', str(num))}`\n⏳ Waiting for OTP...", 
                                 reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.MARKDOWN)
            active_otp_tasks[query.message.chat_id] = asyncio.create_task(check_otp(context, query.message.chat_id, num))
        else:
            await status.edit_text("❌ Server Busy!")

    elif query.data == "back_to_services":
        await query.message.delete()
        await show_services(query.message)

async def show_services(msg):
    kb = [
        [InlineKeyboardButton("🔷 FACEBOOK 🔷", callback_data="service_facebook")],
        [InlineKeyboardButton("📸 INSTAGRAM 📸", callback_data="service_instagram")]
    ]
    await msg.reply_text("🌐 **Select Platform**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

async def show_ranges(msg, service):
    res = await call_website_api_async("liveaccess", "GET")
    if not res:
        await msg.reply_text("❌ API থেকে তথ্য আনা যায়নি।")
        return

    kb = []
    seen = set()
    target = service.lower()

    for s in res.get("services", []):
        sid = s.get("sid", "").lower()
        if target in sid or (target == "instagram" and ("ig" in sid or "insta" in sid)):
            for r in s.get("ranges", []):
                display = get_range_display(r)
                if display not in seen:
                    seen.add(display)
                    kb.append([InlineKeyboardButton(display, callback_data=f"range_{service}_{r}")])

    if not kb:
        await msg.reply_text(f"❌ {service.upper()} এর জন্য কোনো রেঞ্জ পাওয়া যায়নি।")
        return

    kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_services")])
    await msg.reply_text(f"🌍 **{service.upper()} Available Ranges**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

async def check_otp(context, chat_id, number):
    full = re.sub(r'\D', '', str(number))
    for _ in range(900):
        await asyncio.sleep(2)
        res = await call_website_api_async("success-otp-info", "GET")
        if res and "data" in res and "otps" in res["data"]:
            for item in res["data"]["otps"]:
                if full in re.sub(r'\D', '', str(item.get("number", ""))):
                    otp = item.get("otp") or item.get("code")
                    if otp:
                        await context.bot.send_message(chat_id, f"✅ **OTP RECEIVED**\n📱 +{number}\n🔑 `{otp}`", parse_mode=ParseMode.MARKDOWN)
                        return
    await context.bot.send_message(chat_id, f"❌ +{number} এর জন্য OTP আসেনি।")

async def text_handler(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await start(update, context)
        return

    text = update.message.text
    if "GET NUMBER" in text:
        await show_services(update.message)
    elif "2FA CODE" in text:
        await update.message.reply_text("🔐 2FA CODE\n\nনাম্বার পাঠান:")
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 Live OTP Channel", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

if __name__ == "__main__":
    logging.info("🚀 SUPER FIRE OTP Bot Started!")
    app.run_polling()
