from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, Token, UserResponse, CommonResponse, UserLogin, UserUpdate, UserPWDUpdate
from app.security import verify_password, get_password_hash, create_access_token, decode_access_token
from datetime import timedelta
from app.config import settings
from typing import List

router = APIRouter(prefix="/auth", tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    通用的获取当前用户函数
    使用security.py中的decode_access_token函数解析token
    """
    # 使用通用的错误响应格式
    error_response = CommonResponse[List](code=401, msg="请登录", data=[])

    # 验证token
    payload = decode_access_token(token)
    if payload is None:
        return error_response

    email: str = payload.get("sub")
    if email is None:
        return error_response

    # 查询用户
    result = db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return error_response

    return user


@router.post("/register", response_model=CommonResponse[UserResponse], name='注册', description='用户注册')
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 检查用户是否存在
    result = db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return CommonResponse[UserResponse](
            code=400,
            msg="邮箱已被注册",
            data=None
        )

    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        role=user_data.role,
        nick_name=user_data.nick_name or user_data.email,
        phone=user_data.phone or ''
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return CommonResponse[UserResponse](
        code=200,
        msg="注册成功",
        data=new_user
    )


@router.post("/login", response_model=CommonResponse[Token], name='登录', description='用户登录')
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    result = db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        return CommonResponse[Token](
            code=400,
            msg="邮箱或密码错误",
            data=None
        )

    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    expires_time_seconds = int(access_token_expires.total_seconds())
    return CommonResponse[Token](
        code=200,
        msg="登录成功",
        data=Token(access_token=access_token, expires_in=expires_time_seconds, token_type="bearer")
    )


@router.get("/me", response_model=CommonResponse[UserResponse], name='用户信息', description='获取当前用户信息')
async def read_users_me(current_user: User = Depends(get_current_user)):
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    return CommonResponse[UserResponse](
        code=200,
        msg="获取用户信息成功",
        data=current_user
    )

@router.put("/update", response_model=CommonResponse[UserResponse], name='更新用户信息', description='更新当前用户信息')
async def updateUser(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 检查是否为错误响应
    if isinstance(current_user, CommonResponse):
        return current_user

    if user_update.field not in ['nick_name', 'phone', 'email']:
        return CommonResponse[UserResponse](
            code=400,
            msg="不允许修改该字段",
            data=None
        )
    else:
        if user_update.field == 'email':
            # 验证邮箱格式
            import re

            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

            if not re.match(email_pattern, user_update.value):
                return CommonResponse[UserResponse](
                    code=400,
                    msg="邮箱格式不正确",
                    data=None
                )

            result = db.execute(select(User).where(User.email == user_update.value))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                return CommonResponse[UserResponse](
                    code=400,
                    msg="邮箱已被注册",
                    data=None
                )

        setattr(current_user, user_update.field, user_update.value)

        db.commit()

        return CommonResponse[UserResponse](
            data=None
        )


@router.put("/change_password", response_model=CommonResponse[UserResponse], name='修改密码', description='修改当前用户密码')
async def changePassword(password_data: UserPWDUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if password_data.new_password2 != password_data.new_password1:
        return CommonResponse(code=412, msg="新密码不一致")

    hashed_pw = get_password_hash(password_data.new_password1)
    current_user.hashed_password = hashed_pw
    db.commit()

    return CommonResponse[UserResponse](
        code=200,
        msg="修改密码成功"
    )