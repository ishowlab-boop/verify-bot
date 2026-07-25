import logging
from io import BytesIO
import os
import base64
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

CREDITS_FILE = "credits.json"

WAITING_PHOTO = 1
WAITING_SIGN = 2

logging.basicConfig(level=logging.INFO)

def load_credits():
    try:
        with open(CREDITS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_credits(data):
    with open(CREDITS_FILE, "w") as f:
        json.dump(data, f)

def get_credit(user_id):
    data = load_credits()
    return data.get(str(user_id), 0)

def add_credit(user_id, amount):
    data = load_credits()
    data[str(user_id)] = data.get(str(user_id), 0) + amount
    save_credits(data)

def use_credit(user_id):
    data = load_credits()
    uid = str(user_id)
    if data.get(uid, 0) > 0:
        data[uid] -= 1
        save_credits(data)
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✋ Finger Verify", callback_data="finger")],
        [InlineKeyboardButton("📄 Paper Verify", callback_data="paper")],
        [InlineKeyboardButton("🎤 Voice", callback_data="voice")],
        [InlineKeyboardButton("💰 My Credit", callback_data="credit")],
        [InlineKeyboardButton("🌐 Website", callback_data="website")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Welcome to Verify Bot\n\n"
        "নিচের বাটন থেকে বেছে নাও:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "finger":
        if get_credit(user_id) <= 0:
            await query.edit_message_text("❌ তোমার credit শেষ। Admin-কে বলো।")
            return ConversationHandler.END
        await query.edit_message_text(
            "✋ Finger Verify\n\n"
            "একটা পরিষ্কার ছবি পাঠাও।\n"
            "পরের ধাপে hand sign বেছে নিবে।"
        )
        return WAITING_PHOTO

    elif data == "paper":
        await query.edit_message_text("📄 Paper Verify\n\nশীঘ্রই আসছে...")
    
    elif data == "voice":
        await query.edit_message_text("🎤 Voice\n\nশীঘ্রই আসছে...")
    
    elif data == "credit":
        bal = get_credit(user_id)
        await query.edit_message_text(f"💰 তোমার Credit: {bal}")
    
    elif data == "website":
        await query.edit_message_text("🌐 Website\n\nশীঘ্রই আসছে...")

    return ConversationHandler.END

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if get_credit(user_id) <= 0:
        await update.message.reply_text("❌ Credit শেষ।")
        return ConversationHandler.END

    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id

    keyboard = [
        [InlineKeyboardButton("☝️ One Finger", callback_data="sign_one")],
        [InlineKeyboardButton("✌️ Two Fingers", callback_data="sign_two")],
        [InlineKeyboardButton("🤟 Three Fingers", callback_data="sign_three")],
        [InlineKeyboardButton("🖖 Four Fingers", callback_data="sign_four")],
        [InlineKeyboardButton("🖐️ Open Hand", callback_data="sign_open")],
        [InlineKeyboardButton("👍 Thumbs Up", callback_data="sign_thumbs")],
        [InlineKeyboardButton("👎 Thumbs Down", callback_data="sign_thumbsdown")],
        [InlineKeyboardButton("🤙 Call Me", callback_data="sign_call")],
        [InlineKeyboardButton("❤️ Finger Heart", callback_data="sign_heart")],
        [InlineKeyboardButton("🤞 Crossed Fingers", callback_data="sign_crossed")],
        [InlineKeyboardButton("🤚 Hand on Head", callback_data="sign_head")],
        [InlineKeyboardButton("✍️ Holding Pen", callback_data="sign_pen")],
        [InlineKeyboardButton("📝 Holding Paper", callback_data="sign_paper")],
        [InlineKeyboardButton("👁️ Hand on Eye", callback_data="sign_eye")],
        [InlineKeyboardButton("💋 Finger on Lips", callback_data="sign_lips")],
        [InlineKeyboardButton("🤏 Pinching", callback_data="sign_pinch")],
        [InlineKeyboardButton("🖕 Middle Finger", callback_data="sign_middle")],
        [InlineKeyboardButton("🤝 Handshake Pose", callback_data="sign_handshake")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hand sign বেছে নাও:",
        reply_markup=reply_markup
    )
    return WAITING_SIGN

async def process_sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    sign = query.data.replace("sign_", "")

    sign_map = {
        "one": "one finger pointing up",
        "two": "two fingers",
        "three": "three fingers",
        "four": "four fingers",
        "open": "open hand showing all five fingers",
        "thumbs": "thumbs up",
        "thumbsdown": "thumbs down",
        "call": "call me gesture",
        "heart": "finger heart",
        "crossed": "crossed fingers",
        "head": "hand on head",
        "pen": "holding a pen",
        "paper": "holding a white paper",
        "eye": "hand covering one eye",
        "lips": "finger on lips",
        "pinch": "pinching gesture",
        "middle": "middle finger",
        "handshake": "handshake pose"
    }
    caption = sign_map.get(sign, "three fingers")

    if not use_credit(user_id):
        await query.edit_message_text("❌ Credit শেষ।")
        return ConversationHandler.END

    await query.edit_message_text("⏳ Grok প্রসেসিং চলছে...")

    try:
        file = await context.bot.get_file(context.user_data["photo_id"])
        image_bytes = await file.download_as_bytearray()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{image_b64}"

        prompt = (
            f"Keep the exact same girl from the reference image. "
            f"Exact same face, eyes, nose, lips, hair, skin, body, clothes, background and lighting. "
            f"Do not change the identity at all. "
            f"Only change the hand pose to show: {caption}. "
            f"Natural realistic hand, correct fingers, photorealistic."
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}"
        }
        payload = {
            "model": "grok-imagine-image-quality",
            "prompt": prompt,
            "image": {"url": data_uri, "type": "image_url"}
        }

        response = requests.post(
            "https://api.x.ai/v1/images/edits",
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            add_credit(user_id, 1)
            await query.edit_message_text(f"❌ Error: {response.text}")
            return ConversationHandler.END

        result = response.json()
        image_url = result["data"][0]["url"]
        img_data = requests.get(image_url).content

        output_io = BytesIO(img_data)
        output_io.seek(0)

        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=output_io,
            caption=f"✅ Done!\nSign: {caption}\nRemaining Credit: {get_credit(user_id)}"
        )
        await query.delete_message()

    except Exception as e:
        add_credit(user_id, 1)
        await query.edit_message_text(f"❌ Error: {str(e)}")

    return ConversationHandler.END

async def addcredit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ শুধু Admin পারবে।")
        return

    try:
        args = context.args
        user_id = int(args[0])
        amount = int(args[1])
        add_credit(user_id, amount)
        await update.message.reply_text(f"✅ {user_id} কে {amount} credit দেওয়া হয়েছে।\nএখন আছে: {get_credit(user_id)}")
    except:
        await update.message.reply_text("Usage: /addcredit user_id amount")

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^finger$")],
        states={
            WAITING_PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            WAITING_SIGN: [CallbackQueryHandler(process_sign, pattern="^sign_")],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcredit", addcredit_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv)

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
