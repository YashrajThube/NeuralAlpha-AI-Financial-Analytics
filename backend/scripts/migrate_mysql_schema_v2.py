from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

if __package__ is None or __package__ == '':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine


async def _column_exists(conn, table: str, column: str) -> bool:
    result = await conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {'table_name': table, 'column_name': column},
    )
    return int(result.scalar_one() or 0) > 0


async def _index_exists(conn, table: str, index_name: str) -> bool:
    result = await conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND INDEX_NAME = :index_name
            """
        ),
        {'table_name': table, 'index_name': index_name},
    )
    return int(result.scalar_one() or 0) > 0


async def migrate() -> None:
    try:
        async with engine.begin() as conn:
            if not await _column_exists(conn, 'users', 'name'):
                await conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(120) NOT NULL DEFAULT 'User'"))
            if not await _column_exists(conn, 'users', 'password_hash') and await _column_exists(conn, 'users', 'hashed_password'):
                await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL"))
                await conn.execute(text("UPDATE users SET password_hash = hashed_password WHERE password_hash IS NULL"))
                await conn.execute(text("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NOT NULL"))
            if await _column_exists(conn, 'users', 'hashed_password') and await _column_exists(conn, 'users', 'password_hash'):
                await conn.execute(text("UPDATE users SET hashed_password = password_hash WHERE hashed_password IS NULL"))
                await conn.execute(text("ALTER TABLE users MODIFY COLUMN hashed_password VARCHAR(255) NULL"))
            if not await _column_exists(conn, 'users', 'updated_at'):
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                    )
                )
            if not await _column_exists(conn, 'users', 'role'):
                await conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"))

            if not await _column_exists(conn, 'predictions', 'prediction_value') and await _column_exists(conn, 'predictions', 'predicted_value'):
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN prediction_value DOUBLE NULL"))
                await conn.execute(text("UPDATE predictions SET prediction_value = predicted_value WHERE prediction_value IS NULL"))
                await conn.execute(text("ALTER TABLE predictions MODIFY COLUMN prediction_value DOUBLE NOT NULL"))
            if not await _column_exists(conn, 'predictions', 'prediction_value') and await _column_exists(conn, 'predictions', 'predicted_price'):
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN prediction_value DOUBLE NULL"))
                await conn.execute(text("UPDATE predictions SET prediction_value = predicted_price WHERE prediction_value IS NULL"))
                await conn.execute(text("ALTER TABLE predictions MODIFY COLUMN prediction_value DOUBLE NOT NULL"))
            if not await _column_exists(conn, 'predictions', 'confidence') and await _column_exists(conn, 'predictions', 'confidence_score'):
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN confidence DOUBLE NULL"))
                await conn.execute(text("UPDATE predictions SET confidence = confidence_score WHERE confidence IS NULL"))
                await conn.execute(text("ALTER TABLE predictions MODIFY COLUMN confidence DOUBLE NOT NULL"))
            if not await _column_exists(conn, 'predictions', 'model_version'):
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN model_version VARCHAR(64) NOT NULL DEFAULT 'ml-v1'"))
            if not await _column_exists(conn, 'predictions', 'features_json'):
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN features_json TEXT NULL"))
            if not await _column_exists(conn, 'predictions', 'created_at') and await _column_exists(conn, 'predictions', 'timestamp'):
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN created_at DATETIME NULL"))
                await conn.execute(text("UPDATE predictions SET created_at = timestamp WHERE created_at IS NULL"))
                await conn.execute(text("ALTER TABLE predictions MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))

            if not await _index_exists(conn, 'predictions', 'ix_predictions_symbol'):
                await conn.execute(text("CREATE INDEX ix_predictions_symbol ON predictions (symbol)"))
            if not await _index_exists(conn, 'predictions', 'ix_predictions_symbol_created_at'):
                await conn.execute(text("CREATE INDEX ix_predictions_symbol_created_at ON predictions (symbol, created_at)"))
            if not await _index_exists(conn, 'predictions', 'ix_predictions_user_created_at'):
                await conn.execute(text("CREATE INDEX ix_predictions_user_created_at ON predictions (user_id, created_at)"))

            if not await _column_exists(conn, 'sentiment_data', 'sentiment_score') and await _column_exists(conn, 'sentiment_data', 'score'):
                await conn.execute(text("ALTER TABLE sentiment_data ADD COLUMN sentiment_score DOUBLE NULL"))
                await conn.execute(text("UPDATE sentiment_data SET sentiment_score = score WHERE sentiment_score IS NULL"))
                await conn.execute(text("ALTER TABLE sentiment_data MODIFY COLUMN sentiment_score DOUBLE NOT NULL"))
            if await _column_exists(conn, 'sentiment_data', 'score') and await _column_exists(conn, 'sentiment_data', 'sentiment_score'):
                await conn.execute(text("UPDATE sentiment_data SET sentiment_score = score WHERE sentiment_score IS NULL"))
            if not await _column_exists(conn, 'sentiment_data', 'sentiment_label') and await _column_exists(conn, 'sentiment_data', 'label'):
                await conn.execute(text("ALTER TABLE sentiment_data ADD COLUMN sentiment_label VARCHAR(16) NULL"))
                await conn.execute(text("UPDATE sentiment_data SET sentiment_label = label WHERE sentiment_label IS NULL"))
                await conn.execute(text("ALTER TABLE sentiment_data MODIFY COLUMN sentiment_label VARCHAR(16) NOT NULL"))
            if not await _column_exists(conn, 'sentiment_data', 'sentiment_label'):
                await conn.execute(text("ALTER TABLE sentiment_data ADD COLUMN sentiment_label VARCHAR(16) NULL"))
                await conn.execute(
                    text(
                        """
                        UPDATE sentiment_data
                        SET sentiment_label = CASE
                            WHEN COALESCE(sentiment_score, 0) > 0.1 THEN 'Positive'
                            WHEN COALESCE(sentiment_score, 0) < -0.1 THEN 'Negative'
                            ELSE 'Neutral'
                        END
                        WHERE sentiment_label IS NULL
                        """
                    )
                )
                await conn.execute(text("ALTER TABLE sentiment_data MODIFY COLUMN sentiment_label VARCHAR(16) NOT NULL"))
            if not await _column_exists(conn, 'sentiment_data', 'source'):
                await conn.execute(text("ALTER TABLE sentiment_data ADD COLUMN source VARCHAR(64) NOT NULL DEFAULT 'system'"))
            if not await _index_exists(conn, 'sentiment_data', 'ix_sentiment_data_symbol'):
                await conn.execute(text("CREATE INDEX ix_sentiment_data_symbol ON sentiment_data (symbol)"))

            if not await _column_exists(conn, 'portfolio', 'avg_price') and await _column_exists(conn, 'portfolio', 'avg_cost'):
                await conn.execute(text("ALTER TABLE portfolio ADD COLUMN avg_price DOUBLE NULL"))
                await conn.execute(text("UPDATE portfolio SET avg_price = avg_cost WHERE avg_price IS NULL"))
                await conn.execute(text("ALTER TABLE portfolio MODIFY COLUMN avg_price DOUBLE NOT NULL"))
            if not await _column_exists(conn, 'portfolio', 'current_price'):
                await conn.execute(text("ALTER TABLE portfolio ADD COLUMN current_price DOUBLE NULL"))
                if await _column_exists(conn, 'portfolio', 'avg_price'):
                    await conn.execute(text("UPDATE portfolio SET current_price = avg_price WHERE current_price IS NULL"))
                await conn.execute(text("ALTER TABLE portfolio MODIFY COLUMN current_price DOUBLE NOT NULL"))
            if not await _column_exists(conn, 'portfolio', 'updated_at'):
                if await _column_exists(conn, 'portfolio', 'timestamp'):
                    await conn.execute(text("ALTER TABLE portfolio ADD COLUMN updated_at DATETIME NULL"))
                    await conn.execute(text("UPDATE portfolio SET updated_at = timestamp WHERE updated_at IS NULL"))
                    await conn.execute(
                        text(
                            "ALTER TABLE portfolio MODIFY COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                        )
                    )
                else:
                    await conn.execute(
                        text(
                            "ALTER TABLE portfolio ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                        )
                    )
            if not await _index_exists(conn, 'portfolio', 'ix_portfolio_symbol'):
                await conn.execute(text("CREATE INDEX ix_portfolio_symbol ON portfolio (symbol)"))

            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS logs (
                        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NULL,
                        action VARCHAR(128) NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        message TEXT NULL,
                        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    )
                    """
                )
            )
            if not await _index_exists(conn, 'logs', 'ix_logs_action_timestamp'):
                await conn.execute(text("CREATE INDEX ix_logs_action_timestamp ON logs (action, timestamp)"))
            if not await _index_exists(conn, 'logs', 'ix_logs_user_timestamp'):
                await conn.execute(text("CREATE INDEX ix_logs_user_timestamp ON logs (user_id, timestamp)"))

            if not await _index_exists(conn, 'market_data', 'ix_market_data_symbol'):
                await conn.execute(text("CREATE INDEX ix_market_data_symbol ON market_data (symbol)"))
            if not await _index_exists(conn, 'market_data', 'ix_market_data_timestamp'):
                await conn.execute(text("CREATE INDEX ix_market_data_timestamp ON market_data (timestamp)"))
    finally:
        await engine.dispose()

    print('Schema migration v2 complete.')


if __name__ == '__main__':
    asyncio.run(migrate())
