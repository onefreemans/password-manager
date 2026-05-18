from bcrypt import gensalt, hashpw, checkpw


def hash_master_password(password):
    """хеширует пароль"""
    if not password:
        return "поле не может быть пустым"

    else:
        bytes_password = password.encode("utf-8")
        salt = gensalt()

        hash_password = hashpw(bytes_password, salt)
        return hash_password.decode("utf-8")


def check_master_password(password, hashed):
    """проверяет хеш пароля и введённый пользователем в поле ввода"""
    if not password:
        return "поле пароль не может быть пустым"

    else:
        bytes_password = password.encode("utf-8")
        bytes_hashed = hashed.encode("utf-8")

        return checkpw(bytes_password, bytes_hashed)
