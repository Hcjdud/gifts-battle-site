from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, func
from datetime import datetime
import random

from models import Base, User, Case, CaseItem, CaseOpening, Transaction

# Используем SQLite
DATABASE_URL = "sqlite+aiosqlite:///./gifts.db"

engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных готова")

# ===== ПОЛЬЗОВАТЕЛИ =====
async def get_user(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

async def get_user_by_username(username: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

async def create_user(username: str, ip: str = None):
    async with AsyncSessionLocal() as session:
        user = User(
            username=username, 
            ip_address=ip, 
            last_seen=datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def update_balance(user_id: int, amount: float):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return None
        
        user.balance += amount
        user.last_seen = datetime.utcnow()
        
        tx = Transaction(
            user_id=user_id,
            amount=amount,
            type="admin"
        )
        session.add(tx)
        
        await session.commit()
        return {"new_balance": user.balance}

async def get_all_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).order_by(User.balance.desc()))
        return result.scalars().all()

# ===== КЕЙСЫ =====
async def create_case(name: str, description: str, price: float, image_url: str):
    async with AsyncSessionLocal() as session:
        case = Case(
            name=name,
            description=description,
            price=price,
            image_url=image_url
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case

async def delete_case(case_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Case).where(Case.id == case_id))
        await session.commit()

async def get_all_cases(active_only: bool = True):
    async with AsyncSessionLocal() as session:
        query = select(Case)
        if active_only:
            query = query.where(Case.is_active == True)
        result = await session.execute(query.order_by(Case.sort_order))
        return result.scalars().all()

# ===== ПРЕДМЕТЫ =====
async def add_case_item(case_id: int, name: str, value: float, probability: float, image_url: str = None):
    async with AsyncSessionLocal() as session:
        item = CaseItem(
            case_id=case_id,
            name=name,
            value=value,
            probability=probability,
            image_url=image_url
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

async def delete_case_item(item_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(CaseItem).where(CaseItem.id == item_id))
        await session.commit()

async def get_case_items(case_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CaseItem).where(CaseItem.case_id == case_id)
        )
        return result.scalars().all()

# ===== ОТКРЫТИЕ КЕЙСОВ =====
async def open_case(user_id: int, case_id: int, is_test: bool = False):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            return {"error": "User not found"}
        
        case = await session.get(Case, case_id)
        if not case or not case.is_active:
            return {"error": "Case not found"}
        
        items = await get_case_items(case_id)
        if not items:
            return {"error": "Case is empty"}
        
        if not is_test and user.balance < case.price:
            return {"error": "Insufficient balance"}
        
        # Выбор предмета
        total_prob = sum(item.probability for item in items)
        rand = random.uniform(0, total_prob)
        cumulative = 0
        selected = items[-1]
        
        for item in items:
            cumulative += item.probability
            if rand <= cumulative:
                selected = item
                break
        
        win_amount = selected.value
        
        if not is_test:
            user.balance -= case.price
            user.balance += win_amount
            user.total_games += 1
            user.total_wins += 1
        
        opening = CaseOpening(
            user_id=user_id,
            case_id=case_id,
            item_id=selected.id,
            win_amount=win_amount,
            is_test=is_test
        )
        session.add(opening)
        
        await session.commit()
        
        return {
            "success": True,
            "item": {
                "id": selected.id,
                "name": selected.name,
                "image_url": selected.image_url,
                "value": win_amount
            },
            "win_amount": win_amount,
            "new_balance": user.balance if not is_test else None
        }

async def get_recent_openings(limit: int = 10):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CaseOpening)
            .where(CaseOpening.is_test == False)
            .order_by(CaseOpening.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
