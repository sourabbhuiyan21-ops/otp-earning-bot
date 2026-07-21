import logging
import re
import os
import httpx
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

# ================== CREDENTIALS ==================
TOKEN = "8870078495:AAESL6GUbWfuR_OwUD6Pi7cdlgNBc3NiF2Y"
API_KEY = "MURAD_12B9CA6C873901539718ACB1"
OWNER_ID = 6381033891
# ================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

UPDATE_CHANNEL = "@META_FIRE_UPDATE"
OTP_CHANNEL = "@META_FIRE_OTP"

active_otp_tasks = {}
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

# ====================== PROFESSIONAL KEYBOARDS ======================
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("📡 LIVE OTP"), KeyboardButton("❓ Help")]
], resize_keyboard=True, is_persistent=True)

async def start(update: Update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("📢 OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verify Subscription", callback_data="verify")]
        ]
        welcome_text = f"""
🌟 **WELCOME TO SUPER FIRE OTP** 🌟

👋 Hello **{user_name}**!

এই বটটি দিয়ে দ্রুত এবং নির্ভরযোগ্য ভাবে OTP পেতে পারবেন।

**ব্যবহার করার আগে:**
✅ Update Channel-এ জয়েন করুন
✅ OTP Channel-এ জয়েন করুন
✅ Verify বাটনে ক্লিক করুন
        """
        await update.message.reply_text(welcome_text.strip(), reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    else:
        welcome_text = f"""
🎉 **স্বাগতম {user_name}!** 🎉

🌟 **SUPER FIRE OTP** - আপনার বিশ্বস্ত OTP সার্ভিস

🔥 **এখন আপনি সম্পূর্ণ প্রস্তুত!**
নিচ থেকে আপনার পছন্দের সার্ভিস নির্বাচন করুন।
        """
        await update.message.reply_text(welcome_text.strip(), reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)

async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except:
        return False

# ================== REST OF THE CODE (সুন্দর করে রাখা হয়েছে) ==================
async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.message.chat_id, 
                text="✅ **সফলভাবে ভেরিফাইড!**\n\nএখন আপনি পুরোপুরি বট ব্যবহার করতে পারবেন।",
                reply_markup=main_keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("❗ আপনি এখনো উভয় চ্যানেলে জয়েন করেননি!", show_alert=True)

    # Previous callback functions (range, service etc.) remain same...
    elif query.data.startswith("range_") or query.data.startswith("chgnum_"):
        # ... (আগের কোড এখানে রাখুন)
        pass  # আপনার আগের কোডের এই অংশটুকু এখানে রাখবেন

    elif query.data == "back_to_services":
        await query.message.delete()
        await show_services(query.message)
    elif query.data.startswith("service_"):
        await query.message.delete()
        await show_ranges(query.message, query.data.split("_")[1])

async def show_services(msg):
    kb = [
        [InlineKeyboardButton("🔷 FACEBOOK 🔷", callback_data="service_facebook")],
        [InlineKeyboardButton("📸 INSTAGRAM 📸", callback_data="service_instagram")]
    ]
    text = "🌐 **Select Platform**\n\nকোন প্ল্যাটফর্মের জন্য নাম্বার নিতে চান?"
    await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

async def show_ranges(msg, service):
    # আগের কোড অনুযায়ী রাখুন...
    pass

# Help Command
async def help_command(update: Update, context):
    help_text = """
🆘 **SUPER FIRE OTP - Help Center**

🔥 /start - বট রিস্টার্ট করুন
📱 GET NUMBER - নতুন নাম্বার নিন
📡 LIVE OTP - লাইভ ওটিপি চ্যানেল দেখুন

**সাপোর্ট:** @META_FIRE_UPDATE
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def text_handler(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await start(update, context)
        return

    text = update.message.text
    if "GET NUMBER" in text:
        await show_services(update.message)
    elif "LIVE OTP" in text:
        await update.message.reply_text(
            "📡 **Live OTP Channel**", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Open Live OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]])
        )
    elif "Help" in text or "help" in text.lower():
        await help_command(update, context)

# ====================== MAIN ======================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT, text_handler))

if __name__ == "__main__":
    logging.info("🚀 SUPER FIRE OTP Bot Started Successfully!")
    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()
