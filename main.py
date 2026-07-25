import logging
from io import BytesIO
import os
import base64
import json
import requests
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
FREE_CREDIT_AFTER_JOIN = 1

WAITING_PHOTO = 1
WAITING_SIGN = 2
ADMIN_WAIT_ID = 3
ADMIN_WAIT_AMOUNT = 4

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
    return load_credits().get(str(user_id), 0)

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

async def is_joined(context, user_id):
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✋ Finger Verify"), KeyboardButton("📄 Paper Verify")],
        [KeyboardButton("🎤 Voice"), KeyboardButton("💰 My Credit")],
        [KeyboardButton("🌐 Website"), KeyboardButton("📞 Contact Admin")],
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
    user_id = update.effective_user.id
    add_user(user_id)

    if not await is_joined(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "🔒 Please join our channel first to use this bot.\n\nAfter joining, press the button below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if str(user_id) not in load_credits():
        add_credit(user_id, FREE_CREDIT_AFTER_JOIN)

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

    if text == "✋ Finger Verify":
        if get_credit(user_id) <= 0:
            await update.message.reply_text("❌ Credit finished.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=ADMIN_LINK)]]))
            return
        await update.message.reply_text(
            "✋ Finger Verify\n\nSend one clear photo now.\nPress Cancel to go back.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel")]], resize_keyboard=True)
        )
        return WAITING_PHOTO

    elif text == "📄 Paper Verify":
        await update.message.reply_text("📄 Paper Verify\n\nSend one clear photo of the girl now.\nNext you will choose the paper pose.")

    elif text == "🎤 Voice":
        await update.message.reply_text("🎤 Voice Feature", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Voice Channel", url=VOICE_LINK)]]))

    elif text == "💰 My Credit":
        await update.message.reply_text(f"💰 Your Credit: {get_credit(user_id)}")

    elif text == "🌐 Website":
        await update.message.reply_text("🌐 Our Website", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Website", url=WEBSITE_LINK)]]))

    elif text == "📞 Contact Admin":
        await update.message.reply_text("Contact Admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Message Admin", url=ADMIN_LINK)]]))

    elif text == "❌ Cancel":
        await update.message.reply_text("Cancelled.", reply_markup=main_keyboard())
        return ConversationHandler.END

    elif text == "Manage Credits" and user_id == OWNER_ID:
        await update.message.reply_text("Send User ID for credits:")
        return ADMIN_WAIT_ID

    elif text == "List Users" and user_id == OWNER_ID:
        users = load_users()
        if not users:
            await update.message.reply_text("No users yet.")
            return
        msg = "📊 User List (Last 30):\n\n"
        for uid in users[-30:]:
            msg += f"`{uid}`\n"
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "List Premium Users" and user_id == OWNER_ID:
        data = load_credits()
        premium = {k: v for k, v in data.items() if v > 0}
        if not premium:
            await update.message.reply_text("No premium users.")
            return
        msg = "⭐ Premium Users:\n\n"
        for uid, bal in premium.items():
            msg += f"ID: `{uid}` | Credit: {bal}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "Stats" and user_id == OWNER_ID:
        await update.message.reply_text(f"📊 Active Users: {len(load_users())}")

    elif text == "Broadcast" and user_id == OWNER_ID:
        await update.message.reply_text("Coming soon...")

    elif text == "Back to Menu":
        await update.message.reply_text("Main Menu", reply_markup=main_keyboard())

async def admin_receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(update.message.text)
        context.user_data["target_id"] = target_id
        await update.message.reply_text(f"User ID: {target_id}\n\nHow many credits to add?")
        return ADMIN_WAIT_AMOUNT
    except:
        await update.message.reply_text("Invalid ID. Send a valid number.")
        return ADMIN_WAIT_ID

async def admin_receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        target_id = context.user_data.get("target_id")
        add_credit(target_id, amount)
        await update.message.reply_text(
            f"✅ Added {amount} credits to {target_id}\nNew Balance: {get_credit(target_id)}",
            reply_markup=admin_keyboard()
        )
        return ConversationHandler.END
    except:
        await update.message.reply_text("Invalid amount. Send a number.")
        return ADMIN_WAIT_AMOUNT

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_join":
        if await is_joined(context, query.from_user.id):
            if str(query.from_user.id) not in load_credits():
                add_credit(query.from_user.id, FREE_CREDIT_AFTER_JOIN)
            await query.edit_message_text("✅ Verified! Press /start again.")
        else:
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
                [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
            ]
            await query.edit_message_text("❌ Still not joined.", reply_markup=InlineKeyboardMarkup(keyboard))

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["photo_id"] = update.message.photo[-1].file_id
    keyboard = [
        [InlineKeyboardButton("☝️ One Finger", callback_data="sign_one")],
        [InlineKeyboardButton("✌️ Two Fingers", callback_data="sign_two")],
        [InlineKeyboardButton("🤟 Three Fingers", callback_data="sign_three")],
        [InlineKeyboardButton("🖖 Four Fingers", callback_data="sign_four")],
        [InlineKeyboardButton("🖐️ Open Hand", callback_data="sign_open")],
        [InlineKeyboardButton("👍 Thumbs Up", callback_data="sign_thumbs")],
        [InlineKeyboardButton("🤚 Hand on Head", callback_data="sign_head")],
        [InlineKeyboardButton("✍️ Holding Pen", callback_data="sign_pen")],
        [InlineKeyboardButton("📝 Holding Paper", callback_data="sign_paper")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_sign")],
    ]
    await update.message.reply_text("Choose hand sign:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_SIGN

async def process_sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "cancel_sign":
        await query.edit_message_text("Cancelled.")
        await context.bot.send_message(query.message.chat_id, "Back to menu.", reply_markup=main_keyboard())
        return ConversationHandler.END

    sign_map = {
        "one": "one finger pointing up",
        "two": "two fingers",
        "three": "three fingers",
        "four": "four fingers",
        "open": "open hand",
        "thumbs": "thumbs up",
        "head": "hand on head",
        "pen": "holding a pen",
        "paper": "holding a white paper"
    }
    caption = sign_map.get(query.data.replace("sign_", ""), "three fingers")

    if not use_credit(user_id):
        await query.edit_message_text("❌ Credit finished.")
        return ConversationHandler.END

    await query.edit_message_text("⏳ Processing...")

    try:
        file = await context.bot.get_file(context.user_data["photo_id"])
        image_bytes = await file.download_as_bytearray()
        data_uri = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

        prompt = f"Keep the exact same girl, exact same face, hair, body, clothes, background. Only change the hand to show: {caption}. Photorealistic."

        response = requests.post(
            "https://api.x.ai/v1/images/edits",
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "grok-imagine-image-quality", "prompt": prompt, "image": {"url": data_uri, "type": "image_url"}},
            timeout=120
        )

        if response.status_code != 200:
            add_credit(user_id, 1)
            await query.edit_message_text(f"Error: {response.text}")
            return ConversationHandler.END

        img_url = response.json()["data"][0]["url"]
        img_data = requests.get(img_url).content
        await context.bot.send_photo(query.message.chat_id, photo=BytesIO(img_data), caption=f"✅ Done!\nRemaining: {get_credit(user_id)}")
        await context.bot.send_message(query.message.chat_id, "Menu:", reply_markup=main_keyboard())
        await query.delete_message()

    except Exception as e:
        add_credit(user_id, 1)
        await query.edit_message_text(f"Error: {e}")

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
            MessageHandler(filters.Regex("^Manage Credits$"), handle_message),
        ],
        states={
            WAITING_PHOTO: [MessageHandler(filters.PHOTO, receive_photo), MessageHandler(filters.Regex("^❌ Cancel$"), handle_message)],
            WAITING_SIGN: [CallbackQueryHandler(process_sign)],
            ADMIN_WAIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_id)],
            ADMIN_WAIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_amount)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), handle_message)],
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
