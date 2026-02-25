import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

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


# ================== ENV ==================
TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

UA_TZ = ZoneInfo("Europe/Kyiv")


# ================== BUTTON TEXTS ==================
BTN_MENU = "🍽 Меню/Menu"
BTN_LOYALTY = "💳 Система лояльності"
BTN_DELIVERY = "🚗 Доставка"
BTN_PLACES = "📍 Наші заклади"
BTN_EVENTS = "✨ Події"
BTN_CONTACTS = "📞 Контакти"
BTN_REVIEW = "⭐️ Залишити відгук"
BTN_BACK = "⬅️ Назад"

BTN_SHARE_CONTACT = "📲 Поділитися контактом"


# ================== LINKS (встав/онови свої) ==================
LINKS = {
    BTN_MENU: "https://poolclublounge.choiceqr.com/p/vOzk-xefF/section:menyu-echo/zakuski",
    BTN_LOYALTY: "https://www.instagram.com/echo.lounge.lviv/",         # заміниш на лінк лояльності (wallet/google pay)
    BTN_DELIVERY: "https://poolclublounge.choiceqr.com/delivery/section:menyu-echo",                     # <-- встав лінк доставки
    BTN_EVENTS: "https://www.instagram.com/echo.lounge.lviv/",                         # <-- встав лінк подій
    BTN_REVIEW: "https://www.google.com/maps/place/Pool+Club+Lounge/@49.8098504,23.9702707,17z/data=!4m8!3m7!1s0x473ae7d3105fe31f:0x1fae4fb6b13f851e!8m2!3d49.8098504!4d23.9728456!9m1!1b1!16s%2Fg%2F11q25nwv1d?entry=ttu",
}

BOOKING_PHONE = "+380 096 998 67 87"


# ================== TEXTS ==================
TEXT_LOYALTY = (
    "Ставайте частиною закритого клубу Echo 🤍\n\n"
    "📍Після активації ви отримуєте:\n"
    "— 3% кешбек з кожного чеку, який збільшується з кожним наступним візитом\n"
    "— Персональні пропозиції\n"
    "— Доступ до закритих подій та спеціальних форматів\n\n"
    "Карта лояльності автоматично додається в Apple Wallet або Google Pay — без додаткових застосунків.\n\n"
    "Натисніть «Приєднатися», щоб активувати карту"
)

TEXT_DELIVERY = (
    "Замовляйте будь-які позиції з нашого меню з доставкою по місту! 🤍\n\n"
    "Улюблені страви та перевірені смаки — тепер у вас вдома.\n"
    "Готуємо після підтвердження замовлення.\n\n"
    "📍Обов’язково спробуйте нашу фірмову Левову Паляницю.\n\n"
    "Оформити замовлення можна за кнопкою нижче ⬇️"

TEXT_PLACES = (
     "Усі формати — в одному просторі.\n"
    "Обирайте атмосферу під настрій!\n\n"
    "🍸 Echo Lounge\n"
    "• вул. Щирецька 36/15\n"
    "• 12:00 – 23:00\n"
    "Lounge-ресторан: кухня, бар, кальяни та події.\n\n"
    "🎱 Pool Club Lounge\n"
    "• вул. Щирецька 36/15\n"
    "• 10:00 – 23:00\n"
    "Більярд, бар і комфортна зона для відпочинку.\n\n"
    "🏸 Squashfit Center\n"
    "• вул. Щирецька 36/15\n"
    "• 10:00 – 23:00\n"
    "Сквош-корти та простір для активного відпочинку.\n\n"
    "🥗 Smachno In\n"
    "• ТВК «Південний» — Продуктовий ринок\n"
    "• 10:00 – 19:00\n"
    "Свіжі страви для швидкого обіду або перекусу 🤍"
)

TEXT_EVENTS = (
   "21 березня - офіційне відкриття Echo Lounge!\n\n"
    "📍На вас чекає вечір з живим виступом, DJ та особливою атмосферою.\n"
    "Це більше, ніж просто відкриття — це старт нового простору у Львові.\n\n"
    "Деталі програми з’являться зовсім скоро 🤫\n\n"
    "Побачимось 21.03 🤍"

TEXT_CONTACTS = (
    "Забронювати столик:\n"
    "+380 096 998 67 87"
)

TEXT_REVIEW = "Ваша думка дуже важлива для нас 🤍"


# ================== GOOGLE SHEETS ==================
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
    return sh.sheet1


def ensure_header(ws):
    values = ws.get_all_values()
    if not values:
        ws.append_row(
            ["datetime_ua", "first_name", "last_name", "phone_number", "username", "user_id"]
        )


def save_contact_to_sheet(user, phone_number: str):
    ws = get_sheet()
    ensure_header(ws)
    dt_ua = datetime.now(UA_TZ).strftime("%d.%m.%Y %H:%M:%S")
    ws.append_row(
        [
            dt_ua,
            user.first_name or "",
            user.last_name or "",
            phone_number or "",
            user.username or "",
            str(user.id),
        ]
    )


# ================== KEYBOARDS ==================
def kb_request_contact() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def kb_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_MENU), KeyboardButton(BTN_LOYALTY)],
        [KeyboardButton(BTN_DELIVERY), KeyboardButton(BTN_PLACES)],
        [KeyboardButton(BTN_EVENTS), KeyboardButton(BTN_CONTACTS)],
        [KeyboardButton(BTN_REVIEW)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def kb_back_only() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_BACK)]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def inline_button(title: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(title, url=url)]])


# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact_saved"] = False
    await update.message.reply_text(
        "Щоб продовжити — поділись контактом 👇",
        reply_markup=kb_request_contact(),
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    # беремо тільки контакт цього користувача
    if contact.user_id and contact.user_id != user.id:
        await update.message.reply_text(
            "Надішли, будь ласка, *свій* контакт через кнопку 👇",
            reply_markup=kb_request_contact(),
            parse_mode="Markdown",
        )
        return

    try:
        save_contact_to_sheet(user, contact.phone_number)
        context.user_data["contact_saved"] = True
    except Exception as e:
        print("GOOGLE SHEETS ERROR:", repr(e))
        await update.message.reply_text(
            "❌ Не вдалось зберегти контакт в таблицю.\n"
            "Перевір доступ Service Account до Google Sheet та SHEET_ID."
        )
        return

    await update.message.reply_text("Ти частина Echo & Pool 🖤", reply_markup=kb_main_menu())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # якщо контакт не зібраний — просимо контакт
    if not context.user_data.get("contact_saved", False):
        await update.message.reply_text(
            "Спочатку поділись контактом 👇",
            reply_markup=kb_request_contact(),
        )
        return

    # назад
    if text == BTN_BACK:
        await update.message.reply_text("Головне меню", reply_markup=kb_main_menu())
        return

    # ---- ПУНКТИ МЕНЮ ----

    # Меню
    if text == BTN_MENU:
        url = LINKS[BTN_MENU]
        await update.message.reply_text(
            BTN_MENU,
            reply_markup=inline_button("↗ Відкрити меню", url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Система лояльності
    if text == BTN_LOYALTY:
        url = LINKS[BTN_LOYALTY]
        await update.message.reply_text(
            TEXT_LOYALTY,
            reply_markup=inline_button("💳 Приєднатися", url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Доставка
    if text == BTN_DELIVERY:
        url = LINKS[BTN_DELIVERY]
        await update.message.reply_text(
            TEXT_DELIVERY,
            reply_markup=inline_button("🚗 Замовити доставку", url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Наші заклади (без посилання — тільки текст + назад)
    if text == BTN_PLACES:
        await update.message.reply_text(TEXT_PLACES)
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Події
    if text == BTN_EVENTS:
        url = LINKS[BTN_EVENTS]
        await update.message.reply_text(
            TEXT_EVENTS,
            reply_markup=inline_button("📅 Переглянути події", url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Контакти
    if text == BTN_CONTACTS:
        await update.message.reply_text(TEXT_CONTACTS)
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Відгук
    if text == BTN_REVIEW:
        url = LINKS[BTN_REVIEW]
        await update.message.reply_text(
            TEXT_REVIEW,
            reply_markup=inline_button("⭐️ Стань частиною історії", url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # якщо щось інше
    await update.message.reply_text("Обери пункт меню 👇", reply_markup=kb_main_menu())


def main():
    if not TOKEN:
        raise RuntimeError("TOKEN environment variable is not set")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()


if __name__ == "__main__":
    main()
