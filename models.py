from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    balance = Column(Float, default=0.0)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(Text)
    price = Column(Float)
    image_url = Column(String)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    items = relationship("CaseItem", back_populates="case", cascade="all, delete-orphan")

class CaseItem(Base):
    __tablename__ = "case_items"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    name = Column(String)
    image_url = Column(String, nullable=True)
    value = Column(Float)
    probability = Column(Float)
    
    case = relationship("Case", back_populates="items")
    openings = relationship("CaseOpening", back_populates="item")

class CaseOpening(Base):
    __tablename__ = "case_openings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    case_id = Column(Integer, ForeignKey("cases.id"))
    item_id = Column(Integer, ForeignKey("case_items.id"))
    win_amount = Column(Float)
    is_test = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    case = relationship("Case")
    item = relationship("CaseItem")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
