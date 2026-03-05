from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.config import settings

# 设置同步连接池参数
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI.replace('+asyncpg', ''),  # 移除 asyncpg 驱动
    # 连接池配置
    pool_size=20,  # 连接池大小（增加，支持更多并发）
    max_overflow=40,  # 超出 pool_size 后允许的最大连接数（增加）
    pool_timeout=60,  # 获取连接的超时时间（秒）（增加，避免超时）
    pool_recycle=120,  # 连接回收时间（秒）（缩短为 10 分钟，更积极回收）
    pool_pre_ping=True,  # 使用前检查连接是否有效 ⭐ 关键配置
    pool_reset_on_return='rollback',  # 归还连接时重置状态
    echo=False,
)

# 创建同步会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话 - 同步版本"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
