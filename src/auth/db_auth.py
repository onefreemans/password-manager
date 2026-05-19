import json
import os
from datetime import datetime, timedelta
from src.db.database import DB_PATH

JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "auth.json")


def _load_auth():
    """Загружает данные из auth.json. Возвращает словарь или пустой словарь."""
    if not os.path.exists(JSON_PATH):
        return {}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_auth(data):
    """Сохраняет данные в auth.json."""
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_password_db():
    """Создаёт пароль для шифрования базы данных. Возвращает пароль."""
    print("Создание пароля для шифрования базы данных.")
    while True:
        password = input("Введите пароль для шифрования БД: ")
        if len(password) >= 3:
            from src.crypto.password_hash import hash_master_password

            hashed = hash_master_password(password)

            _save_auth(
                {
                    "db_password_hash": hashed,
                    "failed_attempts": 0,
                    "lock_until": None,
                }
            )
            print("Пароль для БД создан успешно!")
            return password
        else:
            print("\nПароль должен быть не менее 3 символов!\n")


def verify_password_db():
    """Проверяет пароль БД. Возвращает пароль или завершает программу."""
    from src.crypto.password_hash import check_master_password

    auth = _load_auth()
    db_password_hash = auth.get("db_password_hash")
    failed_count = auth.get("failed_attempts", 0)
    lock_until_str = auth.get("lock_until")

    # Проверка блокировки
    if lock_until_str:
        lock_until = datetime.fromisoformat(lock_until_str)
        if datetime.now() < lock_until:
            print(f"Доступ к БД заблокирован до {lock_until.strftime('%H:%M:%S')}")
            exit()
        else:
            # Блокировка истекла — финальные попытки
            print("Блокировка БД снята. У вас 2 финальные попытки.")
            for attempt in range(2, 0, -1):
                password = input(f"[{attempt}/2] Введите пароль БД: ")
                if check_master_password(password, db_password_hash):
                    _save_auth({**auth, "failed_attempts": 0, "lock_until": None})
                    return password
                print("Неверный пароль БД.\n")
            print("Финальные попытки исчерпаны. Все данные удалены.")
            os.remove(DB_PATH)
            os.remove(JSON_PATH)
            exit()

    # Обычная проверка
    count = 4 - failed_count
    if count <= 0:
        count = 4
        _save_auth({**auth, "failed_attempts": 0})

    while count > 0:
        password = input("Введите пароль БД: ")
        if not password.strip():
            print("❌ Пароль не может быть пустым!\n")
            continue

        if check_master_password(password, db_password_hash):
            _save_auth({**auth, "failed_attempts": 0, "lock_until": None})
            return password

        count -= 1
        auth["failed_attempts"] = auth.get("failed_attempts", 0) + 1
        _save_auth(auth)

        if count == 0:
            lock_until = datetime.now() + timedelta(hours=1) #TODO: блокировка
            _save_auth({**auth, "lock_until": lock_until.isoformat()})
            print("Неверный пароль БД. Доступ заблокирован на 1 час.")
            exit()

        print(f"Неверный пароль БД ❌ Осталось попыток: {count}\n")

    return None
