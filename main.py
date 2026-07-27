import logging
from io import BytesIO
import os
import base64
import json
import time
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CHANNEL_USERNAME = "PoseCore"
ADMIN_LINK = "https://t.me/lindaariyan"
WEBSITE_LINK = "https://modelboxbd.com"
VOICE_LINK = "https://t.me/ariyanvoice"
CREDITS_FILE = "credits.json"
USERS_FILE = "users.json"
VALIDITY_FILE = "validity.json"
FREE_CREDIT_AFTER_JOIN = 1

WAITING_PHOTO = 1
WAITING_VIDEO = 2
ADMIN_WAIT_ID = 3
ADMIN_WAIT_AMOUNT = 4
ADMIN_WAIT_ACTION = 5
ADMIN_WAIT_VALIDITY = 6

logging.basicConfig(level=logging.INFO)

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def get_credit(user_id):
    return load_json(CREDITS_FILE).get(str(user_id), 0)

def add_credit(user_id, amount):
    data = load_json(CREDITS_FILE)
    data[str(user_id)] = max(0, data.get(str(user_id), 0) + amount)
    save_json(CREDITS_FILE, data)

def use_credit(user_id):
    data = load_json(CREDITS_FILE)
    uid = str(user_id)
    if data.get(uid, 0) > 0:
        data[uid] -= 1
        save_json(CREDITS_FILE, data)
        return True
    return False

def set_validity(user_id, days):
    data = load_json(VALIDITY_FILE)
    expire = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    data[str(user_id)] = expire
    save_json(VALIDITY_FILE, data)

def get_validity(user_id):
    return load_json(VALIDITY_FILE).get(str(user_id), "None")

def load_users():
    return load_json(USERS_FILE)

def add_user(user_id, username=None):
    users = load_users()
    users[str(user_id)] = username or "unknown"
    save_json(USERS_FILE, users)

async def is_joined(context, user_id):
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✋ Finger Verify"), KeyboardButton("📄 Paper Verify")],
        [KeyboardButton("🎥 Video Verify"), KeyboardButton("🎤 Voice")],
        [KeyboardButton("💰 My Credit"), KeyboardButton("🌐 Website")],
        [KeyboardButton("📞 Contact Admin")],
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Manage Credits")],
        [KeyboardButton("List Users")],
        [KeyboardButton("List Premium Users")],
        [KeyboardButton("Stats")],
        [KeyboardButton("Broadcast")],
        [KeyboardButton("Back to Menu")]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)

    if not await is_joined(context, user.id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "🔒 Please join our channel first to use this bot.\n\nAfter joining, press the button below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if str(user.id) not in load_json(CREDITS_FILE):
        add_credit(user.id, FREE_CREDIT_AFTER_JOIN)

    await update.message.reply_text(
        "👋 Welcome to PoseCore Bot\n\nChoose an option from the menu below:",
        reply_markup=main_keyboard()
    )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only Admin can use this.")
        return
    await update.message.reply_text("🔐 Admin Panel", reply_markup=admin_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    context.user_data.clear()

    if text == "✋ Finger Verify":
        if get_credit(user_id) <= 0:
            await update.message.reply_text("❌ Credit finished.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=ADMIN_LINK)]]))
            return
        await update.message.reply_text(
            "✋ Finger Verify\n\nSend one clear photo + caption (example: two fingers / nose touch)\nPress Cancel to go back.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel")]], resize_keyboard=True)
        )
        return WAITING_PHOTO

    elif text == "🎥 Video Verify":
        if get_credit(user_id) <= 0:
            await update.message.reply_text("❌ Credit finished.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=ADMIN_LINK)]]))
            return
        await update.message.reply_text(
            "🎥 Video Verify\n\nSend one clear photo + caption (what the girl should do/say)\nMax 12 seconds video.\nPress Cancel to go back.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel")]], resize_keyboard=True)
        )
        return WAITING_VIDEO

    elif text == "📄 Paper Verify":
        await update.message.reply_text("📄 Paper Verify\n\nSend one clear photo + caption.")

    elif text == "🎤 Voice":
        await update.message.reply_text("🎤 Voice Feature", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Voice Channel", url=VOICE_LINK)]]))

    elif text == "💰 My Credit":
        await update.message.reply_text(f"💰 Your Credit: {get_credit(user_id)}\nValidity: {get_validity(user_id)}")

    elif text == "🌐 Website":
        await update.message.reply_text("🌐 Our Website", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Website", url=WEBSITE_LINK)]]))

    elif text == "📞 Contact Admin":
        await update.message.reply_text("Contact Admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Message Admin", url=ADMIN_LINK)]]))

    elif text == "❌ Cancel":
        await update.message.reply_text("Cancelled.", reply_markup=main_keyboard())
        return ConversationHandler.END

    elif text == "Manage Credits" and user_id == OWNER_ID:
        users = load_users()
        credits = load_json(CREDITS_FILE)
        msg = "Send User ID for credits:\n\n"
        for uid, uname in list(users.items())[-15:]:
            bal = credits.get(uid, 0)
            msg += f"{uid} @{uname} credits={bal}\n"
        await update.message.reply_text(msg)
        return ADMIN_WAIT_ID

    elif text == "List Users" and user_id == OWNER_ID:
        users = load_users()
        credits = load_json(CREDITS_FILE)
        msg = "📊 User List:\n\n"
        for uid, uname in list(users.items())[-30:]:
            bal = credits.get(uid, 0)
            msg += f"{uid} @{uname} credits={bal}\n"
        await update.message.reply_text(msg)

    elif text == "List Premium Users" and user_id == OWNER_ID:
        users = load_users()
        credits = load_json(CREDITS_FILE)
        premium = {k: v for k, v in credits.items() if v > 0}
        if not premium:
            await update.message.reply_text("No premium users.")
            return
        msg = "⭐ Premium Users:\n\n"
        for uid, bal in premium.items():
            uname = users.get(uid, "unknown")
            msg += f"{uid} @{uname} credits={bal}\n"
        await update.message.reply_text(msg)

    elif text == "Stats" and user_id == OWNER_ID:
        await update.message.reply_text(f"📊 Active Users: {len(load_users())}")

    elif text == "Broadcast" and user_id == OWNER_ID:
        await update.message.reply_text("Coming soon...")

    elif text == "Back to Menu":
        await update.message.reply_text("Main Menu", reply_markup=main_keyboard())

async def admin_receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Invalid ID. Send only the number.")
        return ADMIN_WAIT_ID

    target_id = int(text)
    context.user_data["target_id"] = target_id
    keyboard = [
        [KeyboardButton("➕ Add Credits"), KeyboardButton("➖ Remove Credits")],
        [KeyboardButton("📅 Set Validity")],
        [KeyboardButton("🔙 Back")]
    ]
    await update.message.reply_text(
        f"User {target_id}\nChoose action:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ADMIN_WAIT_ACTION

async def admin_receive_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Back":
        await update.message.reply_text("Admin Panel", reply_markup=admin_keyboard())
        return ConversationHandler.END

    if "Validity" in text:
        await update.message.reply_text("How many days validity?")
        return ADMIN_WAIT_VALIDITY

    context.user_data["action"] = "add" if "Add" in text else "remove"
    await update.message.reply_text("How many credits?")
    return ADMIN_WAIT_AMOUNT

async def admin_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
        target_id = context.user_data.get("target_id")
        action = context.user_data.get("action")

        if action == "add":
            add_credit(target_id, amount)
            msg = f"✅ Added {amount} credits to {target_id}\nNew Balance: {get_credit(target_id)}"
        else:
            add_credit(target_id, -amount)
            msg = f"✅ Removed {amount} credits from {target_id}\nNew Balance: {get_credit(target_id)}"

        await update.message.reply_text(msg, reply_markup=admin_keyboard())
        return ConversationHandler.END
    except:
        await update.message.reply_text("Invalid amount.")
        return ADMIN_WAIT_AMOUNT

async def admin_receive_validity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        target_id = context.user_data.get("target_id")
        set_validity(target_id, days)
        await update.message.reply_text(
            f"✅ Set {days} days validity for {target_id}\nExpire: {get_validity(target_id)}",
            reply_markup=admin_keyboard()
        )
        return ConversationHandler.END
    except:
        await update.message.reply_text("Invalid days.")
        return ADMIN_WAIT_VALIDITY

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_join":
        if await is_joined(context, query.from_user.id):
            if str(query.from_user.id) not in load_json(CREDITS_FILE):
                add_credit(query.from_user.id, FREE_CREDIT_AFTER_JOIN)
            await query.edit_message_text("✅ Verified! Press /start again.")
        else:
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
                [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
            ]
            await query.edit_message_text("❌ Still not joined.", reply_markup=InlineKeyboardMarkup(keyboard))

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    caption = update.message.caption or "three fingers"

    if get_credit(user_id) <= 0:
        await update.message.reply_text("❌ Credit finished.", reply_markup=main_keyboard())
        return ConversationHandler.END

    if not use_credit(user_id):
        await update.message.reply_text("❌ Credit finished.", reply_markup=main_keyboard())
        return ConversationHandler.END

    await update.message.reply_text("⏳ Processing...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        data_uri = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

        prompt = (
            f"Keep the exact same girl from the reference image. "
            f"Exact same face, eyes, nose, lips, hair, skin, body, clothes, background and lighting. "
            f"Do not change the identity at all. "
            f"Only change the hand pose to: {caption}. "
            f"Natural realistic hand, correct fingers, photorealistic, high quality."
        )

        response = requests.post(
            "https://api.x.ai/v1/images/edits",
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "grok-imagine-image-quality", "prompt": prompt, "image": {"url": data_uri, "type": "image_url"}},
            timeout=120
        )

        if response.status_code != 200:
            add_credit(user_id, 1)
            await update.message.reply_text(f"Error: {response.text}", reply_markup=main_keyboard())
            return ConversationHandler.END

        img_url = response.json()["data"][0]["url"]
        img_data = requests.get(img_url).content
        await update.message.reply_photo(
            photo=BytesIO(img_data),
            caption=f"✅ Done!\nPrompt: {caption}\nRemaining: {get_credit(user_id)}"
        )
        await update.message.reply_text("Menu:", reply_markup=main_keyboard())

    except Exception as e:
        add_credit(user_id, 1)
        await update.message.reply_text(f"Error: {e}", reply_markup=main_keyboard())

    return ConversationHandler.END

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    caption = update.message.caption or "the girl is smiling and looking at the camera"

    if get_credit(user_id) <= 0:
        await update.message.reply_text("❌ Credit finished.", reply_markup=main_keyboard())
        return ConversationHandler.END

    if not use_credit(user_id):
        await update.message.reply_text("❌ Credit finished.", reply_markup=main_keyboard())
        return ConversationHandler.END

    status_msg = await update.message.reply_text("⏳ Generating video (max 12s)... Please wait. This may take 1-3 minutes.")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        data_uri = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

        prompt = (
            f"Keep the exact same girl from the reference image. "
            f"Exact same face, hair, body, clothes and background. "
            f"Animate naturally: {caption}. "
            f"Photorealistic, smooth natural movement, high quality."
        )

        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }

        # Start video generation
        response = requests.post(
            "https://api.x.ai/v1/videos/generations",
            headers=headers,
            json={
                "model": "grok-imagine-video-1.5",
                "prompt": prompt,
                "image": {"url": data_uri},
                "duration": 12,
                "resolution": "720p"
            },
            timeout=30
        )

        if response.status_code != 200:
            add_credit(user_id, 1)
            await status_msg.edit_text(f"❌ Error starting video: {response.text}")
            await update.message.reply_text("Menu:", reply_markup=main_keyboard())
            return ConversationHandler.END

        request_id = response.json().get("request_id")
        if not request_id:
            add_credit(user_id, 1)
            await status_msg.edit_text("❌ No request_id received.")
            await update.message.reply_text("Menu:", reply_markup=main_keyboard())
            return ConversationHandler.END

        # Poll for completion
        video_url = None
        for _ in range(60):  # max ~5 minutes
            time.sleep(5)
            poll = requests.get(
                f"https://api.x.ai/v1/videos/{request_id}",
                headers={"Authorization": f"Bearer {XAI_API_KEY}"},
                timeout=30
            )
            data = poll.json()
            status = data.get("status")

            if status == "done":
                video_url = data.get("video", {}).get("url") or data.get("url")
                break
            elif status in ["failed", "expired"]:
                add_credit(user_id, 1)
                await status_msg.edit_text(f"❌ Video generation failed: {data}")
                await update.message.reply_text("Menu:", reply_markup=main_keyboard())
                return ConversationHandler.END

        if not video_url:
            add_credit(user_id, 1)
            await status_msg.edit_text("❌ Timeout. Video not ready.")
            await update.message.reply_text("Menu:", reply_markup=main_keyboard())
            return ConversationHandler.END

        # Download and send video
        video_data = requests.get(video_url, timeout=60).content
        await update.message.reply_video(
            video=BytesIO(video_data),
            caption=f"✅ Video Ready!\nPrompt: {caption}\nRemaining Credit: {get_credit(user_id)}",
            supports_streaming=True
        )
        await status_msg.delete()
        await update.message.reply_text("Menu:", reply_markup=main_keyboard())

    except Exception as e:
        add_credit(user_id, 1)
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=main_keyboard())

    return ConversationHandler.END

async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("admin", "Admin Panel"),
    ])

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✋ Finger Verify$"), handle_message),
            MessageHandler(filters.Regex("^🎥 Video Verify$"), handle_message),
            MessageHandler(filters.Regex("^Manage Credits$"), handle_message),
        ],
        states={
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.Regex("^❌ Cancel$"), handle_message)
            ],
            WAITING_VIDEO: [
                MessageHandler(filters.PHOTO, receive_video),
                MessageHandler(filters.Regex("^❌ Cancel$"), handle_message)
            ],
            ADMIN_WAIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_id)],
            ADMIN_WAIT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_action)],
            ADMIN_WAIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_amount)],
            ADMIN_WAIT_VALIDITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_validity)],
        },
        fallbacks=[MessageHandler(filters.TEXT, handle_message)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
