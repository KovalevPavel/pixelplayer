from passlib.context import CryptContext

# Контекст для хеширования паролей, используем bcrypt
__pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_string_hash(string):
    """Хэширование пароля"""
    return __pwd_context.hash(string)
