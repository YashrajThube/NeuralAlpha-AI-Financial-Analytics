from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_db

PUBLIC_USER_EMAIL = 'public@neuralalpha.local'


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
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


def require_role(*roles: str):
    async def _role_guard(user: User = Depends(get_current_user)) -> User:
        _ = roles
        return user

    return _role_guard
