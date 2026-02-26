import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import hashlib
import base64

load_dotenv()

class SecureConfig:
    def __init__(self):
        self._validate_environment()
        self._init_encryption()
    
    def _validate_environment(self):
        # В разработке можно без обязательных переменных
        pass
    
    def _init_encryption(self):
        key = base64.urlsafe_b64encode(
            hashlib.sha256(os.getenv('ENCRYPTION_KEY', 'default-key-32-chars-minimum!!').encode()).digest()
        )
        self.cipher = Fernet(key)
    
    def get(self, key: str, default: any = None) -> any:
        return os.getenv(key, default)
    
    def get_database_url(self) -> str:
        """Возвращает URL базы данных"""
        # Если есть DATABASE_URL в окружении - используем его
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
        # Иначе используем SQLite
        return 'sqlite+aiosqlite:///./gifts.db'
    
    def is_production(self) -> bool:
        return os.getenv('APP_ENV', 'development').lower() == 'production'

config = SecureConfig()
DATABASE_URL = config.get_database_url()
