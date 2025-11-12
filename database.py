import sqlite3
import datetime
from typing import List, Tuple, Dict

class Database:
    def __init__(self, db_name: str = "bot_database.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TEXT,
                last_active TEXT
            )
        ''')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                user_phone TEXT,
                user_email TEXT,
                bike_model TEXT,
                frame_size TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        """Добавление нового пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        current_time = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, current_time, current_time))
        
        conn.commit()
        conn.close()

    def update_user_activity(self, user_id: int):
        """Обновление времени последней активности"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        current_time = datetime.datetime.now().isoformat()
        cursor.execute('''
            UPDATE users SET last_active = ? WHERE user_id = ?
        ''', (current_time, user_id))
        
        conn.commit()
        conn.close()

    def add_order(self, user_id: int, user_name: str, user_phone: str, user_email: str, bike_model: str, frame_size: str):
        """Добавление нового заказа"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        current_time = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO orders (user_id, user_name, user_phone, user_email, bike_model, frame_size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, user_phone, user_email, bike_model, frame_size, current_time))
        
        conn.commit()
        conn.close()

    def get_user_stats(self):
        """Получение статистики пользователей"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Общее количество пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Активные за сегодня
        today = datetime.datetime.now().date().isoformat()
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(last_active) = ?', (today,))
        active_today = cursor.fetchone()[0]
        
        # Новые пользователи за сегодня
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(created_at) = ?', (today,))
        new_today = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'new_today': new_today
        }

    def get_all_users(self):
        """Получение списка всех пользователей"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, username, first_name, last_name FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        
        conn.close()
        return users
