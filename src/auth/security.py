from datetime import datetime, timedelta
from src.crypto.password_hesh import check_master_password
from src.db.models import (
    get_setting_value,
    add_new_data_settings,
    delete_settings_by_key,
    delete_settings_by_all,
    delete_all_applications,
    increment_failed_attempts,
    reset_failed_attempts,
)


def check_bruteforce_protection(lock_until_str):
    """Если 3+ неудачных попыток и нет блокировки — ставит блокировку на 1 час."""
    failed_str = get_setting_value("failed_attempts")
    failed_count = int(failed_str) if failed_str else 0

    if failed_count >= 3 and not lock_until_str:
        lock_until = datetime.now() + timedelta(minutes=1)
        add_new_data_settings("lock_until", lock_until.isoformat())
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


def handle_final_attempts(master_password_hash):
    """Финальные попытки после истечения блокировки. Возвращает пароль или exit."""
    final_str = get_setting_value("final_attempts")
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
            reset_failed_attempts()
            delete_settings_by_key("lock_until")
            delete_settings_by_key("final_attempts")
            return input_pass

        final_left -= 1
        delete_settings_by_key("final_attempts")
        if final_left > 0:
            add_new_data_settings("final_attempts", str(final_left))
        print("Пароль неверный ❌\n")

    delete_settings_by_all()
    delete_all_applications()
    delete_settings_by_key("final_attempts")
    print("Все попытки исчерпаны. Данные удалены. Программа завершена.")
    exit()


def handle_regular_login(master_password_hash):
    """Обычный вход с 4 попытками. Возвращает пароль или exit."""
    failed_str = get_setting_value("failed_attempts")
    failed_count = int(failed_str) if failed_str else 0

    count = 4 - failed_count
    if count <= 0:
        count = 4
        reset_failed_attempts()

    while count > 0:
        input_pass = input("Введите ваш мастер пароль: ")

        if not input_pass.strip():
            print("❌ Пароль не может быть пустым!\n")
            continue

        if check_master_password(input_pass, master_password_hash):
            print("Пароль верный✅")
            reset_failed_attempts()
            return input_pass

        count -= 1
        increment_failed_attempts()

        if count == 2:
            help_hint = get_setting_value("help_pass")
            print(f"\nПодсказка❗ {help_hint}")

        if count == 0:
            lock_until = datetime.now() + timedelta(minutes=1)
            add_new_data_settings("lock_until", lock_until.isoformat())
            print("Вы истратили все попытки. Попробуйте через 1 час.")
            exit()

        print(f"Пароль неверный ❌ - Осталось попыток: {count}\n")

    return None
