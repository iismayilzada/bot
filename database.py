import sqlite3
import datetime

DATABASE_NAME = "data/bot_database.db"

def init_db():
    """Инициализирует базу данных, создает таблицы, если их нет."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                last_daily TEXT,
                last_weekly TEXT,
                last_timely TEXT,
                last_work TEXT,
                last_rob TEXT,
                messages_count INTEGER DEFAULT 0,
                month_messages_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop_roles (
                role_id INTEGER PRIMARY KEY,
                price INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_type TEXT NOT NULL, -- 'role', 'case', 'coupon'
                item_id TEXT NOT NULL,        -- role_id, case_type (enum/str), coupon_type (enum/str)
                quantity INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, item_type, item_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                expire_date TEXT NOT NULL,
                is_active INTEGER DEFAULT 1 -- 1 for active, 0 for expired/removed
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mutes (
                mute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                is_active INTEGER DEFAULT 1 -- 1 for active, 0 for removed
            )
        """)
        db.commit()

def get_user_data(user_id: int):
    """Возвращает данные пользователя или создает новую запись."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            db.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
        return user_data

def update_user_balance(user_id: int, amount: int):
    """Обновляет баланс пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        db.commit()

def set_user_balance(user_id: int, amount: int):
    """Устанавливает баланс пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
        db.commit()

def update_user_bank(user_id: int, amount: int):
    """Обновляет банковский баланс пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET bank = bank + ? WHERE user_id = ?", (amount, user_id))
        db.commit()

def set_user_bank(user_id: int, amount: int):
    """Устанавливает банковский баланс пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET bank = ? WHERE user_id = ?", (amount, user_id))
        db.commit()

def update_last_claim_time(user_id: int, command_type: str, time_str: str):
    """Обновляет время последнего использования команды."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute(f"UPDATE users SET last_{command_type} = ? WHERE user_id = ?", (time_str, user_id))
        db.commit()

def get_last_claim_time(user_id: int, command_type: str):
    """Получает время последнего использования команды."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute(f"SELECT last_{command_type} FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_shop_roles():
    """Получает все роли из магазина."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT role_id, price FROM shop_roles ORDER BY price ASC") # Сортировка по цене
        return cursor.fetchall()

def add_shop_role(role_id: int, price: int):
    """Добавляет роль в магазин."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("INSERT OR REPLACE INTO shop_roles (role_id, price) VALUES (?, ?)", (role_id, price))
        db.commit()

def remove_shop_role(role_id: int):
    """Удаляет роль из магазина."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM shop_roles WHERE role_id = ?", (role_id,))
        db.commit()

def get_shop_role_price(role_id: int):
    """Получает цену роли из магазина."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT price FROM shop_roles WHERE role_id = ?", (role_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def add_inventory_item(user_id: int, item_type: str, item_id: str, quantity: int = 1):
    """Добавляет предмет в инвентарь пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        # Проверяем, существует ли уже запись для этого user_id, item_type, item_id
        cursor.execute("""
            SELECT quantity FROM inventory
            WHERE user_id = ? AND item_type = ? AND item_id = ?
        """, (user_id, item_type, item_id))
        existing_quantity = cursor.fetchone()

        if existing_quantity:
            # Если запись существует, обновляем количество
            cursor.execute("""
                UPDATE inventory SET quantity = quantity + ?
                WHERE user_id = ? AND item_type = ? AND item_id = ?
            """, (quantity, user_id, item_type, item_id))
        else:
            # Если записи нет, вставляем новую
            cursor.execute("""
                INSERT INTO inventory (user_id, item_type, item_id, quantity)
                VALUES (?, ?, ?, ?)
            """, (user_id, item_type, item_id, quantity))
        db.commit()


def remove_inventory_item(user_id: int, item_type: str, item_id: str, quantity: int = 1):
    """Удаляет предмет из инвентаря пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE inventory SET quantity = quantity - ?
            WHERE user_id = ? AND item_type = ? AND item_id = ?
        """, (quantity, user_id, item_type, item_id))
        cursor.execute("""
            DELETE FROM inventory
            WHERE user_id = ? AND item_type = ? AND item_id = ? AND quantity <= 0
        """, (user_id, item_type, item_id))
        db.commit()

def get_inventory_items(user_id: int):
    """Получает все предметы из инвентаря пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT item_type, item_id, quantity FROM inventory WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def get_inventory_item_quantity(user_id: int, item_type: str, item_id: str):
    """Получает количество конкретного предмета в инвентаре."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_type = ? AND item_id = ?", (user_id, item_type, item_id))
        result = cursor.fetchone()
        return result[0] if result else 0

def add_warning(user_id: int, moderator_id: int, reason: str, issue_date: datetime.datetime, expire_date: datetime.datetime):
    """Добавляет предупреждение."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO warnings (user_id, moderator_id, reason, issue_date, expire_date, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (user_id, moderator_id, reason, issue_date.isoformat(), expire_date.isoformat()))
        db.commit()
        return cursor.lastrowid # Возвращаем ID нового предупреждения

def get_active_warnings(user_id: int):
    """Получает активные предупреждения пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT warn_id, reason, issue_date, expire_date FROM warnings
            WHERE user_id = ? AND is_active = 1 AND expire_date > ?
            ORDER BY issue_date ASC
        """, (user_id, datetime.datetime.now().isoformat()))
        return cursor.fetchall()

def remove_warning(warn_id: int):
    """Снимает предупреждение (помечает как неактивное)."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE warnings SET is_active = 0 WHERE warn_id = ?", (warn_id,))
        db.commit()

def add_mute(user_id: int, moderator_id: int, reason: str, issue_date: datetime.datetime, end_date: datetime.datetime):
    """Добавляет запись о муте."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO mutes (user_id, moderator_id, reason, issue_date, end_date, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (user_id, moderator_id, reason, issue_date.isoformat(), end_date.isoformat()))
        db.commit()

def remove_mute(user_id: int):
    """Снимает мут (помечает как неактивный)."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE mutes SET is_active = 0 WHERE user_id = ? AND is_active = 1", (user_id,))
        db.commit()

def get_active_mute(user_id: int):
    """Проверяет, активен ли мут для пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM mutes
            WHERE user_id = ? AND is_active = 1 AND end_date > ?
            ORDER BY issue_date DESC LIMIT 1
        """, (user_id, datetime.datetime.now().isoformat()))
        return cursor.fetchone()

def update_messages_count(user_id: int):
    """Обновляет счетчик сообщений пользователя."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET messages_count = messages_count + 1, month_messages_count = month_messages_count + 1 WHERE user_id = ?", (user_id,))
        db.commit()

def get_leaderboard_balance():
    """Возвращает топ пользователей по балансу."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
        return cursor.fetchall()

def get_leaderboard_messages():
    """Возвращает топ пользователей по сообщениям."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT user_id, messages_count FROM users ORDER BY messages_count DESC LIMIT 10")
        return cursor.fetchall()

def get_leaderboard_month_messages():
    """Возвращает топ пользователей по сообщениям за месяц."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("SELECT user_id, month_messages_count FROM users ORDER BY month_messages_count DESC LIMIT 10")
        return cursor.fetchall()

def reset_month_messages():
    """Сбрасывает счетчики сообщений за месяц для всех пользователей."""
    with sqlite3.connect(DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET month_messages_count = 0")
        db.commit()