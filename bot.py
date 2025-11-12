# bot.py
import os
import logging
import asyncio
from typing import Any
import telegram
print("TELEGRAM BOT VERSION:", telegram.__version__)

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

from database import Database

# --------------------------------------------------------------------------- #
# Настройки
# --------------------------------------------------------------------------- #
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "7819916914:AAHuOv_6eph7IZ2OYyqq-zKz22yr_G4MIPk")
ADMIN_ID = 445570258

# Состояния диалога заказа
ORDER_NAME, ORDER_PHONE, ORDER_EMAIL = range(3)

db = Database()

# --------------------------------------------------------------------------- #
# Тексты и клавиатуры
# --------------------------------------------------------------------------- #
BIKE_DESCRIPTIONS = {
    "PRIMO": (
        "Маневренная, универсальная модель для активного фанового катания в холмистой местности.\n"
        "Велосипед базового уровня в нашей линейке, для зрелых любителей качества и современных тенденции велостроения. "
        "Розничная цена 50 000 руб."
    ),
    "TERZO": (
        "Спортивная модель для профессионального использования.\n"
        "Идеальный выбор для соревнований и тренировок. Премиальное качество сборки. "
        "Розничная цена 75 000 руб."
    ),
    "ULTIMO": (
        "Флагманская модель с инновационными технологиями.\n"
        "Максимальная производительность и комфорт. Для самых требовательных велосипедистов. "
        "Розничная цена 120 000 руб."
    ),
    "TESORO": (
        "Городской велосипед с элегантным дизайном.\n"
        "Идеален для повседневного использования и прогулок по городу. Стиль и практичность. "
        "Розничная цена 45 000 руб."
    ),
    "OTTIMO": (
        "Горный велосипед для экстремальных условий.\n"
        "Прочная конструкция и advanced технологии. Для настоящих любителей адреналина. "
        "Розничная цена 95 000 руб."
    ),
}

FRAME_SIZES = ['M (17")', 'L (19")', 'XL (21")']

ABOUT_TEXT = """О нас | Официальный импортер TXED в России
Компания "СИБВЕЛО" рада представить себя как официального импортера бренда TXED в России. Мы гордимся тем, что предлагаем российским потребителям качественную продукцию с 40‑летней историей.
Почему мы выбрали TXED?
После тщательного анализа рынка мы остановились на бренде TXED благодаря его безупречной репутации в 50+ странах мира. Современное производство с европейскими стандартами качества.
Наш путь с брендом:
• 2023 — начало переговоров о сотрудничестве
• 2024 — официальный старт продаж в России
• Сегодня — активное развитие дилерской сети
Что мы предлагаем:
• Качественные велосипеды и E‑bike по доступным ценам
• Полную техническую поддержку
• Гарантийное обслуживание на территории РФ
• Постоянное наличие запчастей на складах
Наши преимущества:
Прямые поставки с завода позволяют нам поддерживать конкурентные цены и обеспечивать стабильное наличие товара.
Наша миссия:
Сделать современные велосипеды и E‑bike доступными для широкого круга российских потребителей.
Сайт: https://txedbikes.ru
Напишите нам — ответим на все вопросы!
С уважением,
Команда "СИБВЕЛО"
Официальный импортер TXED в России"""

# --------------------------------------------------------------------------- #
# Вспомогательные функции
# --------------------------------------------------------------------------- #
def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("Каталог"), KeyboardButton("О нас")],
        [KeyboardButton("Позвать специалиста")],
    ]
    if user_id == ADMIN_ID:
        rows.append([KeyboardButton("Админ‑панель")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def catalog_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("PRIMO"), KeyboardButton("TERZO"), KeyboardButton("ULTIMO")],
        [KeyboardButton("TESORO"), KeyboardButton("OTTIMO"), KeyboardButton("Назад")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def frame_keyboard() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(size)] for size in FRAME_SIZES]
    rows.append([KeyboardButton("Назад")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def admin_panel_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("Статистика"), KeyboardButton("Рассылка")],
        [KeyboardButton("Список пользователей"), KeyboardButton("Выйти из админки")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# --------------------------------------------------------------------------- #
# Обработчики
# --------------------------------------------------------------------------- #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.full_name)

    await update.message.reply_text(
        f"Привет, {user.first_name}! Добро пожаловать в официальный магазин TXED!\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu_keyboard(user.id),
    )


async def catalog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Выберите модель велосипеда:", reply_markup=catalog_keyboard()
    )


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        ABOUT_TEXT,
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True),
    )


async def call_specialist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.update_user_activity(user.id)

    info = f"Пользователь {user.full_name} (ID: {user.id}) хочет связаться с Вами"
    try:
        await context.bot.send_message(ADMIN_ID, info)
        await update.message.reply_text(
            "Специалист уведомлен! С Вами свяжутся в ближайшее время."
        )
    except Exception as e:
        logger.error(f"Error sending notification to admin: {e}")
        await update.message.reply_text(
            "Произошла ошибка при отправке уведомления. Попробуйте позже."
        )


async def bike_model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    model = update.message.text
    if model not in BIKE_DESCRIPTIONS:
        return

    db.update_user_activity(update.effective_user.id)
    context.user_data["selected_bike"] = model

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Заказать"), KeyboardButton("Назад к моделям")]],
        resize_keyboard=True,
    )
    await update.message.reply_text(BIKE_DESCRIPTIONS[model], reply_markup=keyboard)


# ------------------- Оформление заказа ------------------- #
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Выберите размер рамы:", reply_markup=frame_keyboard()
    )
    return ORDER_NAME


async def frame_size_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    size = update.message.text
    if size not in FRAME_SIZES:
        return ORDER_NAME

    db.update_user_activity(update.effective_user.id)
    context.user_data["frame_size"] = size

    await update.message.reply_text(
        "Отлично! Теперь введите ваши данные для оформления заказа.\n\n"
        "Введите ваше ФИО:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ORDER_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["user_name"] = update.message.text
    await update.message.reply_text("Введите ваш номер телефона:")
    return ORDER_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["user_phone"] = update.message.text
    await update.message.reply_text("Введите ваш email:")
    return ORDER_EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["user_email"] = update.message.text

    # Сохраняем заказ
    db.add_order(
        user_id=user.id,
        user_name=context.user_data["user_name"],
        user_phone=context.user_data["user_phone"],
        user_email=context.user_data["user_email"],
        bike_model=context.user_data["selected_bike"],
        frame_size=context.user_data["frame_size"],
    )

    # Уведомление админу
    order_msg = f"""НОВЫЙ ЗАКАЗ!
Модель: {context.user_data['selected_bike']}
Размер рамы: {context.user_data['frame_size']}
ФИО: {context.user_data['user_name']}
Телефон: {context.user_data['user_phone']}
Email: {context.user_data['user_email']}
ID пользователя: {user.id}"""
    try:
        await context.bot.send_message(ADMIN_ID, order_msg)
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")

    await update.message.reply_text(
        "Спасибо за заказ! Наш специалист свяжется с вами в ближайшее время для подтверждения.",
        reply_markup=main_menu_keyboard(user.id),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Оформление заказа отменено.", reply_markup=main_menu_keyboard(update.effective_user.id)
    )
    context.user_data.clear()
    return ConversationHandler.END


# ------------------- Админ‑панель ------------------- #
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к админ‑панели")
        return

    await update.message.reply_text(
        "Панель администратора:", reply_markup=admin_panel_keyboard()
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа")
        return

    stats = db.get_user_stats()
    text = f"""Статистика бота:
Всего пользователей: {stats['total_users']}
Активных сегодня: {stats['active_today']}
Новых сегодня: {stats['new_today']}"""
    await update.message.reply_text(text)


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа")
        return

    context.user_data["awaiting_broadcast"] = True
    await update.message.reply_text(
        "Введите сообщение для рассылки:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Отмена рассылки")]], resize_keyboard=True
        ),
    )


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (
        update.effective_user.id != ADMIN_ID
        or not context.user_data.get("awaiting_broadcast")
    ):
        return

    users = db.get_all_users()
    successful = failed = 0
    await update.message.reply_text(f"Начинаю рассылку для {len(users)} пользователей...")

    for uid, *_ in users:
        try:
            await context.bot.send_message(uid, update.message.text)
            successful += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast error to {uid}: {e}")

    await update.message.reply_text(
        f"Рассылка завершена!\nУспешно: {successful}\nНе удалось: {failed}",
        reply_markup=admin_panel_keyboard(),
    )
    context.user_data.pop("awaiting_broadcast", None)


async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа")
        return

    users = db.get_all_users()
    if not users:
        await update.message.reply_text("Пользователей пока нет")
        return

    text = "Список пользователей:\n\n"
    for i, (uid, username, first, last) in enumerate(users[:50], 1):
        name = f"{first or ''} {last or ''}".strip() or "Не указано"
        uname = f"@{username}" if username else "Не указан"
        text += f"{i}. ID: {uid}\n Имя: {name}\n Username: {uname}\n\n"

    if len(users) > 50:
        text += f"... и ещё {len(users) - 50} пользователей"

    await update.message.reply_text(text)


# ------------------- Навигация ------------------- #
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.update_user_activity(update.effective_user.id)
    await update.message.reply_text(
        "Главное меню:", reply_markup=main_menu_keyboard(update.effective_user.id)
    )


async def back_to_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await catalog_handler(update, context)


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.update_user_activity(update.effective_user.id)
    await update.message.reply_text("Пожалуйста, используйте кнопки меню для навигации.")


# --------------------------------------------------------------------------- #
# Регистрация обработчиков
# --------------------------------------------------------------------------- #
def register_handlers(app: Application) -> None:
    # --- Команды ---
    app.add_handler(CommandHandler("start", start_command))

    # --- Диалог заказа ---
    order_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Заказать$"), order_start)],
        states={
            ORDER_NAME: [
                MessageHandler(filters.Regex("^" + "|".join(FRAME_SIZES) + "$"), frame_size_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name),
            ],
            ORDER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ORDER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Назад$"), cancel_order),
        ],
    )
    app.add_handler(order_conv)

    # --- Основные кнопки ---
    app.add_handler(MessageHandler(filters.Regex("^Каталог$"), catalog_handler))
    app.add_handler(MessageHandler(filters.Regex("^О нас$"), about_handler))
    app.add_handler(MessageHandler(filters.Regex("^Позвать специалиста$"), call_specialist))

    # --- Выбор модели ---
    app.add_handler(
        MessageHandler(
            filters.Regex("^(PRIMO|TERZO|ULTIMO|TESORO|OTTIMO)$"), bike_model_handler
        )
    )

    # --- Админ‑панель ---
    app.add_handler(MessageHandler(filters.Regex("^Админ‑панель$"), admin_panel))
    app.add_handler(MessageHandler(filters.Regex("^Статистика$"), admin_stats))
    app.add_handler(MessageHandler(filters.Regex("^Рассылка$"), broadcast_start))
    app.add_handler(MessageHandler(filters.Regex("^Список пользователей$"), users_list))
    app.add_handler(MessageHandler(filters.Regex("^Выйти из админки$"), back_to_main))

    # --- Рассылка (сообщение) ---
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & ~filters.Regex("^Отмена рассылки$")
            & filters.User(user_id=ADMIN_ID),
            broadcast_message,
        )
    )
    app.add_handler(
        MessageHandler(filters.Regex("^Отмена рассылки$"), admin_panel)
    )

    # --- Навигация ---
    app.add_handler(MessageHandler(filters.Regex("^Назад$"), back_to_main))
    app.add_handler(MessageHandler(filters.Regex("^Назад к моделям$"), back_to_catalog))

    # --- Неизвестные сообщения ---
    app.add_handler(MessageHandler(filters.ALL, unknown_message))


# --------------------------------------------------------------------------- #
# Запуск
# --------------------------------------------------------------------------- #
async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    register_handlers(app)

    port = int(os.getenv("PORT", 8443))
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL', 'your-app.railway.app')}/{BOT_TOKEN}"

    await app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=webhook_url,
    )


if __name__ == "__main__":
    asyncio.run(main())

