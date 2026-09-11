import os
import re
import asyncio
import yt_dlp

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# توکن ربات
# ==============================

BOT_TOKEN = "توکن_ربات_خودت_را_اینجا_بگذار"


# ==============================
# پوشه دانلود
# ==============================

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ==============================
# فقط YouTube
# ==============================

def is_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/"
    return re.match(pattern, url.strip(), re.IGNORECASE) is not None


# ==============================
# شروع ربات
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🎵 سلام!\n\n"
        "لینک موزیک YouTube را بفرست.\n"
        "من آن را دانلود می‌کنم و برایت می‌فرستم.\n\n"
        "فقط لینک‌های YouTube پشتیبانی می‌شوند."
    )

    await update.message.reply_text(text)


# ==============================
# دانلود موزیک
# ==============================

def download_music(url):

    options = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": os.path.join(
            DOWNLOAD_DIR,
            "%(title)s.%(ext)s"
        ),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        filename = ydl.prepare_filename(info)

    return filename, info


# ==============================
# دریافت لینک
# ==============================

async def receive_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    url = update.message.text.strip()

    # بررسی YouTube
    if not is_youtube_url(url):

        await update.message.reply_text(
            "❌ فقط لینک YouTube قابل قبول است."
        )

        return

    status = await update.message.reply_text(
        "⏳ در حال دریافت اطلاعات و دانلود موزیک..."
    )

    try:

        # دانلود در یک Thread جدا
        filename, info = await asyncio.to_thread(
            download_music,
            url
        )

        title = info.get(
            "title",
            "موزیک YouTube"
        )

        # اگر فایل وجود نداشت
        if not os.path.exists(filename):

            await status.edit_text(
                "❌ فایل دانلود شد اما پیدا نشد."
            )

            return

        await status.edit_text(
            "📤 دانلود شد؛ در حال ارسال به تلگرام..."
        )

        # ارسال فایل صوتی
        with open(filename, "rb") as audio:

            await update.message.reply_audio(
                audio=audio,
                title=title,
                caption="🎵 دانلود شده از YouTube"
            )

        await status.delete()

        # حذف فایل بعد از ارسال
        try:
            os.remove(filename)
        except Exception:
            pass

    except Exception as e:

        await status.edit_text(
            "❌ دانلود انجام نشد.\n\n"
            "خطا:\n"
            + str(e)[:3000]
        )


# ==============================
# خطاها
# ==============================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "ERROR:",
        context.error
    )


# ==============================
# اجرای ربات
# ==============================

def main():

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_link
        )
    )

    app.add_error_handler(
        error_handler
    )

    print("ربات روشن شد...")

    app.run_polling()


if __name__ == "__main__":
    main()
