from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import base64


def _base64_32bit(master_password):
    """приводит master_password в требуемый вид для cryptography"""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(master_password.encode())
    key = base64.urlsafe_b64encode(digest.finalize())
    cipher_suite = Fernet(key)
    return cipher_suite


def encrypt_password(enter_password, master_password):
    """Шифрует пароль с помощью ключа из мастер-пароля и возвращает зашифрванный текст (str)"""
    cipher_suite = _base64_32bit(master_password)

    encrypted_text = cipher_suite.encrypt(enter_password.encode())
    return encrypted_text.decode("utf-8")


def decrypt_password(password_encryption, master_password):
    """Дешифровывает шифротекст и возвращает текст (str)"""
    cipher_suite = _base64_32bit(master_password)

    decrypted_text = cipher_suite.decrypt(password_encryption.encode("utf-8"))
    return decrypted_text.decode("utf-8")
