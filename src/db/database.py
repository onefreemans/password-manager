from sqlcipher3 import dbapi2 as sqlite3
import os


DB_PATH = os.path.join(os.path.dirname(__file__), "tracker.db")


def get_db(password_db):
    """Создаёт и возвращает соединение с SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"PRAGMA key = '{password_db}'")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(password_db):
    """Создаёт таблицы, если их ещё нет."""
    conn = get_db(password_db)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT NOT NULL,
            link TEXT DEFAULT 'Не добавлен.',
            login TEXT NOT NULL,
            password_encryption TEXT NOT NULL
            )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL
                )
        """)

    conn.commit()
    conn.close()
