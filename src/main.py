from src.menu_handlers import (
    handle_add,
    handle_show_all,
    handle_search,
    handle_delete,
    clear_db,
)
from src.db.database import init_db
from src.auth.auth import create_master_password, verify_master_password
from src.db.models import get_setting_value


def main():
    """Создает мастер пароль или проверяет его на правильность"""
    init_db()
    if not get_setting_value("master_password"):
        input_master_password = create_master_password()
        show_menu(input_master_password)

    else:
        input_master_password = verify_master_password()
        show_menu(input_master_password)


def break_menu_and_exit(input_master_password):
    """Определяет вернуться ли после вызова в меню или нет"""
    number_menu = input("\nВернутся в меню?(Что угодно - да|0 - выход: ")
    match number_menu:
        case "0":
            exit()

        case _:
            show_menu(input_master_password)


def show_menu(input_master_password):
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
                handle_add(input_master_password)
                break_menu_and_exit(input_master_password)

            case 2:
                handle_show_all(input_master_password)
                break_menu_and_exit(input_master_password)

            case 3:
                handle_search(input_master_password)
                break_menu_and_exit(input_master_password)

            case 4:
                handle_delete()
                break_menu_and_exit(input_master_password)

            case 5:
                clear_db()
                break_menu_and_exit(input_master_password)

            case 0:
                exit()


if __name__ == "__main__":
    main()
