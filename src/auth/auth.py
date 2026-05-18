from src.crypto.password_hesh import hash_master_password
from src.db.models import get_setting_value, add_new_data_settings
from src.auth.security import (
    check_bruteforce_protection,
    check_lockout,
    handle_final_attempts,
    handle_regular_login,
)


def create_master_password():
    """Создание нового мастер пароль."""
    print("Мастер-пароль не задан.")
    while True:
        input_master_password = input("Введите ваш новый мастер пароль: ")
        if len(input_master_password) >= 5:
            hash_password = hash_master_password(input_master_password)
            add_new_data_settings("master_password", hash_password)

            help_pass = input("Введите подсказку для пароля: ")
            add_new_data_settings("help_pass", help_pass)

            print("Мастер-пароль добавлен успешно!")
            return input_master_password

        else:
            print("\nПароль должен быть не менее 5 символов❗\n")


def verify_master_password():
    """Проверка мастер-пароля при входе."""
    master_password_hash = get_setting_value("master_password")
    lock_until_str = get_setting_value("lock_until")

    check_bruteforce_protection(lock_until_str)

    if lock_until_str:
        if check_lockout(lock_until_str):
            exit()
        return handle_final_attempts(master_password_hash)

    return handle_regular_login(master_password_hash)
