import logging
from io import BytesIO
import os
import replicate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")  # এখানে তোমার কী বসাবে

replicate.Client(api_token=REPLICATE_API_TOKEN)

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
        "আমি AI দিয়ে ফিঙ্গার চেঞ্জ করে Verified করে দিবো 🔥"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        caption = update.message.caption or "three fingers"
        await update.message.reply_text("⏳ AI প্রসেসিং চলছে... (১৫-৩০ সেকেন্ড লাগতে পারে)")

        # ইমেজ ডাউনলোড
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        # FLUX Image-to-Image প্রম্পট
        prompt = f"A photorealistic image of the same girl, exact same face, hair, body, clothes, background and lighting. Only change the right hand to show {caption}. Hand clearly visible in foreground, natural pose, perfect skin tone, detailed fingers, seamless blend, high quality."

        output = replicate.run(
            "black-forest-labs/flux-dev",
            input={
                "image": BytesIO(image_bytes),
                "prompt": prompt,
                "strength": 0.75,      # কতটা চেঞ্জ করবে
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_quality": 90
            }
        )

        # আউটপুট ডাউনলোড
        edited_image = requests.get(output[0]).content

        # Verified ব্যাজ যোগ করা
        img = Image.open(BytesIO(edited_image)).convert("RGB")
        width, height = img.size
        draw = ImageDraw.Draw(img)

        badge_size = int(height * 0.22)
        badge_x = width - badge_size - 40
        badge_y = height - badge_size - 40

        draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill="#1DA1F2")
        tick = [(badge_x + badge_size*0.28, badge_y + badge_size*0.52),
                (badge_x + badge_size*0.48, badge_y + badge_size*0.78),
                (badge_x + badge_size*0.82, badge_y + badge_size*0.28)]
        draw.line(tick, fill="white", width=int(badge_size*0.13), joint="curve")

        text = "VERIFIED"
        try:
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_x = badge_x + (badge_size - (text_bbox[2] - text_bbox[0])) // 2
        text_y = badge_y - int(badge_size * 0.7)
        draw.text((text_x, text_y), text, fill="#1DA1F2", font=font)

        output_io = BytesIO()
        img.save(output_io, format="PNG", quality=95)
        output_io.seek(0)

        await update.message.reply_photo(
            photo=output_io,
            caption=f"✅ AI Finger Verified!\n**প্রম্পট:** {caption}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\nReplicate API টাকা শেষ হয়ে গেছে নাকি চেক করো।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 AI Finger Verify Bot চালু...")
    app.run_polling()

if __name__ == "__main__":
    main()
