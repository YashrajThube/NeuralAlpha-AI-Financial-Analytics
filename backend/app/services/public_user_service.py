from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

PUBLIC_USER_EMAIL = 'public@neuralalpha.local'


class PublicUserService:
    @staticmethod
    async def get_or_create(db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.email == PUBLIC_USER_EMAIL))
        user = result.scalar_one_or_none()
        if user is not None:
            return user

        user = User(
            name='Public User',
            email=PUBLIC_USER_EMAIL,
            password_hash='public-access-no-password',
            role='user',
        )
        db.add(user)
        flush = getattr(db, 'flush', None)
        if callable(flush):
            await flush()
        return user
