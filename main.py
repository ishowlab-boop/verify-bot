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
        "👋 **AI Finger Verify Bot** রেডি!\n\n"
        "কীভাবে ব্যবহার করবে:\n"
        "1. একটা ছবি পাঠাও\n"
        "2. ক্যাপশনে লিখো:\n"
        "   • three fingers\n"
        "   • two fingers\n"
        "   • thumbs up\n"
        "   • call me\n"
        "   • finger heart\n"
        "   • hand on head\n"
        "   • rose holding\n\n"
        "আমি AI দিয়ে শুধু হাত বদলে দিবো, মুখ একদম একই থাকবে।"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        caption = update.message.caption or "three fingers"
        await update.message.reply_text("⏳ AI প্রসেসিং চলছে... (১৫-৩০ সেকেন্ড লাগতে পারে)")

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        prompt = (
            f"Keep the exact same girl, exact same face, exact same eyes, nose, lips, hair, skin, body, clothes, background and lighting. "
            f"Do not change the face at all. Only change the right hand pose to show {caption}. "
            f"Natural realistic hand, detailed fingers, perfect skin tone, seamless blend, photorealistic, high quality."
        )

        output = replicate_client.run(
            "black-forest-labs/flux-dev",
            input={
                "image": BytesIO(image_bytes),
                "prompt": prompt,
                "strength": 0.40,
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
            caption=f"✅ Done!\n**প্রম্পট:** {caption}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 AI Finger Verify Bot চালু...")
    app.run_polling()

if __name__ == "__main__":
    main()
