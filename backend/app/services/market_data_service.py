from datetime import datetime

from sqlalchemy import Select, and_, desc, distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_data import MarketData


class MarketDataService:
    @staticmethod
    async def list_symbols(db: AsyncSession, limit: int = 500) -> list[str]:
        stmt = select(distinct(MarketData.symbol)).order_by(MarketData.symbol.asc()).limit(limit)
        rows = await db.execute(stmt)
        symbols = [str(item).upper() for item in rows.scalars().all() if item]
        if symbols:
            return symbols

        # Safe defaults when market_data table is empty.
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']

    @staticmethod
    async def insert_tick(
        db: AsyncSession,
        symbol: str,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
    ) -> MarketData:
        row = MarketData(
            symbol=symbol.upper(),
            timestamp=timestamp,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
        )
        db.add(row)
        flush = getattr(db, 'flush', None)
        if callable(flush):
            await flush()
        refresh = getattr(db, 'refresh', None)
        if callable(refresh):
            await refresh(row)
        return row

    @staticmethod
    async def get_latest(db: AsyncSession, symbol: str, limit: int = 200) -> list[MarketData]:
        stmt: Select[tuple[MarketData]] = (
            select(MarketData)
            .where(MarketData.symbol == symbol.upper())
            .order_by(desc(MarketData.timestamp))
            .limit(limit)
        )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get_range(
        db: AsyncSession,
        symbol: str,
        start_ts: datetime,
        end_ts: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[MarketData]:
        stmt: Select[tuple[MarketData]] = (
            select(MarketData)
            .where(
                and_(
                    MarketData.symbol == symbol.upper(),
                    MarketData.timestamp >= start_ts,
                    MarketData.timestamp <= end_ts,
                )
            )
            .order_by(MarketData.timestamp.asc())
            .offset(offset)
            .limit(limit)
        )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())
