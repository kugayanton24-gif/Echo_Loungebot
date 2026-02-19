import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8118144550:AAEeebM7QsUEESddnt2ohSyND4zEGjLgNxQ"  # Railway Variables -> TOKEN

# 1) Тексти кнопок (як на скріні)
BTN_MENU = "🍽 Меню/Menu"
BTN_LOYALTY = "⭐️ Система лояльності"
BTN_DEALS = "🤩 Акції"
BTN_PLACES = "🥂 Наші заклади"
BTN_EVENTS = "Події📸"
BTN_RULES = "Правила закладу"
BTN_CRASH = "Краш-лист"
BTN_CONTACTS = "📞 Контакти"
BTN_REVIEW = "⭐️ Залишити відгук"

# 2) Куди мають вести кнопки (встав свої URL)
LINKS = {
    BTN_MENU: "https://your-site.com/menu",
    BTN_LOYALTY: "https://your-site.com/loyalty",
    BTN_DEALS: "https://your-site.com/deals",
    BTN_PLACES: "https://your-site.com/places",
    BTN_EVENTS: "https://your-site.com/events",
    BTN_RULES: "https://your-site.com/rules",
    BTN_CRASH: "https://your-site.com/crush",
    BTN_CONTACTS: "https://your-site.com/contacts",
    BTN_REVIEW: "https://your-site.com/review",
}

def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_MENU), KeyboardButton(BTN_LOYALTY)],
        [KeyboardButton(BTN_DEALS), KeyboardButton(BTN_PLACES)],
        [KeyboardButton(BTN_EVENTS), KeyboardButton(BTN_RULES)],
        [KeyboardButton(BTN_CRASH), KeyboardButton(BTN_CONTACTS)],
        [KeyboardButton(BTN_REVIEW)],  # на всю ширину
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Обери пункт меню 👇",
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Головне меню",
        reply_markup=main_keyboard()
    )

async def on_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Якщо натиснули кнопку з нашого меню
    if text in LINKS:
        url = LINKS[text]
        inline = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Відкрити", url=url)]
        ])
        await update.message.reply_text(
            f"{text}\nНатисни кнопку нижче 👇",
            reply_markup=inline
        )
        return

    # Якщо написали щось інше
    await update.message.reply_text(
        "Обери пункт з меню нижче 👇",
        reply_markup=main_keyboard()
    )

def main():
    if not TOKEN:
        raise RuntimeError("TOKEN environment variable is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_menu_click))

    app.run_polling()

if __name__ == "__main__":
    main()
