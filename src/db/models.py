from src.db.database import get_db


def add_new_data(site_name, link, login, password_encryption, password_db):
    """Создаёт новые данные в 'applications'"""
    conn = get_db(password_db)
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO applications (site_name, link, login, password_encryption)
    VALUES (?, ?, ?, ?)
    """,
        (site_name, link, login, password_encryption),
    )
    conn.commit()
    conn.close()


def add_new_data_settings(key, value, password_db):
    """Создаёт новые данные в 'settings'"""
    conn = get_db(password_db)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        """,
        (key, value),
    )
    conn.commit()
    conn.close()


def get_setting_value(key, password_db):
    """Получает значение key из базы данны"""
    conn = get_db(password_db)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return None


def get_all_applications(password_db):
    """Возвращает все записи таблицы"""
    conn = get_db(password_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications")
    row = cursor.fetchall()
    conn.close()
    if row:
        return row
    return []


def search_application_by_site(site_name, password_db):
    """Поиск по имени сайта в таблице"""
    conn = get_db(password_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM applications WHERE site_name LIKE ?", (f"%{site_name}%",)
    )
    row = cursor.fetchall()
    conn.close()
    if row:
        return row
    return []


def delete_application_by_id(app_id, password_db):
    """Удаление записи из базы данных"""
    conn = get_db(password_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return True
    return False


def delete_settings_by_key(key, password_db):
    """Удалить запись по значению поля value"""
    conn = get_db(password_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return True
    return False


def increment_failed_attempts(password_db):
    """Увеличивает счётчик неудачных попыток на 1. Возвращает новое значение."""
    count_str = get_setting_value("failed_attempts", password_db)
    count = int(count_str) if count_str else 0
    count += 1
    # Если запись есть — обновляем, если нет — создаём
    conn = get_db(password_db)
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM settings WHERE key = 'failed_attempts'")
    if cursor.fetchone():
        cursor.execute(
            "UPDATE settings SET value = ? WHERE key = 'failed_attempts'", (str(count),)
        )
    else:
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES ('failed_attempts', ?)",
            (str(count),),
        )
    conn.commit()
    conn.close()
    return count


def reset_failed_attempts(password_db):
    """Сбрасывает счётчик неудачных попыток."""
    delete_settings_by_key("failed_attempts", password_db)
