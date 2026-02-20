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


# ================== BUTTON TEXTS (як на фото) ==================
BTN_MENU = "🍽 Меню/Menu"
BTN_LOYALTY = "⭐️ Система лояльності"
BTN_DEALS = "🤩 Акції"
BTN_PLACES = "🥂 Наші заклади"
BTN_EVENTS = "Події📸"
BTN_RULES = "Правила закладу"
BTN_CRASH = "Краш-лист"
BTN_CONTACTS = "📞 Контакти"
BTN_REVIEW = "⭐️ Залишити відгук"
BTN_BACK = "⬅️ Назад"

BTN_SHARE_CONTACT = "📲 Поділитися контактом"


# ================== LINKS (встав свої посилання) ==================
LINKS = {
    BTN_MENU: "https://poolclublounge.choiceqr.com/p/vOzk-xefF/section:menyu-echo/zakuski",
    BTN_LOYALTY: "https://www.instagram.com/echo.lounge.lviv/", "https://www.instagram.com/pool_club_lounge/",
    BTN_DEALS: "https://your-deals-link.com",
    BTN_EVENTS: "https://your-events-link.com",
    BTN_PLACES: "https://your-places-link.com",
    BTN_RULES: "https://your-rules-link.com",
    BTN_CRASH: "https://your-crash-link.com",
    BTN_REVIEW: "https://www.google.com/maps/place/Pool+Club+Lounge/@49.8098504,23.9702707,17z/data=!4m8!3m7!1s0x473ae7d3105fe31f:0x1fae4fb6b13f851e!8m2!3d49.8098504!4d23.9728456!9m1!1b1!16s%2Fg%2F11q25nwv1d?entry=ttu&g_ep=EgoyMDI2MDIxNy4wIKXMDSoASAFQAw%3D%3D",
}

BOOKING_PHONE = "+380 096 998 67 87"


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
    ws = sh.sheet1
    return ws


def ensure_header(ws):
    # якщо таблиця пуста — додати шапку
    values = ws.get_all_values()
    if not values:
        ws.append_row(
            [
                "datetime_ua",
                "first_name",
                "last_name",
                "phone_number",
                "username",
                "user_id",
            ]
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
    # 2 колонки як на фото + остання кнопка на всю ширину
    keyboard = [
        [KeyboardButton(BTN_MENU), KeyboardButton(BTN_LOYALTY)],
        [KeyboardButton(BTN_DEALS), KeyboardButton(BTN_PLACES)],
        [KeyboardButton(BTN_EVENTS), KeyboardButton(BTN_RULES)],
        [KeyboardButton(BTN_CRASH), KeyboardButton(BTN_CONTACTS)],
        [KeyboardButton(BTN_REVIEW)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def kb_back_only() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_BACK)]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def inline_open_button(url: str, title: str = "↗ Відкрити") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(title, url=url)]])


# ================== FLOW / STATE ==================
# Щоб людина не могла тиснути меню до того, як поділиться контактом:
async def require_contact_first(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return True

    # Ставимо прапорець у user_data після успішного збору контакту
    if update.message and update.message.chat_id:
        # context недоступний тут — перевірка робиться в handler-ах нижче
        pass
    return True


# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # скидаємо прапорець на новий старт
    context.user_data["contact_saved"] = False

    await update.message.reply_text(
        "Щоб продовжити — поділись контактом 👇",
        reply_markup=kb_request_contact(),
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    # захист: беремо тільки контакт цього ж користувача
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

    # Якщо контакт ще не зібраний — не даємо в меню, знову просимо контакт
    if not context.user_data.get("contact_saved", False):
        if text != "/start":
            await update.message.reply_text(
                "Спочатку поділись контактом 👇",
                reply_markup=kb_request_contact(),
            )
        return

    # Назад на головне меню
    if text == BTN_BACK:
        await update.message.reply_text("Головне меню", reply_markup=kb_main_menu())
        return

    # ---- MENU ITEMS ----

    # 🍽 Меню/Menu
    if text == BTN_MENU:
        url = LINKS[BTN_MENU]
        await update.message.reply_text(
            BTN_MENU,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # ⭐️ Система лояльності (з текстом + кнопка приєднатися)
    if text == BTN_LOYALTY:
        url = LINKS[BTN_LOYALTY]
        join_kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔥 Приєднатися", url=url)]]
        )

        await update.message.reply_text(
            "Наша нова система лояльності - вже ДОСТУПНА!❤️\n\n"
            "І її не потрібно скачувати, бо вона буде прямо у вашому Apple Wallet або Google Pay🥵😎\n\n"
            "Зареєструвавшись - ви отримуєте кешбек 3% за кожний оплачений чек "
            "(чим частіше до нас ходите - тим більший відсоток)\n\n"
            "*натискай кнопочку система лояльності*",
            parse_mode="Markdown",
            reply_markup=join_kb,
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # 🤩 Акції
    if text == BTN_DEALS:
        url = LINKS[BTN_DEALS]
        await update.message.reply_text(
            BTN_DEALS,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # 🎉 Події
    if text == BTN_EVENTS:
        url = LINKS[BTN_EVENTS]
        await update.message.reply_text(
            BTN_EVENTS,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # 🥂 Наші заклади
    if text == BTN_PLACES:
        url = LINKS[BTN_PLACES]
        await update.message.reply_text(
            BTN_PLACES,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Правила закладу
    if text == BTN_RULES:
        url = LINKS[BTN_RULES]
        await update.message.reply_text(
            BTN_RULES,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Краш-лист
    if text == BTN_CRASH:
        url = LINKS[BTN_CRASH]
        await update.message.reply_text(
            BTN_CRASH,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # 📞 Контакти (текст + назад)
    if text == BTN_CONTACTS:
        await update.message.reply_text(
            f"Забронювати столик:\n{BOOKING_PHONE}"
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # ⭐️ Залишити відгук
    if text == BTN_REVIEW:
        url = LINKS[BTN_REVIEW]
        await update.message.reply_text(
            BTN_REVIEW,
            reply_markup=inline_open_button(url),
        )
        await update.message.reply_text(" ", reply_markup=kb_back_only())
        return

    # Якщо написали щось інше
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
