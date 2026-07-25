import logging
from io import BytesIO
import os
import base64
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not TOKEN:
    raise ValueError("BOT_TOKEN not set")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY not set")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bot Ready!\n\n"
        "ছবি পাঠাও + ক্যাপশনে লিখো কী চাও\n"
        "উদাহরণ: two fingers / three fingers / thumbs up"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        caption = update.message.caption or "three fingers"
        await update.message.reply_text("⏳ Grok প্রসেসিং চলছে...")

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        # base64 encode
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
            "image": {
                "url": data_uri,
                "type": "image_url"
            }
        }

        response = requests.post(
            "https://api.x.ai/v1/images/edits",
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            await update.message.reply_text(f"❌ Error: {response.text}")
            return

        result = response.json()
        image_url = result["data"][0]["url"]

        # download and send
        img_data = requests.get(image_url).content
        output_io = BytesIO(img_data)
        output_io.seek(0)

        await update.message.reply_photo(
            photo=output_io,
            caption=f"✅ Done\nPrompt: {caption}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
