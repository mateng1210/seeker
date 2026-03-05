from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT token并返回payload
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def get_user_from_token(token: str, db_session) -> Optional[object]:
    """
    从token中解析用户信息并从数据库获取用户对象
    这是一个通用的函数，可以在任何需要验证用户的地方使用
    """
    from sqlalchemy import select
    from app.models import User

    try:
        payload = decode_access_token(token)
        if payload is None:
            return None

        email: str = payload.get("sub")
        if email is None:
            return None

        # 从数据库查询用户
        result = db_session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user
    except Exception:
        return None
