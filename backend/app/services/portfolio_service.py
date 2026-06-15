from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.models.portfolio import Portfolio
from app.db.models.user import User
from app.services.log_service import LogService


class PortfolioService:
    @staticmethod
    async def summary(current_user: User, db: AsyncSession) -> dict:
        rows = await db.execute(select(Portfolio).where(Portfolio.user_id == current_user.id))
        items = rows.scalars().all()

        holdings = [
            {
                'symbol': item.symbol,
                'quantity': float(item.quantity),
                'avg_price': float(item.avg_price),
                'market_price': float(item.current_price),
                'market_value': float(item.quantity * item.current_price),
                'pnl': float((item.current_price - item.avg_price) * item.quantity),
            }
            for item in items
        ]

        total_market_value = sum(row['market_value'] for row in holdings)
        for row in holdings:
            row['weight_pct'] = round((row['market_value'] / total_market_value) * 100, 4) if total_market_value > 0 else 0.0

        return {
            'holdings': holdings,
            'total_market_value': round(total_market_value, 4),
            'positions': len(holdings),
        }

    @staticmethod
    async def upsert_position(
        current_user: User,
        symbol: str,
        quantity: float,
        avg_price: float,
        current_price: float,
        db: AsyncSession,
    ) -> dict:
        symbol = symbol.upper()
        now = func.now()
        existing = await db.execute(
            select(Portfolio).where(
                Portfolio.user_id == current_user.id,
                Portfolio.symbol == symbol,
            )
        )
        row = existing.scalar_one_or_none()

        if row is None:
            await db.execute(
                text(
                    """
                    INSERT INTO portfolio (
                        user_id,
                        symbol,
                        quantity,
                        avg_cost,
                        avg_price,
                        current_price,
                        timestamp,
                        updated_at
                    ) VALUES (
                        :user_id,
                        :symbol,
                        :quantity,
                        :avg_cost,
                        :avg_price,
                        :current_price,
                        NOW(),
                        NOW()
                    )
                    """
                ),
                {
                    'user_id': current_user.id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'avg_cost': avg_price,
                    'avg_price': avg_price,
                    'current_price': current_price,
                },
            )
        else:
            await db.execute(
                text(
                    """
                    UPDATE portfolio
                    SET quantity = :quantity,
                        avg_cost = :avg_cost,
                        avg_price = :avg_price,
                        current_price = :current_price,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    'id': row.id,
                    'quantity': quantity,
                    'avg_cost': avg_price,
                    'avg_price': avg_price,
                    'current_price': current_price,
                },
            )

        await LogService.create_log(
            db,
            user_id=current_user.id,
            action='portfolio.upsert',
            status='success',
            message=f'{symbol}:{quantity}',
        )
        return {
            'symbol': symbol,
            'quantity': float(quantity),
            'avg_price': float(avg_price),
            'current_price': float(current_price),
        }
