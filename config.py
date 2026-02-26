import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def get_database_url(self) -> str:
        return 'sqlite+aiosqlite:///./gifts.db'
    
    def is_production(self) -> bool:
        return os.getenv('APP_ENV', 'development').lower() == 'production'

config = Config()
