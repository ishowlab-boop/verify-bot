import logging
from io import BytesIO
import os
import base64
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)

# ================== CONFIG ==================
TOKEN = os.getenv("BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CHANNEL_USERNAME = "PoseCore"
ADMIN_LINK = "https://t.me/AriyanInfo"
WEBSITE_LINK = "https://modelboxbd.com"
VOICE_LINK = "https://t.me/ariyanvoice"
CREDITS_FILE = "credits.json"
USERS_FILE = "users.json"
FREE_CREDIT_AFTER_JOIN = 1

WAITING_PHOTO = 1
WAITING_SIGN = 2

logging.basicConfig(level=logging.INFO)

# ================== CREDIT SYSTEM ==================
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

# ================== ACTIVE USERS ==================
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# ================== CHANNEL CHECK ==================
async def is_joined(context, user_id):
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Channel check error: {e}")
        return False

# ================== KEYBOARDS ==================
def main_keyboard():
    keyboard = [
        [KeyboardButton("✋ Finger Verify"), KeyboardButton("📄 Paper Verify")],
        [KeyboardButton("🎤 Voice"), KeyboardButton("💰 My Credit")],
        [KeyboardButton("🌐 Website"), KeyboardButton("📞 Contact Admin")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_keyboard():
    keyboard = [
        [KeyboardButton("Manage Credits"), KeyboardButton("List Users")],
        [KeyboardButton("Broadcast"), KeyboardButton("Stats")],
        [KeyboardButton("Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    if not await is_joined(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "🔒 Please join our channel first to use this bot.\n\n"
            "After joining, press the button below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    data = load_credits()
    if str(user_id) not in data:
        add_credit(user_id, FREE_CREDIT_AFTER_JOIN)

    await update.message.reply_text(
        "👋 Welcome to PoseCore Bot\n\n"
        "Choose an option from the menu below:",
        reply_markup=main_keyboard()
    )

# ================== ADMIN COMMAND ==================
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Only Admin can use this.")
        return
    await update.message.reply_text("🔐 Admin Panel", reply_markup=admin_keyboard())

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "✋ Finger Verify":
        if get_credit(user_id) <= 0:
            await update.message.reply_text(
                "❌ Your credit is finished.\nContact admin to buy more.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Contact Admin", url=ADMIN_LINK)]])
            )
            return ConversationHandler.END
        keyboard = [[KeyboardButton("❌ Cancel")]]
        await update.message.reply_text(
            "✋ Finger Verify\n\nSend one clear photo of the girl now.\nNext you will choose the hand sign.\n\nPress Cancel to go back.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return WAITING_PHOTO

    elif text == "📄 Paper Verify":
        await update.message.reply_text(
            "📄 Paper Verify\n\nSend one clear photo of the girl now.\nNext you will choose the paper pose."
        )

    elif text == "🎤 Voice":
        await update.message.reply_text(
            "🎤 Voice Feature\n\nGo to our voice channel:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Voice Channel", url=VOICE_LINK)]])
        )

    elif text == "💰 My Credit":
        bal = get_credit(user_id)
        await update.message.reply_text(f"💰 Your Credit: {bal}")

    elif text == "🌐 Website":
        await update.message.reply_text(
            "🌐 Our Website:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Website", url=WEBSITE_LINK)]])
        )

    elif text == "📞 Contact Admin":
        await update.message.reply_text(
            "Contact Admin:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Message Admin", url=ADMIN_LINK)]])
        )

    elif text == "❌ Cancel":
        await update.message.reply_text("Cancelled. Back to menu.", reply_markup=main_keyboard())
        return ConversationHandler.END

    elif text == "Manage Credits" and user_id == OWNER_ID:
        await update.message.reply_text("Send: /addcredit user_id amount\nExample: /addcredit 123456789 10")

    elif text == "List Users" and user_id == OWNER_ID:
        total = len(load_users())
        await update.message.reply_text(f"📊 Total Users: {total}")

    elif text == "Stats" and user_id == OWNER_ID:
        total = len(load_users())
        await update.message.reply_text(f"📊 Total Active Users: {total}")

    elif text == "Broadcast" and user_id == OWNER_ID:
        await update.message.reply_text("Broadcast feature coming soon...")

    elif text == "Back to Menu":
        await update.message.reply_text("Back to main menu.", reply_markup=main_keyboard())

# ================== CALLBACK ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "check_join":
        if await is_joined(context, user_id):
            if str(user_id) not in load_credits():
                add_credit(user_id, FREE_CREDIT_AFTER_JOIN)
            await query.edit_message_text("✅ Verified! You received free credit.\n\nNow press /start again.")
        else:
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
                [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
            ]
            await query.edit_message_text(
                "❌ You still haven't joined the channel.\n\nPlease join and press the button again.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

# ================== PHOTO + SIGN ==================
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if get_credit(user_id) <= 0:
        await update.message.reply_text("❌ Credit finished.", reply_markup=main_keyboard())
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
        [InlineKeyboardButton("🤝 Handshake", callback_data="sign_handshake")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_sign")],
    ]
    await update.message.reply_text("Choose the hand sign:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_SIGN

async def process_sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "cancel_sign":
        await query.edit_message_text("Cancelled.")
        await context.bot.send_message(chat_id=query.message.chat_id, text="Back to menu.", reply_markup=main_keyboard())
        return ConversationHandler.END

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
        await query.edit_message_text("❌ Credit finished.")
        return ConversationHandler.END

    await query.edit_message_text("⏳ Processing with Grok... Please wait.")

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
            f"Natural realistic hand, correct fingers, photorealistic, high quality."
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
        await context.bot.send_message(chat_id=query.message.chat_id, text="Back to menu.", reply_markup=main_keyboard())

    except Exception as e:
        add_credit(user_id, 1)
        await query.edit_message_text(f"❌ Error: {str(e)}")

    return ConversationHandler.END

# ================== ADD CREDIT ==================
async def addcredit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return
    try:
        args = context.args
        user_id = int(args[0])
        amount = int(args[1])
        add_credit(user_id, amount)
        await update.message.reply_text(f"✅ Added {amount} credit to {user_id}\nBalance: {get_credit(user_id)}")
    except:
        await update.message.reply_text("Usage: /addcredit user_id amount")

# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✋ Finger Verify$"), handle_message)],
        states={
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.Regex("^❌ Cancel$"), handle_message)
            ],
            WAITING_SIGN: [CallbackQueryHandler(process_sign, pattern="^(sign_|cancel_sign)")],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), handle_message)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("addcredit", addcredit_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
