from src.crypto.password_hash import hash_master_password, check_master_password
from src.crypto.password_encrypt import encrypt_password, decrypt_password
from unittest.mock import patch
from datetime import datetime, timedelta
import sqlite3, pytest, tempfile, os


class TestHashEncrypt:
    """Тестирование шифрования и проверки паролей"""
    def test_hash_and_check(self):
        password = "my_secret_123"

        # Хэшируем
        hashed = hash_master_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt-хэш начинается с версии

        # Верный пароль проходит
        assert check_master_password(password, hashed) == True

        # неверный пароль не проходит
        assert check_master_password("wrong_password", hashed) == False

        # Два хэша одного пароля - разные (из-за соли)
        hashed2 = hash_master_password(password)
        assert hashed != hashed2


    def test_encrypt_decrypt_cycle(self):
        master_password = "master_secret_123"
        site_password = "my_site_password_456"

        encrypted = encrypt_password(site_password, master_password)

        # Результат - строка и не равен исходному паролю
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != site_password

        # Расшифровываем
        decrypted = decrypt_password(encrypted, master_password)
        assert decrypted == site_password

        # C другим мастер-паролем не расшифруется
        from cryptography.fernet import InvalidToken
        try:
            decrypt_password(encrypted, "wrong_master")
            assert False, "Должна быть ошибка расшифровки"
        except InvalidToken:
            pass


class TestSecurity:
    """Тесты безопасности: блокировки, финальные попытки, пароль БД."""

    # ======================== БЛОКИРОВКА ПОСЛЕ 3 ПОПЫТОК ========================

    @patch("src.auth.security.exit")
    @patch("src.auth.security.add_new_data_settings")
    @patch("src.auth.security.get_setting_value")
    def test_bruteforce_sets_lockout(self, mock_get, mock_add, mock_exit):
        """После 3 неудачных попыток и без блокировки - ставится lock_until."""
        mock_get.side_effect = lambda key, _: "3" if key == "failed_attempts" else None
        from src.auth.security import check_bruteforce_protection

        check_bruteforce_protection(lock_until_str=None, password_db="test")

        mock_add.assert_called_once()
        assert mock_add.call_args[0][0] == "lock_until"
        mock_exit.assert_called_once()


    @patch("src.auth.security.exit")
    @patch("src.auth.security.add_new_data_settings")
    @patch("src.auth.security.get_setting_value")
    def test_bruteforce_no_lockout_if_already_locked(self, mock_get, mock_add, mock_exit):
        """Если блокировка уже есть - повторно не ставится."""
        mock_get.side_effect = lambda key, _: "3" if key == "failed_attempts" else "exists"
        from src.auth.security import check_bruteforce_protection

        check_bruteforce_protection(lock_until_str="exists", password_db="test")

        mock_add.assert_not_called()
        mock_exit.assert_not_called()


    @patch("src.auth.security.exit")
    @patch("src.auth.security.add_new_data_settings")
    @patch("src.auth.security.get_setting_value")
    def test_bruteforce_no_lockout_low_attempts(self, mock_get, mock_add, mock_exit):
        """Если попыток меньше 3 - блокировка не ставится."""
        mock_get.side_effect = lambda key, _: "2" if key == "failed_attempts" else None
        from src.auth.security import check_bruteforce_protection

        check_bruteforce_protection(lock_until_str=None, password_db="test")

        mock_add.assert_not_called()
        mock_exit.assert_not_called()

    # ======================== ПРОВЕРКА БЛОКИРОВКИ ========================

    def test_check_lockout_active(self):
        """Активная блокировка - возвращает True."""
        future = (datetime.now() + timedelta(hours=1)).isoformat()
        from src.auth.security import check_lockout

        assert check_lockout(future) is True


    def test_check_lockout_expired(self):
        """Истекшая блокировка - возвращает False."""
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        from src.auth.security import check_lockout

        assert check_lockout(past) is False


    def test_check_lockout_none(self):
        """Нет блокировки - возвращает False."""
        from src.auth.security import check_lockout

        assert check_lockout(None) is False

    # ======================== ФИНАЛЬНЫЕ ПОПЫТКИ ========================

    @patch("builtins.input")
    @patch("src.auth.security.reset_failed_attempts")
    @patch("src.auth.security.delete_settings_by_key")
    @patch("src.auth.security.check_master_password")
    @patch("src.auth.security.get_setting_value")
    def test_final_attempts_success(self, mock_get, mock_check, mock_del, mock_reset, mock_input):
        """Успешный вход в финальных попытках."""
        mock_get.side_effect = lambda key, _: "2" if key == "final_attempts" else None
        mock_check.return_value = True
        mock_input.return_value = "password"
        from src.auth.security import handle_final_attempts

        result = handle_final_attempts("hash", "test_db")

        assert result == "password"
        mock_reset.assert_called_once()
        assert mock_del.call_count == 2


    @patch("builtins.input")
    @patch("src.auth.security.exit")
    @patch("src.auth.security.os.remove")
    @patch("src.auth.security.add_new_data_settings")
    @patch("src.auth.security.delete_settings_by_key")
    @patch("src.auth.security.check_master_password")
    @patch("src.auth.security.get_setting_value")
    def test_final_attempts_exhausted(
        self, mock_get, mock_check, mock_del_key, mock_add, mock_remove, mock_exit, mock_input
    ):
        """Все финальные попытки исчерпаны - данные удаляются с диска."""
        mock_get.side_effect = lambda key, _: "2" if key == "final_attempts" else None
        mock_check.return_value = False
        mock_input.return_value = "wrong"
        from src.auth.security import handle_final_attempts

        handle_final_attempts("hash", "test_db")

        assert mock_remove.call_count == 2
        mock_exit.assert_called_once()

    # ======================== ПАРОЛЬ БД (JSON) ========================

    @patch("builtins.input")
    @patch("src.auth.db_auth._save_auth")
    @patch("src.auth.db_auth._load_auth")
    @patch("src.crypto.password_hash.check_master_password")
    def test_verify_password_db_success(self, mock_check, mock_load, mock_save, mock_input):
        """Верный пароль БД - возвращает пароль, сбрасывает счётчик."""
        mock_load.return_value = {
            "db_password_hash": "hashed",
            "failed_attempts": 0,
            "lock_until": None,
        }
        mock_check.return_value = True
        mock_input.return_value = "db_pass"
        from src.auth.db_auth import verify_password_db

        result = verify_password_db()

        assert result == "db_pass"
        mock_save.assert_called_with(
            {"db_password_hash": "hashed", "failed_attempts": 0, "lock_until": None}
        )


    @patch("builtins.input")
    @patch("src.auth.db_auth.os.remove")
    @patch("src.auth.db_auth.exit")
    @patch("src.auth.db_auth._save_auth")
    @patch("src.auth.db_auth._load_auth")
    @patch("src.crypto.password_hash.check_master_password")
    def test_verify_password_db_lockout(
        self, mock_check, mock_load, mock_save, mock_exit, mock_remove, mock_input
    ):
        """4 неверных попытки - блокировка БД."""
        mock_load.return_value = {
            "db_password_hash": "hashed",
            "failed_attempts": 0,
            "lock_until": None,
        }
        mock_check.return_value = False
        mock_input.return_value = "wrong"
        from src.auth.db_auth import verify_password_db

        verify_password_db()

        last_call_args = mock_save.call_args_list[-1][0][0]
        assert last_call_args["lock_until"] is not None
        mock_exit.assert_called()


    @patch("builtins.input")
    @patch("src.auth.db_auth.os.remove")
    @patch("src.auth.db_auth.exit")
    @patch("src.auth.db_auth._save_auth")
    @patch("src.auth.db_auth._load_auth")
    @patch("src.crypto.password_hash.check_master_password")
    def test_verify_password_db_final_attempts_exhausted(
        self, mock_check, mock_load, mock_save, mock_exit, mock_remove, mock_input
    ):
        """Финальные попытки БД исчерпаны - программа завершается."""
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        mock_load.return_value = {
            "db_password_hash": "hashed",
            "failed_attempts": 0,
            "lock_until": past,
        }
        mock_check.return_value = False
        mock_input.return_value = "wrong"
        from src.auth.db_auth import verify_password_db

        verify_password_db()

        mock_exit.assert_called()


@pytest.fixture
def temp_db():
    """Создаёт временный файл базы данных и возвращает (путь, функцию подключения)."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT NOT NULL,
            link TEXT DEFAULT 'Не добавлен.',
            login TEXT NOT NULL,
            password_encryption TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    def _get_db(password_db=None):
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    yield path, _get_db

    os.unlink(path)


class TestModels:
    """Тесты моделей: CRUD-операции с БД."""

    def test_add_new_data(self, temp_db):
        """Добавление записи - запись появляется в таблице."""
        path, get_db = temp_db

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import add_new_data
            add_new_data("Test", "test.com", "login", "encrypted_pass", password_db="test")

        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE site_name = 'Test'")
        row = cursor.fetchone()
        assert row is not None
        assert row["site_name"] == "Test"
        assert row["link"] == "test.com"
        assert row["login"] == "login"
        assert row["password_encryption"] == "encrypted_pass"
        conn.close()

    def test_get_all_applications(self, temp_db):
        """Получение всех записей - возвращает список."""
        path, get_db = temp_db

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO applications (site_name, link, login, password_encryption) VALUES (?, ?, ?, ?)",
            ("Site1", "link1", "log1", "pass1"),
        )
        cursor.execute(
            "INSERT INTO applications (site_name, link, login, password_encryption) VALUES (?, ?, ?, ?)",
            ("Site2", "link2", "log2", "pass2"),
        )
        conn.commit()
        conn.close()

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import get_all_applications
            result = get_all_applications("test")

            assert len(result) == 2
            assert result[0]["site_name"] == "Site1"
            assert result[1]["site_name"] == "Site2"

    def test_get_all_applications_empty(self, temp_db):
        """Пустая таблица - возвращает пустой список."""
        _, get_db = temp_db

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import get_all_applications
            result = get_all_applications("test")

            assert result == []

    def test_search_application_by_site_found(self, temp_db):
        """Поиск по подстроке - находит совпадения."""
        path, get_db = temp_db

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO applications (site_name, link, login, password_encryption) VALUES (?, ?, ?, ?)",
            ("Yandex", "ya.ru", "log", "pass"),
        )
        cursor.execute(
            "INSERT INTO applications (site_name, link, login, password_encryption) VALUES (?, ?, ?, ?)",
            ("Yahoo", "yahoo.com", "log2", "pass2"),
        )
        conn.commit()
        conn.close()

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import search_application_by_site
            result = search_application_by_site("yan", "test")

            assert len(result) == 1
            assert result[0]["site_name"] == "Yandex"

    def test_search_application_by_site_not_found(self, temp_db):
        """Поиск по несуществующей подстроке - пустой список."""
        _, get_db = temp_db

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import search_application_by_site
            result = search_application_by_site("nonexistent", "test")

            assert result == []

    def test_delete_application_by_id_success(self, temp_db):
        """Удаление существующей записи - возвращает True."""
        path, get_db = temp_db

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO applications (site_name, link, login, password_encryption) VALUES (?, ?, ?, ?)",
            ("Site", "link", "log", "pass"),
        )
        conn.commit()
        conn.close()

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import delete_application_by_id
            result = delete_application_by_id(1, "test")

            assert result is True

        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = 1")
        assert cursor.fetchone() is None
        conn.close()

    def test_delete_application_by_id_not_found(self, temp_db):
        """Удаление несуществующей записи - возвращает False."""
        _, get_db = temp_db

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import delete_application_by_id
            result = delete_application_by_id(999, "test")

            assert result is False

    def test_get_setting_value_exists(self, temp_db):
        """Получение существующей настройки - возвращает значение."""
        path, get_db = temp_db

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("test_key", "test_value"),
        )
        conn.commit()
        conn.close()

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import get_setting_value
            result = get_setting_value("test_key", "test")

            assert result == "test_value"

    def test_get_setting_value_not_exists(self, temp_db):
        """Получение несуществующей настройки - возвращает None."""
        _, get_db = temp_db

        with patch("src.db.models.get_db", side_effect=get_db):
            from src.db.models import get_setting_value
            result = get_setting_value("nonexistent", "test")

            assert result is None