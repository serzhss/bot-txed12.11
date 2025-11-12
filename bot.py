import os
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '7819916914:AAHuOv_6eph7IZ2OYyqq-zKz22yr_G4MIPk')

# ID администратора
ADMIN_ID = 445570258

# Состояния для ConversationHandler
ORDER_NAME, ORDER_PHONE, ORDER_EMAIL = range(3)

# Инициализация базы данных
db = Database()

# Тексты и фотографии для моделей велосипедов
BIKE_DESCRIPTIONS = {
    'PRIMO': {
        'description': '''Маневренная, универсальная модель для активного фанового катания в холмистой местности.
Велосипед базового уровня в нашей линейке, для зрелых любителей качества и современных тенденции велостроения. Розничная цена 50 000руб.''',
        'photos': [
            'https://optim.tildacdn.com/tild3663-6265-4666-b535-613361663030/-/format/webp/Photo-44.webp',
            'https://optim.tildacdn.com/tild6263-6233-4537-a436-633033386132/-/format/webp/Photo-47.webp',
            'https://optim.tildacdn.com/tild3038-3263-4935-a533-326637363030/-/format/webp/Photo-49.webp',
            'https://optim.tildacdn.com/tild3831-3637-4836-b836-363934653638/-/format/webp/Photo-50.webp',
            'https://optim.tildacdn.com/tild3734-6433-4835-b639-623036366165/-/format/webp/Photo-57.webp'
        ]
    },
    
    'TERZO': {
        'description': '''Спортивная модель для профессионального использования. 
Идеальный выбор для соревнований и тренировок. Премиальное качество сборки. Розничная цена 75 000руб.''',
        'photos': [
            'https://optim.tildacdn.com/tild6165-6635-4737-a532-303866623732/-/format/webp/Photo-1.webp',
            'https://optim.tildacdn.com/tild3866-3634-4337-b030-666134326134/-/format/webp/Photo-3.webp',
            'https://optim.tildacdn.com/tild3232-6462-4263-a564-333965326565/-/format/webp/Photo-4.webp',
            'https://optim.tildacdn.com/tild6330-3863-4234-a162-326465613431/-/format/webp/Photo-6.webp',
            'https://optim.tildacdn.com/tild3339-3737-4462-a239-323865323936/-/format/webp/Photo-8.webp'
        ]
    },
    
    'ULTIMO': {
        'description': '''Флагманская модель с инновационными технологиями.
Максимальная производительность и комфорт. Для самых требовательных велосипедистов. Розничная цена 120 000руб.''',
        'photos': [
            'https://optim.tildacdn.com/tild3634-6164-4532-a639-383334633561/-/format/webp/Photo-58.webp',
            'https://optim.tildacdn.com/tild3238-6530-4431-a135-346665323065/-/format/webp/Photo-61.webp',
            'https://optim.tildacdn.com/tild3135-3365-4363-b236-346363303238/-/format/webp/Photo-62.webp',
            'https://optim.tildacdn.com/tild3962-6133-4636-b236-313336356163/-/format/webp/Photo-67.webp'
        ]
    },
    
    'TESORO': {
        'description': '''Городской велосипед с элегантным дизайном.
Идеален для повседневного использования и прогулок по городу. Стиль и практичность. Розничная цена 45 000руб.''',
        'photos': [
            'https://optim.tildacdn.com/tild3661-3336-4362-a130-326639613866/-/format/webp/Photo-13.webp',
            'https://optim.tildacdn.com/tild6131-3239-4237-a465-346663376637/-/format/webp/Photo-14.webp',
            'https://optim.tildacdn.com/tild3732-3431-4132-b266-636138336465/-/format/webp/Photo-17.webp',
            'https://optim.tildacdn.com/tild3835-3233-4337-b337-366431643565/-/format/webp/Photo-18.webp',
            'https://optim.tildacdn.com/tild6330-6564-4434-a236-393039343938/-/format/webp/Photo-21.webp',
            'https://optim.tildacdn.com/tild6531-3662-4733-a635-343765343739/-/format/webp/Photo-24.webp'
        ]
    },
    
    'OTTIMO': {
        'description': '''Горный велосипед для экстремальных условий.
Прочная конструкция и advanced технологии. Для настоящих любителей адреналина. Розничная цена 95 000руб.''',
        'photos': [
            'https://optim.tildacdn.com/tild6662-6461-4138-a661-323964656231/-/format/webp/Photo-27.webp',
            'https://optim.tildacdn.com/tild3333-6366-4032-a632-356637323136/-/format/webp/Photo-30.webp',
            'https://optim.tildacdn.com/tild6435-3566-4231-a232-303332323339/-/format/webp/Photo-35.webp',
            'https://optim.tildacdn.com/tild3365-6263-4039-b632-653338326235/-/format/webp/Photo-36.webp',
            'https://optim.tildacdn.com/tild3761-6261-4332-b839-653934353539/-/format/webp/Photo-37.webp',
            'https://optim.tildacdn.com/tild3432-3963-4162-b565-373563326635/-/format/webp/Photo-38.webp',
            'https://optim.tildacdn.com/tild3634-3132-4734-a666-336634666538/-/format/webp/Photo-43.webp'
        ]
    }
}

# Размеры рам
FRAME_SIZES = ['M (17")', 'L (19")', 'XL (21")']

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Главное меню (без админ-панели)
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f'Привет, {user.first_name}! Добро пожаловать в официальный магазин TXED!\n\n'
        'Выберите нужный раздел:',
        reply_markup=reply_markup
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return
    
    keyboard = [
        ['📊 Статистика', '📢 Рассылка'],
        ['👥 Список пользователей', '⬅️ Выйти из админки']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text('⚙️ Панель администратора:', reply_markup=reply_markup)

async def handle_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Каталог"""
    keyboard = [
        ['PRIMO', 'TERZO', 'ULTIMO'],
        ['TESORO', 'OTTIMO', '⬅️ Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите модель велосипеда:', reply_markup=reply_markup)

async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки О нас"""
    about_text = """О нас | Официальный импортер TXED в России

Компания "СИБВЕЛО" рада представить себя как официального импортера бренда TXED в России. Мы гордимся тем, что предлагаем российским потребителям качественную продукцию с 40-летней историей.

Почему мы выбрали TXED?
После тщательного анализа рынка мы остановились на бренде TXED благодаря его безупречной репутации в 50+ странах мира. Современное производство с европейскими стандартами качества.

Наш путь с брендом:
• 2023 — начало переговоров о сотрудничестве
• 2024 — официальный старт продаж в России
• Сегодня — активное развитие дилерской сети

Что мы предлагаем:
• Качественные велосипеды и E-bike по доступным ценам
• Полную техническую поддержку
• Гарантийное обслуживание на территории РФ
• Постоянное наличие запчастей на складах

Наши преимущества:
Прямые поставки с завода позволяют нам поддерживать конкурентные цены и обеспечивать стабильное наличие товара.

Наша миссия:
Сделать современные велосипеды и E-bike доступными для широкого круга российских потребителей.

Сайт: https://txedbikes.ru
Напишите нам — ответим на все вопросы!

С уважением,
Команда "СИБВЕЛО"
Официальный импортер TXED в России"""
    
    keyboard = [['⬅️ Назад']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(about_text, reply_markup=reply_markup)

async def handle_specialist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Позвать специалиста"""
    user = update.message.from_user
    db.update_user_activity(user.id)
    
    # Отправляем уведомление администратору
    user_info = f"Пользователь {user.first_name} (ID: {user.id}) хочет связаться с Вами"
    
    try:
        await context.bot.send_message(ADMIN_ID, user_info)
        await update.message.reply_text("✅ Специалист уведомлен! С Вами свяжутся в ближайшее время.")
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при отправке уведомления. Попробуйте позже.")
        logger.error(f"Error sending notification to admin: {e}")

async def handle_bike_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора модели велосипеда"""
    bike_model = update.message.text
    user = update.message.from_user
    db.update_user_activity(user.id)
    
    if bike_model in BIKE_DESCRIPTIONS:
        bike_data = BIKE_DESCRIPTIONS[bike_model]
        description = bike_data['description']
        photos = bike_data['photos']
        context.user_data['selected_bike'] = bike_model
        
        # Отправляем первую фотографию с описанием
        await update.message.reply_photo(
            photo=photos[0],
            caption=f"{bike_model}\n\n{description}"
        )
        
        # Отправляем остальные фотографии
        for i, photo_url in enumerate(photos[1:], 2):
            await update.message.reply_photo(
                photo=photo_url,
                caption=f"{bike_model} - фото {i}/{len(photos)}"
            )
            # Небольшая задержка между отправкой фото
            await asyncio.sleep(0.5)
        
        # Кнопки после показа всех фото
        keyboard = [['🛒 Заказать', '⬅️ Назад к моделям']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f'Хотите заказать {bike_model} или посмотреть другие модели?',
            reply_markup=reply_markup
        )

async def handle_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало оформления заказа - выбор размера рамы"""
    keyboard = [[size] for size in FRAME_SIZES]
    keyboard.append(['⬅️ Назад'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите размер рамы:', reply_markup=reply_markup)

async def handle_frame_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора размера рамы"""
    frame_size = update.message.text
    user = update.message.from_user
    db.update_user_activity(user.id)
    
    if frame_size in FRAME_SIZES:
        context.user_data['frame_size'] = frame_size
        
        await update.message.reply_text(
            'Отлично! Теперь введите ваши данные для оформления заказа.\n\n'
            'Введите ваше ФИО:',
            reply_markup=ReplyKeyboardRemove()
        )
        return ORDER_NAME

async def get_order_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени пользователя"""
    context.user_data['user_name'] = update.message.text
    
    await update.message.reply_text('Введите ваш номер телефона:')
    return ORDER_PHONE

async def get_order_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение телефона пользователя"""
    context.user_data['user_phone'] = update.message.text
    
    await update.message.reply_text('Введите ваш email:')
    return ORDER_EMAIL

async def get_order_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email и завершение заказа"""
    user = update.message.from_user
    context.user_data['user_email'] = update.message.text
    
    # Сохраняем заказ в базу данных
    db.add_order(
        user_id=user.id,
        user_name=context.user_data['user_name'],
        user_phone=context.user_data['user_phone'],
        user_email=context.user_data['user_email'],
        bike_model=context.user_data['selected_bike'],
        frame_size=context.user_data['frame_size']
    )
    
    # Отправляем уведомление администратору
    order_info = f"""🎯 НОВЫЙ ЗАКАЗ!

Модель: {context.user_data['selected_bike']}
Размер рамы: {context.user_data['frame_size']}
ФИО: {context.user_data['user_name']}
Телефон: {context.user_data['user_phone']}
Email: {context.user_data['user_email']}
ID пользователя: {user.id}"""
    
    try:
        await context.bot.send_message(ADMIN_ID, order_info)
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")
    
    # Возвращаем в главное меню (без админ-панели)
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '✅ Спасибо за заказ! Наш специалист свяжется с вами в ближайшее время для подтверждения.',
        reply_markup=reply_markup
    )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена оформления заказа"""
    user = update.message.from_user
    
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Оформление заказа отменено.',
        reply_markup=reply_markup
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# АДМИН-ПАНЕЛЬ
async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик админ-панели"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа к админ-панели")
        return
    
    keyboard = [
        ['📊 Статистика', '📢 Рассылка'],
        ['👥 Список пользователей', '⬅️ Выйти из админки']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text('⚙️ Панель администратора:', reply_markup=reply_markup)

async def handle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ статистики"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа")
        return
    
    stats = db.get_user_stats()
    
    stats_text = f"""📊 Статистика бота:

👥 Всего пользователей: {stats['total_users']}
✅ Активных сегодня: {stats['active_today']}
🆕 Новых сегодня: {stats['new_today']}"""
    
    await update.message.reply_text(stats_text)

async def handle_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало рассылки"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа")
        return
    
    context.user_data['awaiting_broadcast'] = True
    await update.message.reply_text(
        'Введите сообщение для рассылки:',
        reply_markup=ReplyKeyboardMarkup([['❌ Отмена рассылки']], resize_keyboard=True)
    )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения для рассылки"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID or not context.user_data.get('awaiting_broadcast'):
        return
    
    users = db.get_all_users()
    successful = 0
    failed = 0
    
    await update.message.reply_text(f"🔄 Начинаю рассылку для {len(users)} пользователей...")
    
    for user_data in users:
        try:
            await context.bot.send_message(user_data[0], update.message.text)
            successful += 1
        except Exception as e:
            failed += 1
            logger.error(f"Error sending to user {user_data[0]}: {e}")
    
    # Возвращаем в админ-панель
    keyboard = [
        ['📊 Статистика', '📢 Рассылка'],
        ['👥 Список пользователей', '⬅️ Выйти из админки']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Рассылка завершена!\n\n"
        f"✅ Успешно: {successful}\n"
        f"❌ Не удалось: {failed}",
        reply_markup=reply_markup
    )
    
    context.user_data.pop('awaiting_broadcast', None)

async def handle_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка пользователей"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа")
        return
    
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("📝 Пользователей пока нет")
        return
    
    users_text = "👥 Список пользователей:\n\n"
    for i, user_data in enumerate(users[:50], 1):
        user_id, username, first_name, last_name = user_data
        name = f"{first_name or ''} {last_name or ''}".strip() or 'Не указано'
        username = f"@{username}" if username else 'Не указан'
        users_text += f"{i}. ID: {user_id}\n   Имя: {name}\n   Username: {username}\n\n"
    
    if len(users) > 50:
        users_text += f"... и еще {len(users) - 50} пользователей"
    
    await update.message.reply_text(users_text)

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Назад"""
    user = update.message.from_user
    db.update_user_activity(user.id)
    
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Главное меню:', reply_markup=reply_markup)

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных сообщений"""
    user = update.message.from_user
    db.update_user_activity(user.id)
    await update.message.reply_text("Пожалуйста, используйте кнопки меню для навигации.")

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler для оформления заказа
    order_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex('^🛒 Заказать$'), handle_order_start)],
        states={
            ORDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_name)],
            ORDER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_phone)],
            ORDER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_email)],
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex('^⬅️ Назад$'), cancel_order)]
    )
    
    # Обработчики сообщений
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('admin', admin_command))  # Команда /admin
    application.add_handler(order_conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^🚲 Каталог$'), handle_catalog))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^ℹ️ О нас$'), handle_about))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^👨‍💼 Позвать специалиста$'), handle_specialist))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⚙️ Админ-панель$'), handle_admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^📊 Статистика$'), handle_admin_stats))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^📢 Рассылка$'), handle_broadcast_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^👥 Список пользователей$'), handle_users_list))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⬅️ Выйти из админки$'), handle_back))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⬅️ Назад$'), handle_back))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⬅️ Назад к моделям$'), handle_catalog))
    
    # Обработчики выбора моделей и размеров
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(PRIMO|TERZO|ULTIMO|TESORO|OTTIMO)$'), handle_bike_model))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(M \\(17\"\\)|L \\(19\"\\)|XL \\(21\"\\))$'), handle_frame_size))
    
    # Обработчик для рассылки
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Отмена рассылки$'), 
        handle_broadcast_message
    ))
    
    # Обработчик отмены рассылки
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^❌ Отмена рассылки$'), handle_admin_panel))
    
    # Обработчик неизвестных сообщений
    application.add_handler(MessageHandler(filters.ALL, handle_unknown_message))
    
    # Запускаем бота с polling
    application.run_polling()

if __name__ == '__main__':
    main()
