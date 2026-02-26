from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import random

from config import Config
config = Config()
from database import *
import admin_routes

# Создаем папки для загрузок
os.makedirs("uploads/cases", exist_ok=True)
os.makedirs("uploads/items", exist_ok=True)

app = FastAPI(title="Gifts Battle", description="Сайт с кейсами", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Подключаем админку
app.include_router(admin_routes.router, prefix="/admin")

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Страница админки
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# API: получить все кейсы
@app.get("/api/cases")
async def get_cases():
    cases = await get_all_cases(active_only=True)
    result = []
    for case in cases:
        items = await get_case_items(case.id)
        result.append({
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "price": case.price,
            "image_url": case.image_url or "/static/default-case.png",
            "background_color": case.background_color,
            "items_count": len(items)
        })
    return {"cases": result}

# API: открыть кейс
@app.post("/api/cases/{case_id}/open")
async def open_case_api(case_id: int, request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    result = await open_case(user_id, case_id, is_test=False)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

# API: последние открытия
@app.get("/api/recent-openings")
async def get_recent_openings_api(limit: int = 20):
    openings = await get_recent_openings(limit)
    result = []
    for opening in openings:
        result.append({
            "username": opening.user.username if opening.user else "Аноним",
            "case_name": opening.case.name if opening.case else "Кейс",
            "item_name": opening.item.name if opening.item else "Предмет",
            "win_amount": opening.win_amount,
            "created_at": opening.created_at.isoformat() if opening.created_at else ""
        })
    return {"openings": result}

# API: пользователь
@app.post("/api/user")
async def get_or_create_user(request: Request):
    data = await request.json()
    username = data.get("username", f"user_{random.randint(1000, 9999)}")
    
    user = await get_user_by_username(username)
    
    if not user:
        user = await create_user(
            username=username,
            ip=request.client.host if request.client else None
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "balance": float(user.balance),
        "is_premium": user.is_premium,
        "is_admin": user.is_admin
    }

# Проверка здоровья
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ База данных готова")
    print("✅ Сервер запущен")
