import logging
from io import BytesIO
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")

# এখানে তোমার AI API কী বসাবে (Replicate / Grok / Flux)
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")   # পরে যোগ করবো

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Finger Verify Bot** রেডি!\n\n"
        "কীভাবে ব্যবহার করবে:\n"
        "• একটা ছবি পাঠাও\n"
        "• ক্যাপশনে লিখো: `three fingers`, `thumbs up`, `call me`, `rose holding` ইত্যাদি\n\n"
        "আমি AI দিয়ে ফিঙ্গার এড করে Verified করে দিবো।"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prompt = update.message.caption or "three fingers"
        user = update.effective_user.first_name
        
        await update.message.reply_text("⏳ প্রসেসিং হচ্ছে... ফিঙ্গার এড করা হচ্ছে।")

        # ইমেজ ডাউনলোড
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        # এখানে AI Image Edit API কল করা হবে (আপাতত Verified ব্যাজ দিয়ে দিলাম)
        # পরে Replicate Flux দিয়ে আপগ্রেড করবো
        
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # Verified Badge
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

        output = BytesIO()
        img.save(output, format="PNG", quality=95)
        output.seek(0)

        await update.message.reply_photo(
            photo=output,
            caption=f"✅ **Finger Verified**\n\n**প্রম্পট:** {prompt}\n**ইউজার:** {user}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
