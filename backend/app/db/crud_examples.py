from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.logs import LogEntry
from app.db.models.market_data import MarketData
from app.db.models.portfolio import Portfolio
from app.db.models.prediction import Prediction
from app.db.models.sentiment import SentimentData
from app.db.models.user import User


async def create_user(session: AsyncSession, name: str, email: str, password_hash: str, role: str = 'user') -> User:
    user = User(name=name, email=email.lower(), password_hash=password_hash, role=role)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def save_prediction(
    session: AsyncSession,
    user_id: int,
    symbol: str,
    prediction_value: float,
    confidence: float,
    model_version: str,
) -> Prediction:
    row = Prediction(
        user_id=user_id,
        symbol=symbol.upper(),
        prediction_value=prediction_value,
        confidence=confidence,
        model_version=model_version,
    )
    session.add(row)
    await session.flush()
    return row


async def fetch_market_window(
    session: AsyncSession,
    symbol: str,
    days: int = 30,
    limit: int = 500,
) -> list[MarketData]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await session.execute(
        select(MarketData)
        .where(MarketData.symbol == symbol.upper(), MarketData.timestamp >= since)
        .order_by(MarketData.timestamp.asc())
        .limit(limit)
    )
    return list(rows.scalars().all())


async def fetch_latest_sentiment(session: AsyncSession, symbol: str) -> SentimentData | None:
    row = await session.execute(
        select(SentimentData)
        .where(SentimentData.symbol == symbol.upper())
        .order_by(SentimentData.timestamp.desc())
        .limit(1)
    )
    return row.scalar_one_or_none()


async def upsert_portfolio_position(
    session: AsyncSession,
    user_id: int,
    symbol: str,
    quantity: float,
    avg_price: float,
    current_price: float,
) -> Portfolio:
    existing = await session.execute(
        select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.symbol == symbol.upper())
    )
    row = existing.scalar_one_or_none()
    if row is None:
        row = Portfolio(
            user_id=user_id,
            symbol=symbol.upper(),
            quantity=quantity,
            avg_price=avg_price,
            current_price=current_price,
        )
        session.add(row)
    else:
        row.quantity = quantity
        row.avg_price = avg_price
        row.current_price = current_price
    await session.flush()
    return row


async def create_log(
    session: AsyncSession,
    action: str,
    status: str,
    message: str,
    user_id: int | None = None,
) -> LogEntry:
    row = LogEntry(user_id=user_id, action=action, status=status, message=message)
    session.add(row)
    await session.flush()
    return row
