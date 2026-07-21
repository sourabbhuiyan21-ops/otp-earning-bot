import logging
import re
import os
import httpx
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

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

def get_country_details(range_str):
    clean = re.sub(r'\D', '', str(range_str))
    prefix = clean[:3]
    countries = {
        "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
        "224": {"name": "Guinea", "flag": "🇬🇳"},
        "225": {"name": "Ivory Coast", "flag": "🇨🇮"},
    }
    return countries.get(prefix, {"name": f"Server {prefix}", "flag": "🌍"})

# ================== START ==================
async def start(update: Update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]
        ]
        await update.message.reply_text(f"🌟 **SUPER FIRE OTP BOT**\n\n👋 স্বাগতম {user_name}!\nচ্যানেলে জয়েন করে ভেরিফাই করুন।", 
                                      reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"🎉 স্বাগতম {user_name}!\n\n🌟 SUPER FIRE OTP - সকল সুবিধা উন্মুক্ত", 
                                      reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)

# ================== 2FA CONVERSATION ==================
async def twofa_start(update: Update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await start(update, context)
        return ConversationHandler.END
    await update.message.reply_text("🔐 **2FA CODE**\n\nযে নাম্বারের 2FA কোড চান সেটি পাঠান (যেমন: +88017xxxxxxxx)")
    return 1

async def twofa_number_received(update: Update, context):
    number = update.message.text
    await update.message.reply_text(f"🔍 `{number}` এর জন্য 2FA/OTP মনিটরিং শুরু হয়েছে...")
    context.user_data['2fa_number'] = number
    asyncio.create_task(check_otp(context, update.message.chat_id, number))
    return ConversationHandler.END

# ================== OTP CHECKER (GET NUMBER + 2FA উভয়ের জন্য) ==================
async def check_otp(context, chat_id, number):
    full_number = re.sub(r'\D', '', str(number))
    for attempt in range(900):
        await asyncio.sleep(2)
        try:
            res = await call_website_api_async("success-otp-info", method="GET")
            if res and "data" in res and "otps" in res.get("data", {}):
                for item in res["data"]["otps"]:
                    item_num = re.sub(r'\D', '', str(item.get("number", "")))
                    if item_num == full_number or item_num.endswith(full_number[-8:]):
                        otp = item.get("otp") or item.get("code") or item.get("sms")
                        if otp:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"✅ **OTP / 2FA CODE RECEIVED!**\n\n📱 `+{number}`\n🔑 `{otp}`",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
        except:
            continue
    await context.bot.send_message(chat_id=chat_id, text=f"❌ Timeout! +{number} এর জন্য কোনো কোড আসেনি।")

# ================== অন্যান্য ফাংশন ==================
async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text="✅ ভেরিফাই সফল!", reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.answer("❗ চ্যানেলে জয়েন করুন!", show_alert=True)

    elif query.data.startswith("service_"):
        await query.message.delete()
        await show_ranges(query.message, query.data.split("_")[1])

    elif query.data.startswith("range_") or query.data.startswith("chgnum_"):
        # আগের নাম্বার অ্যালোকেশন কোড (একই রাখা হয়েছে)
        parts = query.data.split("_")
        if query.message.chat_id in active_otp_tasks:
            active_otp_tasks[query.message.chat_id].cancel()
        status_msg = await query.message.edit_text("⚡ নাম্বার খুঁজছি...")
        res = await call_website_api_async("getnum", method="POST", payload={"range": parts[2]})
        if res and res.get("meta", {}).get("status") == "ok":
            num = res["data"].get("full_number") or res["data"].get("number")
            c = get_country_details(num)
            btn = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{parts[1]}_{parts[2]}")]]
            await status_msg.edit_text(f"🚀 **NUMBER ALLOCATED**\n📍 {c['flag']} {c['name']}\n📱 `+{re.sub(r'\D', '', str(num))}`", 
                                     reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.MARKDOWN)
            active_otp_tasks[query.message.chat_id] = asyncio.create_task(check_otp(context, query.message.chat_id, num))
        else:
            await status_msg.edit_text("❌ Server Busy!")

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
    res = await call_website_api_async("liveaccess", method="GET")
    if not res:
        await msg.reply_text("❌ API Error")
        return
    # ... (আগের show_ranges কোড রাখুন)

async def text_handler(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await start(update, context)
        return

    text = update.message.text
    if "GET NUMBER" in text:
        await show_services(update.message)
    elif "2FA CODE" in text:
        await twofa_start(update, context)
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 Live OTP Channel", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Open", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))

# ================== CONVERSATION HANDLER ==================
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("2FA CODE"), twofa_start)],
    states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, twofa_number_received)]},
    fallbacks=[]
)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

if __name__ == "__main__":
    logging.info("🚀 SUPER FIRE OTP Bot Started Successfully!")
    app.run_polling()
