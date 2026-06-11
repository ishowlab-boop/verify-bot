import logging
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import os

TOKEN = os.getenv("BOT_TOKEN")  # Set this in Render / Railway Environment Variables

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Verify Bot!\n\n"
        "📸 যেকোনো ছবি পাঠাও, আমি Verified ব্যাজ লাগিয়ে দিবো।\n"
        "🔢 অথবা /gesture লিখে হ্যান্ড জেসচার মেনু দেখো"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = img.size
        
        draw = ImageDraw.Draw(img)
        
        # Verified Badge
        badge_size = int(height * 0.18)
        badge_x = width - badge_size - 30
        badge_y = height - badge_size - 30
        
        draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill="#1DA1F2")
        
        # White Tick
        tick = [
            (badge_x + badge_size*0.25, badge_y + badge_size*0.5),
            (badge_x + badge_size*0.45, badge_y + badge_size*0.75),
            (badge_x + badge_size*0.8, badge_y + badge_size*0.25)
        ]
        draw.line(tick, fill="white", width=int(badge_size*0.12), joint="curve")
        
        # Verified Text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(badge_size*0.35))
        except:
            font = ImageFont.load_default()
        
        text = "Verified"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_x = badge_x + (badge_size - (text_bbox[2] - text_bbox[0])) // 2
        text_y = badge_y - int(badge_size * 0.65)
        draw.text((text_x, text_y), text, fill="#1DA1F2", font=font)
        
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        
        await update.message.reply_photo(
            photo=output,
            caption="✅ Verified করে দিলাম!"
        )
        
    except Exception as e:
        await update.message.reply_text("❌ Error: " + str(e))

async def gesture_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤚 হ্যান্ড জেসচার মেনু:\n\n"
        "1️⃣ /one\n"
        "2️⃣ /two\n"
        "3️⃣ /three\n"
        "4️⃣ /four\n"
        "5️⃣ /five\n"
        "👍 /thumbsup\n"
        "👎 /thumbsdown\n"
        "🤙 /callme\n"
        "🤞 /crossed\n"
        "🫰 /heart\n\n"
        "ছবি পাঠিয়ে পরে gesture চয়ন করো (আপাতত বেসিক)"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gesture", gesture_menu))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
