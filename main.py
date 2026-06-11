import logging
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import os

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Finger Verify Bot** চালু আছে!\n\n"
        "📸 ইমেজ পাঠাও + ক্যাপশনে প্রম্পট লিখো\n"
        "উদাহরণ:\n"
        "right hand showing three fingers, index middle ring finger up"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # প্রম্পট নেওয়া (ক্যাপশন)
        prompt = update.message.caption or "No prompt provided"
        print(f"Received Prompt: {prompt}")  # লগ দেখার জন্য
        
        # ইমেজ ডাউনলোড
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
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        text = "Verified"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_x = badge_x + (badge_size - (text_bbox[2] - text_bbox[0])) // 2
        text_y = badge_y - int(badge_size * 0.65)
        draw.text((text_x, text_y), text, fill="#1DA1F2", font=font)
        
        # সেভ
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        
        await update.message.reply_photo(
            photo=output,
            caption=f"✅ Verified!\n\n**প্রম্পট:** {prompt}\n\nএখনো শুধু Verified ব্যাজ লাগানো হয়েছে।\nপুরো AI ফিঙ্গার এডিট চাইলে বলো।"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Finger Verify Bot চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
