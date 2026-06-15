"""Failure mode checks for GenAI fallback and DB connectivity behavior."""

from __future__ import annotations

import json
import os

import httpx
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

BASE_URL = 'http://127.0.0.1:8000/api/v1'


def check_chat_fallback_path() -> dict:
    with httpx.Client(timeout=5.0) as client:
        resp = client.post(
            f'{BASE_URL}/chat',
            json={'message': 'Summarize AAPL with concise bullet points', 'ticker': 'AAPL'},
        )
        ok = resp.status_code == 200
        body = resp.json() if ok else {'error': resp.text}
        reply = str((body.get('data') or {}).get('reply', '')) if isinstance(body, dict) else ''
        fallback_used = 'Context-grounded response for' in reply or 'No GenAI knowledge bundle was matched' in reply

    return {
        'status_code': resp.status_code,
        'api_ok': ok,
        'fallback_observed_or_live_reply': bool(reply),
        'fallback_detected': fallback_used,
    }


async def check_db_connection() -> dict:
    database_url = os.getenv('DATABASE_URL', 'mysql+aiomysql://neuralalpha:neuralalpha@localhost:3306/neuralalpha')
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
        return {'db_ok': True}
    except Exception as exc:  # noqa: BLE001
        return {'db_ok': False, 'error': str(exc)}
    finally:
        await engine.dispose()


async def main() -> None:
    chat = check_chat_fallback_path()
    db = await check_db_connection()
    print(json.dumps({'chat_failure_mode': chat, 'db_failure_mode': db}, indent=2))


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
