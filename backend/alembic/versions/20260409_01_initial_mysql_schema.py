"""initial schema for production MySQL backend.

Revision ID: 20260409_01
Revises:
Create Date: 2026-04-09 14:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260409_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default=sa.text("'user'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "market_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_data_symbol", "market_data", ["symbol"], unique=False)
    op.create_index("ix_market_data_timestamp", "market_data", ["timestamp"], unique=False)
    op.create_index("ix_market_data_symbol_timestamp", "market_data", ["symbol", "timestamp"], unique=False)

    op.create_table(
        "sentiment_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("sentiment_label", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default=sa.text("'system'")),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sentiment_data_symbol", "sentiment_data", ["symbol"], unique=False)
    op.create_index("ix_sentiment_data_symbol_timestamp", "sentiment_data", ["symbol", "timestamp"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("prediction_value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("features_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_symbol", "predictions", ["symbol"], unique=False)
    op.create_index("ix_predictions_symbol_created_at", "predictions", ["symbol", "created_at"], unique=False)
    op.create_index("ix_predictions_user_created_at", "predictions", ["user_id", "created_at"], unique=False)

    op.create_table(
        "portfolio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("avg_price", sa.Float(), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_user_symbol", "portfolio", ["user_id", "symbol"], unique=False)
    op.create_index("ix_portfolio_symbol", "portfolio", ["symbol"], unique=False)

    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_logs_action_timestamp", "logs", ["action", "timestamp"], unique=False)
    op.create_index("ix_logs_user_timestamp", "logs", ["user_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_logs_user_timestamp", table_name="logs")
    op.drop_index("ix_logs_action_timestamp", table_name="logs")
    op.drop_table("logs")
    op.drop_index("ix_portfolio_symbol", table_name="portfolio")
    op.drop_index("ix_portfolio_user_symbol", table_name="portfolio")
    op.drop_table("portfolio")
    op.drop_index("ix_predictions_user_created_at", table_name="predictions")
    op.drop_index("ix_predictions_symbol_created_at", table_name="predictions")
    op.drop_index("ix_predictions_symbol", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_sentiment_data_symbol_timestamp", table_name="sentiment_data")
    op.drop_index("ix_sentiment_data_symbol", table_name="sentiment_data")
    op.drop_table("sentiment_data")
    op.drop_index("ix_market_data_symbol_timestamp", table_name="market_data")
    op.drop_index("ix_market_data_timestamp", table_name="market_data")
    op.drop_index("ix_market_data_symbol", table_name="market_data")
    op.drop_table("market_data")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
