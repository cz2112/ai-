import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 强制使用 SQLite 数据库（文件保存在 backend 目录下）
DATABASE_URL = "sqlite:///./smart_study.db"

# SQLite 特殊配置
connect_args = {"check_same_thread": False}

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()