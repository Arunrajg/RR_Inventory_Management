import random
import string
from cryptography.fernet import Fernet

# Generate a key and store it securely


def generate_key():
    return Fernet.generate_key()

# Encrypt a message


def encrypt_message(message: str, key: bytes) -> bytes:
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message

# Decrypt a message


def decrypt_message(encrypted_message: bytes, key: bytes) -> str:
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_message).decode()
    return decrypted_message


def generate_random_password(length=10):
    special_characters = "!@#$%^&*-_="
    characters = string.ascii_letters + string.digits + special_characters
    return ''.join(random.choice(characters) for _ in range(length))

# If you want to generate a key, you can run this separately and store the key securely
# key = generate_key()
# print(key)
