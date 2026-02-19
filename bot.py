import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8118144550:AAEeebM7QsUEESddnt2ohSyND4zEGjLgNxQ"  # Краще брати з Railway environment variables

MENU_URL = "https://poolclublounge.choiceqr.com/p/vOzk-xefF/section:menyu?fbclid=PAAaYRsBQQZMON_RdkYRs5zoWbEBz0YXs88XB17YoJ29zR1AgLJ_ZSY_wxJzA_aem_AXhqg6zQUCinofq5vdkNOkXL-rHwKWCQ9fXvEzfMJb2gcaLGGWlA97L8jYx3250KViw&utm_source=ig&utm_medium=social&utm_content=link_in_bio"  # ← сюди вставляєте ваше посилання

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Меню", url=MENU_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привіт! Обери дію 👇",
        reply_markup=reply_markup
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ти написав(ла): {update.message.text}")

def main():
    if not TOKEN:
        raise RuntimeError("TOKEN environment variable is not set")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == "__main__":
    main()

