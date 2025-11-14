import os
import logging
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, CallbackContext, filters

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 445570258))

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable is required!")
    logger.info("💡 How to fix: Go to your Railway project -> Settings -> Variables -> Add BOT_TOKEN")
    exit(1)

logger.info("✅ Bot token loaded successfully")

# === БАЗА ДАННЫХ ===
DB_FILE = "users.db"

def ensure_users_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            first_seen TEXT,
            last_activity TEXT,
            messages_count INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    logger.info(f"✅ Database {DB_FILE} ready")

ensure_users_db()

# === ПОЛЬЗОВАТЕЛИ ===
def load_users():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        users = {}
        for row in rows:
            users[row[0]] = {
                'username': row[1], 'first_name': row[2], 'last_name': row[3],
                'full_name': row[4], 'first_seen': row[5], 'last_activity': row[6],
                'messages_count': row[7]
            }
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}

def save_users(users):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for uid, data in users.items():
            cursor.execute('''
                INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                uid, data.get('username'), data.get('first_name'), data.get('last_name'),
                data.get('full_name'), data.get('first_seen'), data.get('last_activity'),
                data.get('messages_count')
            ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        return False

def add_user(user_id, username, first_name, last_name):
    import datetime
    users = load_users()
    now = datetime.datetime.now().isoformat()
    uid = str(user_id)
    if uid in users:
        users[uid].update({
            'username': username, 'first_name': first_name, 'last_name': last_name,
            'full_name': f"{first_name} {last_name or ''}".strip(),
            'last_activity': now,
            'messages_count': users[uid].get('messages_count', 0) + 1
        })
    else:
        users[uid] = {
            'username': username, 'first_name': first_name, 'last_name': last_name,
            'full_name': f"{first_name} {last_name or ''}".strip(),
            'first_seen': now, 'last_activity': now, 'messages_count': 1
        }
    save_users(users)

def get_all_users():
    return load_users()

def update_user_activity(user_id):
    import datetime
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]['last_activity'] = datetime.datetime.now().isoformat()
        users[uid]['messages_count'] = users[uid].get('messages_count', 0) + 1
        save_users(users)
    else:
        add_user(user_id, None, None, None)

# === КАТАЛОГ ===
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
    }
}

# Размеры рам
FRAME_SIZES = ['M (17")', 'L (19")', 'XL (21")']

# Состояния для ConversationHandler
ORDER_NAME_PHONE, NAME, PHONE = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.message.from_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Главное меню
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append(['⚙️ Админ-панель'])
    
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
    user = update.message.from_user
    update_user_activity(user.id)
    
    keyboard = [
        ['PRIMO', 'TERZO'],
        ['⬅️ Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите модель велосипеда:', reply_markup=reply_markup)

async def handle_bike_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора модели велосипеда"""
    bike_model = update.message.text
    user = update.message.from_user
    update_user_activity(user.id)
    
    if bike_model in BIKE_DESCRIPTIONS:
        bike_data = BIKE_DESCRIPTIONS[bike_model]
        description = bike_data['description']
        photos = bike_data['photos']
        context.user_data['selected_bike'] = bike_model
        
        # Отправляем первую фотографию с описанием
        await update.message.reply_photo(
            photo=photos[0],
            caption=f"🚲 {bike_model}\n\n{description}"
        )
        
        # Отправляем остальные фотографии
        for i, photo_url in enumerate(photos[1:], 2):
            await update.message.reply_photo(
                photo=photo_url,
                caption=f"{bike_model} - фото {i}/{len(photos)}"
            )
            await asyncio.sleep(0.5)
        
        # Кнопки после показа всех фото
        keyboard = [['🛒 Заказать', '⬅️ Назад к моделям']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f'Хотите заказать {bike_model} или посмотреть другие модели?',
            reply_markup=reply_markup
        )

async def handle_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало оформления заказа"""
    user = update.message.from_user
    update_user_activity(user.id)
    
    # Проверяем, что модель выбрана
    if 'selected_bike' not in context.user_data:
        await update.message.reply_text("❌ Сначала выберите модель велосипеда")
        return ConversationHandler.END
    
    keyboard = [[size] for size in FRAME_SIZES]
    keyboard.append(['⬅️ Отмена заказа'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите размер рамы:', reply_markup=reply_markup)
    
    return ORDER_NAME_PHONE

async def handle_frame_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора размера рамы"""
    frame_size = update.message.text
    user = update.message.from_user
    update_user_activity(user.id)
    
    if frame_size in FRAME_SIZES:
        context.user_data['frame_size'] = frame_size
        
        await update.message.reply_text(
            '📝 Введите ваше имя:',
            reply_markup=ReplyKeyboardRemove()
        )
        return NAME
    
    await update.message.reply_text("❌ Пожалуйста, выберите размер рамы из предложенных вариантов.")
    return ORDER_NAME_PHONE

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени пользователя"""
    user = update.message.from_user
    update_user_activity(user.id)
    
    user_name = update.message.text.strip()
    
    if len(user_name) < 2:
        await update.message.reply_text("❌ Имя слишком короткое. Введите ваше настоящее имя:")
        return NAME
    
    context.user_data['user_name'] = user_name
    
    await update.message.reply_text(
        '📞 Теперь введите ваш номер телефона:'
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение телефона пользователя"""
    user = update.message.from_user
    update_user_activity(user.id)
    
    user_phone = update.message.text.strip()
    
    # Базовая проверка номера телефона
    if len(user_phone) < 5:
        await update.message.reply_text("❌ Номер телефона слишком короткий. Введите корректный номер:")
        return PHONE
    
    # Отправляем уведомление администратору
    order_info = f"""🎯 НОВЫЙ ЗАКАЗ!

Модель: {context.user_data['selected_bike']}
Размер рамы: {context.user_data['frame_size']}
Имя: {context.user_data['user_name']}
Телефон: {user_phone}
ID пользователя: {user.id}
Username: @{user.username or 'не указан'}"""
    
    await context.bot.send_message(ADMIN_ID, order_info)
    
    # Возвращаем в главное меню
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append(['⚙️ Админ-панель'])
    
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
    update_user_activity(user.id)
    
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append(['⚙️ Админ-панель'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '❌ Оформление заказа отменено.',
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
    
    update_user_activity(user.id)
    
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
    
    update_user_activity(user.id)
    
    users = get_all_users()
    import datetime
    today = datetime.datetime.now().date()
    active_today = sum(1 for u in users.values() if u.get('last_activity') and datetime.datetime.fromisoformat(u['last_activity']).date() == today)
    total_messages = sum(u.get('messages_count', 0) for u in users.values())
    
    stats_text = f"""📊 Статистика бота:

👥 Всего пользователей: {len(users)}
✅ Активных сегодня: {active_today}
💬 Всего сообщений: {total_messages}"""

    await update.message.reply_text(stats_text)

async def handle_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка пользователей"""
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа")
        return
    
    update_user_activity(user.id)
    
    users = get_all_users()
    
    if not users:
        await update.message.reply_text("📝 Пользователей пока нет")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]['last_activity'], reverse=True)
    text = "<b>Последние пользователи:</b>\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        text += f"{i}. {data['full_name']}\n"
        text += f"   @{data['username'] or 'нет'}\n"
        text += f"   ID: {uid}\n"
        text += f"   Сообщений: {data['messages_count']}\n\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Назад"""
    user = update.message.from_user
    update_user_activity(user.id)
    
    keyboard = [
        ['🚲 Каталог', 'ℹ️ О нас'],
        ['👨‍💼 Позвать специалиста']
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append(['⚙️ Админ-панель'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Главное меню:', reply_markup=reply_markup)

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных сообщений"""
    user = update.message.from_user
    update_user_activity(user.id)
    await update.message.reply_text("❌ Пожалуйста, используйте кнопки меню для навигации.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler для оформления заказа
    order_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex('^🛒 Заказать$'), handle_order_start)],
        states={
            ORDER_NAME_PHONE: [
                MessageHandler(filters.TEXT & filters.Regex('^(M \\(17\"\\)|L \\(19\"\\)|XL \\(21\"\\))$'), handle_frame_size),
                MessageHandler(filters.TEXT & filters.Regex('^⬅️ Отмена заказа$'), cancel_order)
            ],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex('^⬅️ Отмена заказа$'), cancel_order),
            CommandHandler('cancel', cancel_order),
            MessageHandler(filters.ALL, cancel_order)
        ]
    )
    
    # Обработчики сообщений
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('admin', admin_command))
    application.add_handler(CommandHandler('cancel', cancel_order))
    application.add_handler(order_conv_handler)
    
    # Обработчики кнопок
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^🚲 Каталог$'), handle_catalog))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^👨‍💼 Позвать специалиста$'), lambda u, c: u.message.reply_text("✅ Специалист уведомлен! С Вами свяжутся в ближайшее время.")))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⚙️ Админ-панель$'), handle_admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^📊 Статистика$'), handle_admin_stats))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^👥 Список пользователей$'), handle_users_list))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⬅️ Выйти из админки$'), handle_back))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⬅️ Назад$'), handle_back))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^⬅️ Назад к моделям$'), handle_catalog))
    
    # Обработчики выбора моделей
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^(PRIMO|TERZO)$'), handle_bike_model))
    
    # Обработчик неизвестных сообщений
    application.add_handler(MessageHandler(filters.ALL, handle_unknown_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота с polling
    logger.info("✅ Starting bot with polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
