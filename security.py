import secrets
import hashlib
import time
from fastapi import Request, HTTPException

class SecurityManager:
    def __init__(self):
        self.rate_limit_store = {}
        self.banned_ips = set()
    
    def check_rate_limit(self, key: str, max_requests: int = 100, period: int = 60) -> bool:
        now = time.time()
        if key not in self.rate_limit_store:
            self.rate_limit_store[key] = []
        
        self.rate_limit_store[key] = [t for t in self.rate_limit_store[key] if now - t < period]
        
        if len(self.rate_limit_store[key]) >= max_requests:
            return False
        
        self.rate_limit_store[key].append(now)
        return True
    
    def generate_csrf_token(self) -> str:
        return secrets.token_urlsafe(32)

security = SecurityManager()

class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Rate limiting по IP
        ip = request.client.host if request.client else "0.0.0.0"
        if not security.check_rate_limit(ip):
            raise HTTPException(status_code=429, detail="Too many requests")
        
        # Проверка на бан
        if ip in security.banned_ips:
            raise HTTPException(status_code=403, detail="IP banned")
        
        response = await call_next(request)
        return response
