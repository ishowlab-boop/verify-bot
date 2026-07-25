import logging
from io import BytesIO
import os
import requests
import replicate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image

TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN environment variable not set")

replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **AI Finger Bot** রেডি!\n\n"
        "ছবি পাঠাও + ক্যাপশনে লিখো কী হাত চাও\n"
        "উদাহরণ: two fingers / three fingers / thumbs up"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        caption = update.message.caption or "three fingers"
        await update.message.reply_text("⏳ প্রসেসিং চলছে...")

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        prompt = (
            f"Photorealistic photo of the exact same woman from the reference image. "
            f"Keep 100% identical face, eyes, nose, lips, hair, skin tone, body shape, clothes, background, lighting and camera angle. "
            f"Do not change the face or identity at all. "
            f"Only change the hand pose to: {caption}. "
            f"Natural realistic hand with correct number of fingers, perfect anatomy, seamless blend."
        )

        output = replicate_client.run(
            "black-forest-labs/flux-dev",
            input={
                "image": BytesIO(image_bytes),
                "prompt": prompt,
                "strength": 0.28,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_quality": 95
            }
        )

        edited_image = requests.get(output[0]).content
        img = Image.open(BytesIO(edited_image)).convert("RGB")

        output_io = BytesIO()
        img.save(output_io, format="PNG")
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
