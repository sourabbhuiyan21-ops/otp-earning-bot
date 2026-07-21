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

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP")]
], resize_keyboard=True, is_persistent=True)

async def start(update: Update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]
        ]
        welcome_text = f"""
🌟 **SUPER FIRE OTP BOT** 🌟

👋 স্বাগতম **{user_name}**!

বটটি ব্যবহার করতে প্রথমে নিচের দুইটি চ্যানেলে জয়েন করুন এবং **ভেরিফাই** বাটনে ক্লিক করুন।
        """
        await update.message.reply_text(welcome_text.strip(), reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"""
🎉 **স্বাগতম {user_name}!** 

🌟 **SUPER FIRE OTP** - প্রিমিয়াম সার্ভিস
🔥 নিচ থেকে অপশন নির্বাচন করুন
        """, reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)

async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except:
        return False

# ================== CALLBACK HANDLER ==================
async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ **সফলভাবে ভেরিফাইড হয়েছে!**\n\nএখন আপনি বটের সকল সুবিধা ব্যবহার করতে পারবেন।",
                reply_markup=main_keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("❗ দয়া করে উভয় চ্যানেলে জয়েন করুন!", show_alert=True)

    # আপনার আগের range, service ইত্যাদি কোড এখানে রাখুন...

# ================== TEXT HANDLER ==================
async def text_handler(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await start(update, context)
        return

    text = update.message.text
    if "GET NUMBER" in text:
        await show_services(update.message)
    elif "2FA CODE" in text:
        await update.message.reply_text("🔐 **2FA CODE**\n\nএই সার্ভিসটি বর্তমানে আপডেটের কাজ চলছে।")
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 **Live OTP Section**", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Open Live OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))

# অন্যান্য ফাংশন (show_services, show_ranges, check_otp) আগের কোড থেকে রাখুন

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT, text_handler))

if __name__ == "__main__":
    logging.info("🚀 SUPER FIRE OTP Bot Started Successfully!")
    app.run_polling()
