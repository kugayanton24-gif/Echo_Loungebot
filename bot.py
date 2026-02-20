import os
import json
from datetime import datetime
import pytz

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import gspread
from google.oauth2.service_account import Credentials


# ================= ENV =================
TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

KYIV_TZ = pytz.timezone("Europe/Kyiv")


# ================= GOOGLE =================
def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    return sh.sheet1


def save_contact(user, phone):
    ws = get_sheet()

    now_kyiv = datetime.now(KYIV_TZ).strftime("%d.%m.%Y %H:%M:%S")

    ws.append_row([
        now_kyiv,
        user.first_name or "",
        user.last_name or "",
        phone,
        user.username or "",
        str(user.id)
    ])


# ================= KEYBOARDS =================

def contact_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📲 Поділитися контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def main_menu():
    keyboard = [
        ["🍽 Menu"],
        ["⭐️ Система Лояльності"],
        ["🎉 Події"],
        ["🥂 Наші заклади"],
        ["📞 Контакти"],
        ["⭐️ Залишити відгук"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Щоб продовжити, поділись своїм контактом 👇",
        reply_markup=contact_keyboard()
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    try:
        save_contact(user, contact.phone_number)
    except Exception as e:
        print("GOOGLE ERROR:", e)
        await update.message.reply_text("Помилка збереження контакту ❌")
        return

    await update.message.reply_text(
        "Ти частина Echo & Pool 🖤",
        reply_markup=main_menu()
    )


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🍽 Menu":
        await update.message.reply_text(
            "Переглянути меню 👇\nhttps://your-menu-link.com"
        )

    elif text == "⭐️ Система Лояльності":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Приєднатися", url="https://your-loyalty-link.com")]
        ])

        await update.message.reply_text(
            "Наша нова система лояльності - вже ДОСТУПНА!❤️\n\n"
            "І її не потрібно скачувати, бо вона буде прямо у вашому Apple Wallet або Google Pay🥵😎\n\n"
            "Зареєструвавшись - ви отримуєте кешбек 3% за кожний оплачений чек\n"
            "(чим частіше до нас ходите - тим більший відсоток)\n\n"
            "*натискай кнопочку система лояльності*",
            reply_markup=keyboard
        )

    elif text == "🎉 Події":
        await update.message.reply_text(
            "Актуальні події 👇\nhttps://your-events-link.com"
        )

    elif text == "🥂 Наші заклади":
        await update.message.reply_text(
            "Наші заклади 👇\nhttps://your-places-link.com"
        )

    elif text == "📞 Контакти":
        await update.message.reply_text(
            "Забронювати столик:\n+380 096 998 67 87"
        )

    elif text == "⭐️ Залишити відгук":
        await update.message.reply_text(
            "Залишити відгук 👇\nhttps://your-review-link.com"
        )


# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    app.run_polling()


if __name__ == "__main__":
    main()
