from __future__ import annotations

from app.schemas.chat import ChatData


class GenAIService:
    async def chat(self, user_message: str, ticker: str, conversation_history, db) -> str:
        _ = conversation_history, db
        return f'Mock reply about {ticker}' if user_message else f'No message provided for {ticker}'

    async def generate_insight(self, ticker: str, prediction, financial_data) -> str:
        _ = prediction, financial_data
        return f'Mock insight for {ticker}. Market context looks stable.'