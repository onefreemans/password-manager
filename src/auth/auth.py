from src.crypto.password_hash import hash_master_password
from src.db.models import get_setting_value, add_new_data_settings
from src.auth.security import (
    check_bruteforce_protection,
    check_lockout,
    handle_final_attempts,
    handle_regular_login,
)


def create_master_password(password_db):
    """Создание нового мастер-пароля."""
    print("\nМастер-пароль не задан.")
    while True:
        input_master_password = input("Введите ваш новый мастер пароль: ")
        if len(input_master_password) >= 9:
            hash_password = hash_master_password(input_master_password)
            add_new_data_settings("master_password", hash_password, password_db)

            help_pass = input("Введите подсказку для пароля: ")
            add_new_data_settings("help_pass", help_pass, password_db)

            print("Мастер-пароль добавлен успешно!")
            return input_master_password
        else:
            print("\nПароль должен быть не менее 9 символов!\n")


def verify_master_password(password_db):
    """Проверка мастер-пароля при входе."""
    master_password_hash = get_setting_value("master_password", password_db)
    lock_until_str = get_setting_value("lock_until", password_db)

    check_bruteforce_protection(lock_until_str, password_db)

    if lock_until_str:
        if check_lockout(lock_until_str):
            exit()
        return handle_final_attempts(master_password_hash, password_db)

    return handle_regular_login(master_password_hash, password_db)
