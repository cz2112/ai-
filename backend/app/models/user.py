# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # 邮箱是否已验证
    created_at = Column(DateTime, default=datetime.now)

    # 基础关系（只保留最基本的）
    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    # courses = relationship("Course", back_populates="user")
    tags = relationship("Tag", back_populates="user")