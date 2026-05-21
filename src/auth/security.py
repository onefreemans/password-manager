from datetime import datetime, timedelta
from src.crypto.password_hash import check_master_password
from src.auth.db_auth import JSON_PATH
from src.db.database import DB_PATH
import os
from src.db.models import (
    get_setting_value,
    add_new_data_settings,
    delete_settings_by_key,
    increment_failed_attempts,
    reset_failed_attempts,
)


def check_bruteforce_protection(lock_until_str, password_db):
    """Если 3+ неудачных попыток и нет блокировки — ставит блокировку на 1 час."""
    failed_str = get_setting_value("failed_attempts", password_db)
    failed_count = int(failed_str) if failed_str else 0

    if failed_count >= 3 and not lock_until_str:
        lock_until = datetime.now() + timedelta(hours=1) #TODO: блокировка
        add_new_data_settings("lock_until", lock_until.isoformat(), password_db)
        print("Слишком много неверных попыток. Доступ заблокирован на 1 час.")
        exit()


def check_lockout(lock_until_str):
    """Проверяет активную блокировку. Возвращает True, если доступ запрещён."""
    if not lock_until_str:
        return False

    lock_until = datetime.fromisoformat(lock_until_str)
    if datetime.now() < lock_until:
        print(f"Доступ заблокирован до {lock_until.strftime('%H:%M:%S')}")
        return True
    return False


def handle_final_attempts(master_password_hash, password_db):
    """Финальные попытки после истечения блокировки. Возвращает пароль или exit."""
    final_str = get_setting_value("final_attempts", password_db)
    final_left = int(final_str) if final_str else 2

    while final_left > 0:
        print(
            f"⚠️ Финальные попытки: {final_left}. При неудаче все данные будут удалены!"
        )
        input_pass = input("Введите ваш мастер пароль: ")

        if not input_pass.strip():
            print("❌ Пароль не может быть пустым!\n")
            continue

        if check_master_password(input_pass, master_password_hash):
            print("Пароль верный✅")
            reset_failed_attempts(password_db)
            delete_settings_by_key("lock_until", password_db)
            delete_settings_by_key("final_attempts", password_db)
            return input_pass

        final_left -= 1
        delete_settings_by_key("final_attempts", password_db)
        if final_left > 0:
            add_new_data_settings("final_attempts", str(final_left), password_db)
        print("Пароль неверный ❌\n")

    os.remove(DB_PATH)
    os.remove(JSON_PATH)
    print("Все попытки исчерпаны. Данные удалены. Программа завершена.")
    exit()


def handle_regular_login(master_password_hash, password_db):
    """Обычный вход с 4 попытками. Возвращает пароль или exit."""
    failed_str = get_setting_value("failed_attempts", password_db)
    failed_count = int(failed_str) if failed_str else 0

    count = 4 - failed_count
    if count <= 0:
        count = 4
        reset_failed_attempts(password_db)

    while count > 0:
        input_pass = input("Введите ваш мастер пароль: ")

        if not input_pass.strip():
            print("❌ Пароль не может быть пустым!\n")
            continue

        if check_master_password(input_pass, master_password_hash):
            print("Пароль верный✅")
            reset_failed_attempts(password_db)
            return input_pass

        count -= 1
        increment_failed_attempts(password_db)

        if count == 2:
            help_hint = get_setting_value("help_pass", password_db)
            print(f"\nПодсказка❗ {help_hint}")

        if count == 0:
            lock_until = datetime.now() + timedelta(hours=1) #TODO: блокировка
            add_new_data_settings("lock_until", lock_until.isoformat(), password_db)
            print("Вы истратили все попытки. Попробуйте через 1 час.")
            exit()

        print(f"Пароль неверный ❌ - Осталось попыток: {count}\n")

    return None
