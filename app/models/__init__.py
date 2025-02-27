from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    wardrobe_items = relationship("WardrobeItem", back_populates="owner", cascade="all, delete-orphan")
    outfits = relationship("Outfit", back_populates="owner", cascade="all, delete-orphan")

class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="wardrobe_items")

class Outfit(Base):
    __tablename__ = "outfits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    occasion = Column(String(50), nullable=False)
    weather = Column(String(50), nullable=True)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="outfits")
