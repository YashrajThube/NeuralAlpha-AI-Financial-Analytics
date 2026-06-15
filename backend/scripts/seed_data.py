"""Idempotent local seed data for users and financial_data."""

from __future__ import annotations

import asyncio
import math
import sys
from datetime import date, timedelta
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.db.session import async_session_factory

DEMO_USER_EMAIL = "demo@neuralalpha.local"
DEMO_TICKERS = ("AAPL", "MSFT")
DAYS_PER_TICKER = 90


async def _ensure_demo_user(session) -> None:
    result = await session.execute(text("SELECT id FROM users WHERE email = :email LIMIT 1"), {"email": DEMO_USER_EMAIL})
    if result.first() is not None:
        return

    await session.execute(
        text(
            "INSERT INTO users (name, email, password_hash, role) VALUES (:name, :email, :password_hash, :role)"
        ),
        {
            "name": "Demo User",
            "email": DEMO_USER_EMAIL,
            "password_hash": "seeded-local-password-hash",
            "role": "user",
        },
    )


def _build_price(day_index: int, ticker: str) -> tuple[float, float, float, float, float]:
    base = 150.0 if ticker == "AAPL" else 320.0
    trend = day_index * (0.18 if ticker == "AAPL" else 0.14)
    seasonal = math.sin(day_index / 5.0) * (1.2 if ticker == "AAPL" else 1.6)
    close = base + trend + seasonal
    open_price = close - 0.45
    high = close + 1.15
    low = close - 1.10
    volume = 1_200_000 + ((day_index % 11) * 17_500)
    return round(open_price, 4), round(high, 4), round(low, 4), round(close, 4), float(volume)


async def _seed_market_data(session) -> int:
    inserted = 0
    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS_PER_TICKER - 1)

    for ticker in DEMO_TICKERS:
        existing_dates_result = await session.execute(
            text("SELECT timestamp FROM market_data WHERE symbol = :symbol"),
            {"symbol": ticker},
        )
        existing_dates = {row[0] for row in existing_dates_result.all() if row and row[0]}

        for offset in range(DAYS_PER_TICKER):
            row_date = start_date + timedelta(days=offset)
            if row_date in existing_dates:
                continue

            open_price, high, low, close, volume = _build_price(offset, ticker)
            await session.execute(
                text(
                    """
                    INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume)
                    VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)
                    """
                ),
                {
                    "symbol": ticker,
                    "timestamp": row_date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                },
            )
            inserted += 1

    return inserted


async def main() -> None:
    async with async_session_factory() as session:
        await _ensure_demo_user(session)
        inserted_rows = await _seed_market_data(session)
        await session.commit()

    print(f"Seed complete. Inserted market_data rows: {inserted_rows}")


if __name__ == "__main__":
    asyncio.run(main())
