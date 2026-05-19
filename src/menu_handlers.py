from src.crypto.password_encrypt import encrypt_password, decrypt_password
from src.crypto.password_hash import check_master_password
from datetime import datetime, timedelta
from src.auth.db_auth import JSON_PATH
from src.db.database import DB_PATH
import os
from src.db.models import (
    delete_application_by_id,
    add_new_data,
    get_all_applications,
    search_application_by_site,
    get_setting_value,
    add_new_data_settings,
)


def handle_add(master_password, password_db):
    """Добавляет новые записи в базу данных"""
    print("Укажите следующие данные")
    site_name = input("Название сайта\приложения: ")
    link = input("Ссылка на сайт\приложение: ")
    link = link if link else "Не добавлен."
    login = input("Логин для входа: ")
    password = input("Пароль для входа: ")

    password_encryption = encrypt_password(password, master_password)
    add_new_data(site_name, link, login, password_encryption, password_db)

    print("Данные добавлены")


def handle_show_all(master_password, password_db):
    """Выводит все имеющиеся записи и их информацию из базы данных"""
    all_data = get_all_applications(password_db)
    if all_data:
        for data in all_data:
            id_data = data["id"]
            site_name = data["site_name"]
            link = data["link"]
            login = data["login"]
            password = decrypt_password(data["password_encryption"], master_password)

            print(f"""
==============| ID-{id_data}. {site_name} |=================
Сайт: {link}
Логин: {login}
Пароль: {password}
""")

    else:
        print("Нет сохранённых записей")


def handle_search(master_password, password_db):
    """Поиск по базе данныx с помощью названия сайта"""
    site_name = input("Введите название сайта: ")
    search_data = search_application_by_site(site_name, password_db)

    if not search_data:
        print("Ничего не найдено")
        return

    for data in search_data:
        id_data = data["id"]
        site_name = data["site_name"]
        link = data["link"]
        login = data["login"]
        password = decrypt_password(data["password_encryption"], master_password)

        print(f"""
==============| ID-{id_data}. {site_name} |=================
Сайт: {link}
{login}
{password}
""")


def handle_delete(password_db):
    """Удалить данные из базы данных, используя идентификатор(id)"""
    try:
        id_to_del = int(input("ID записи для удаления (0 - отмена): "))
    except ValueError:
        print("❌ Допустимы только цифры")
        return

    if id_to_del == 0:
        print("Удаление отменено.")

    else:
        if delete_application_by_id(id_to_del, password_db):
            print("Запись удалена.")

        else:
            print("Ошибка при попытке удалить запись.")


def clear_db(password_db): #TODO: вырезать проверку и блокировку в отдельную функцию
    """Очистка всей базы данных. Требует мастер-пароль с одной попытки."""
    print(
        "==!!!ВНИМАНИЕ!!!== Все данные будут безвозвратно удалены! ==!!!ВНИМАНИЕ!!!=="
    )
    confirm = input("Вы уверены? (y/n): ").lower()
    if confirm != "y":
        print("Удаление отменено.")
        return

    master_password_hash = get_setting_value("master_password", password_db)
    input_pass = input("Введите мастер-пароль для подтверждения: ")
    if not input_pass.strip():
        print("❌ Пароль не может быть пустым!\n")
        return

    elif check_master_password(input_pass, master_password_hash):
        os.remove(DB_PATH)
        os.remove(JSON_PATH)
        print("База данных полностью удалена. Программа завершена.")
        exit()

    lock_until = datetime.now() + timedelta(hours=1) #TODO: блокировка
    add_new_data_settings("lock_until", lock_until.isoformat(), password_db)
    print("Неверный пароль! Доступ заблокирован на 1 час.")
    exit()
