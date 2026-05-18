# 🔐 Локальный менеджер паролей

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

Локальный менеджер паролей с защитой мастер-паролем, шифрованием данных и защитой от брутфорса.

---

## 🛠 Возможности

- **Мастер-пароль** — хеширование bcrypt, подсказка для восстановления
- **Шифрование паролей** — Fernet (cryptography), ключ из мастер-пароля через SHA-256
- **CRUD записей** — добавление, просмотр, поиск по сайту, удаление по ID
- **Защита от брутфорса** — 4 попытки → блокировка на 1 час → 2 финальные попытки → удаление данных
- **Счётчики между перезапусками** — попытки и блокировка сохраняются в SQLite
- **Очистка базы** — полное удаление всех данных с подтверждением мастер-паролем

---

## 🚀 Установка

### 1. Клонируй репозиторий
```bash
git clone https://github.com/OneFreemans/password-manager.git
cd password-manager
```
---
### 2. Создай виртуальное окружение
```bash
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```
---
### 3. Установи зависимости
```bash
pip install -r requirements.txt
```
---
### 4. Запуск
```bash
python src/main.py
```

---

## 📁 Структура проекта

```
password-manager/
├── src/
│   ├── main.py              # точка входа, меню
│   ├── menu_handlers.py     # обработчики пунктов меню
│   ├── auth/
│   │   ├── auth.py          # оркестратор авторизации
│   │   └── security.py      # защита: попытки, блокировки, брутфорс
│   ├── crypto/
│   │   ├── password_hesh.py # bcrypt: хеш и проверка
│   │   └── password_encrypt.py # Fernet: шифрование/расшифровка
│   └── db/
│       ├── database.py      # подключение к SQLite, создание таблиц
│       └── models.py        # CRUD-запросы к базе
└── requirements.txt
```

---

## 🧠 Технологии

| Библиотека | Назначение |
|---|---|
| `bcrypt` | Хеширование мастер-пароля |
| `cryptography` | Шифрование паролей сайтов |
| `sqlite3` | Локальное хранение данных |

---

## 📄 Лицензия

MIT

---

## ✍️ Автор

**OneFreemans** — [GitHub](https://github.com/OneFreemans)
