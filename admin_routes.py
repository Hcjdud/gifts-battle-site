from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
from datetime import datetime

from database import *
from security import security

router = APIRouter()

# Простая защита админки (для демо)
async def verify_admin(request: Request):
    # В реальном проекте тут проверка сессии
    return True

# Получить все кейсы
@router.get("/cases")
async def get_cases_list(admin=Depends(verify_admin)):
    cases = await get_all_cases(active_only=False)
    result = []
    for case in cases:
        items = await get_case_items(case.id)
        result.append({
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "price": case.price,
            "image_url": case.image_url,
            "is_active": case.is_active,
            "items_count": len(items),
            "total_probability": sum(i.probability for i in items)
        })
    return {"cases": result}

# Создать кейс
@router.post("/cases/create")
async def create_new_case(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    background_color: str = Form("#1a1a1a"),
    sort_order: int = Form(0),
    image: UploadFile = File(None),
    admin=Depends(verify_admin)
):
    image_url = None
    if image and image.filename:
        ext = image.filename.split(".")[-1]
        filename = f"case_{uuid.uuid4()}.{ext}"
        filepath = f"uploads/cases/{filename}"
        
        os.makedirs("uploads/cases", exist_ok=True)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/uploads/cases/{filename}"
    
    case = await create_case(
        name=name,
        description=description,
        price=price,
        image_url=image_url or "/static/default-case.png",
        background_color=background_color,
        sort_order=sort_order
    )
    
    return {"success": True, "case_id": case.id}

# Удалить кейс
@router.delete("/cases/{case_id}")
async def delete_case_route(case_id: int, admin=Depends(verify_admin)):
    await delete_case(case_id)
    return {"success": True}

# Получить предметы кейса
@router.get("/cases/{case_id}/items")
async def get_case_items_route(case_id: int, admin=Depends(verify_admin)):
    items = await get_case_items(case_id)
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "image_url": item.image_url,
            "value": item.value,
            "probability": item.probability,
            "rarity": item.rarity,
            "color": item.color
        })
    return {"items": result}

# Добавить предмет
@router.post("/cases/{case_id}/items/add")
async def add_item_to_case(
    case_id: int,
    name: str = Form(...),
    value: float = Form(...),
    probability: float = Form(...),
    rarity: str = Form("common"),
    description: str = Form(None),
    color: str = Form("#ffffff"),
    image: UploadFile = File(None),
    admin=Depends(verify_admin)
):
    image_url = None
    if image and image.filename:
        ext = image.filename.split(".")[-1]
        filename = f"item_{uuid.uuid4()}.{ext}"
        filepath = f"uploads/items/{filename}"
        
        os.makedirs("uploads/items", exist_ok=True)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/uploads/items/{filename}"
    
    item = await add_case_item(
        case_id=case_id,
        name=name,
        value=value,
        probability=probability,
        image_url=image_url,
        description=description,
        rarity=rarity,
        color=color
    )
    
    return {"success": True, "item_id": item.id}

# Удалить предмет
@router.delete("/items/{item_id}")
async def delete_item_route(item_id: int, admin=Depends(verify_admin)):
    await delete_case_item(item_id)
    return {"success": True}

# Выдать баланс
@router.post("/users/{user_id}/balance")
async def add_user_balance(
    user_id: int,
    amount: float = Form(...),
    description: str = Form(None),
    admin=Depends(verify_admin)
):
    result = await update_balance(user_id, amount, "admin")
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "new_balance": result["new_balance"]}
