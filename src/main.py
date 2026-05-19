from src.menu_handlers import (
    handle_add,
    handle_show_all,
    handle_search,
    handle_delete,
    clear_db,
)
from src.auth.auth import create_master_password, verify_master_password
from src.db.database import DB_PATH, init_db
from src.auth.db_auth import create_password_db, verify_password_db
import os


def main():
    """Создает мастер пароль или проверяет его на правильность"""
    if not os.path.exists(DB_PATH):
        input_password_db = create_password_db()
        init_db(input_password_db)
        input_master_password = create_master_password(input_password_db)
        show_menu(input_master_password, input_password_db)

    else:
        input_password_db = verify_password_db()
        init_db(input_password_db)
        input_master_password = verify_master_password(input_password_db)
        show_menu(input_master_password, input_password_db)


def break_menu_and_exit(input_master_password, password_db):
    """Определяет вернуться ли после вызова в меню или нет"""
    number_menu = input("\nВернутся в меню?(Что угодно - да|0 - выход: ")
    match number_menu:
        case "0":
            exit()

        case _:
            show_menu(input_master_password, password_db)


def show_menu(input_master_password, password_db):
    """Меню менеджера паролей"""
    while True:
        print("""
Добро пожаловать в меню!
    
1 — Добавить новую запись
2 — Показать все записи
3 — Найти по сайту
4 - Удалить запись по id
5 - Удаление базы данных
0 — Выйти
    """)
        try:
            number_menu = int(input("Введите номер пункта из списка выше: "))
        except ValueError:
            print("❌ Допустимы только цифры")
            continue

        match number_menu:
            case 1:
                handle_add(input_master_password, password_db)
                break_menu_and_exit(input_master_password, password_db)

            case 2:
                handle_show_all(input_master_password, password_db)
                break_menu_and_exit(input_master_password, password_db)

            case 3:
                handle_search(input_master_password, password_db)
                break_menu_and_exit(input_master_password, password_db)

            case 4:
                handle_delete(password_db)
                break_menu_and_exit(input_master_password, password_db)

            case 5:
                clear_db(password_db)
                break_menu_and_exit(input_master_password, password_db)

            case 0:
                exit()


if __name__ == "__main__":
    main()
