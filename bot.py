import os
import json
from datetime import datetime, timezone

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
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


# ====== ENV ======
TOKEN = "8118144550:AAEeebM7QsUEESddnt2ohSyND4zEGjLgNxQ"
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# ====== BUTTONS ======
BTN_CONTACTS = "📞 Контакти"
BTN_MENU = "🍽 Меню/Menu"
BTN_REVIEW = "⭐️ Залишити відгук"

def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_MENU), KeyboardButton(BTN_CONTACTS)],
        [KeyboardButton(BTN_REVIEW)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def contact_request_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("✅ Поділитися контактом", request_contact=True)],
        [KeyboardButton("⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# ====== GOOGLE SHEETS CLIENT ======
def get_sheet():
    if not GOOGLE_CREDS_JSON:
        raise RuntimeError("GOOGLE_CREDS_JSON is not set")
    if not SHEET_ID:
        raise RuntimeError("SHEET_ID is not set")

    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(SHEET_ID)
    ws = sh.sheet1  # перший лист
    return ws

def ensure_header(ws):
    # Якщо таблиця пуста — додамо шапку
    values = ws.get_all_values()
    if not values:
        ws.append_row([
            "timestamp_utc",
            "user_id",
            "username",
            "first_name",
            "last_name",
            "phone_number",
        ])

# ====== HANDLERS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Головне меню", reply_markup=main_keyboard())

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text == BTN_CONTACTS:
        await update.message.reply_text(
            "Натисни кнопку нижче, щоб поділитися номером (запишемо в нашу базу для зв’язку).",
            reply_markup=contact_request_keyboard(),
        )
        return

    if text == "⬅️ Назад":
        await update.message.reply_text("Головне меню", reply_markup=main_keyboard())
        return

    await update.message.reply_text("Обери пункт меню 👇", reply_markup=main_keyboard())

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.message.contact
    u = update.effective_user

    # Додатковий захист: контакт має належати цьому ж користувачу
    # (Telegram зазвичай так і надсилає при request_contact=True)
    if c.user_id and c.user_id != u.id:
        await update.message.reply_text("Будь ласка, надішли свій контакт через кнопку нижче.")
        return

    ws = get_sheet()
    ensure_header(ws)

    now_utc = datetime.now(timezone.utc).isoformat()

    ws.append_row([
        now_utc,
        str(u.id),
        u.username or "",
        u.first_name or "",
        u.last_name or "",
        c.phone_number or "",
    ])

    await update.message.reply_text("✅ Дякую! Контакт збережено.", reply_markup=main_keyboard())

def main():
    if not TOKEN:
        raise RuntimeError("TOKEN environment variable is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    app.run_polling()

if __name__ == "__main__":
    main()
