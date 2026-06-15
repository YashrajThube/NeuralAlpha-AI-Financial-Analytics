from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenData
from app.services.log_service import LogService


class AuthService:
    @staticmethod
    async def register(payload: RegisterRequest, db: AsyncSession) -> User:
        existing = await db.execute(select(User).where(User.email == payload.email.lower()))
        if existing.scalar_one_or_none() is not None:
            raise AppException('Email already registered', status_code=409)

        user = User(
            name=(payload.name or payload.email.split('@')[0]).strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        db.add(user)
        flush = getattr(db, 'flush', None)
        if callable(flush):
            await flush()
        refresh = getattr(db, 'refresh', None)
        if callable(refresh):
            await refresh(user)
        await LogService.create_log(db, user_id=user.id, action='auth.register', status='success', message='User registered')
        return user

    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession) -> TokenData:
        result = await db.execute(select(User).where(User.email == payload.email.lower()))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(payload.password, user.password_hash):
            await LogService.create_log(db, user_id=None, action='auth.login', status='error', message='Invalid credentials')
            raise AppException('Invalid credentials', status_code=401)

        token = create_access_token(subject=str(user.id), role=user.role)
        await LogService.create_log(db, user_id=user.id, action='auth.login', status='success', message='Login successful')
        return TokenData(access_token=token)
