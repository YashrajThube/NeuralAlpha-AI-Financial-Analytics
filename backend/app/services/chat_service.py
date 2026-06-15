from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.db.models.prediction import Prediction
from app.db.models.sentiment import SentimentData
from app.schemas.chat import ChatData, ChatRequest
from app.services.cache_service import CacheService
from app.services.log_service import LogService
from sqlalchemy import select

try:
    from sqlalchemy.ext.asyncio import AsyncSession
except Exception:  # pragma: no cover
    AsyncSession = object  # type: ignore[assignment]


@dataclass
class RetrievedChunk:
    source: str
    text: str
    score: float


def _tokenize(value: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", value.lower()))


def _chunk_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[3]
    configured_root = Path(settings.model_dir)
    return [
        configured_root / 'genai' / 'genai_chunks.json',
        repo_root / 'backend' / 'models' / 'genai' / 'genai_chunks.json',
        repo_root / 'ml_pipeline' / 'models' / 'genai' / 'genai_chunks.json',
    ]


@lru_cache(maxsize=1)
def _load_chunks() -> list[dict[str, str]]:
    for candidate in _chunk_paths():
        if candidate.exists():
            with candidate.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                return [
                    {
                        'source': str(item.get('source', 'unknown')),
                        'text': str(item.get('text', '')).strip(),
                    }
                    for item in payload
                    if str(item.get('text', '')).strip()
                ]
    return []


def _retrieve(query: str, top_k: int = 3) -> list[RetrievedChunk]:
    query_tokens = _tokenize(query)
    matches: list[RetrievedChunk] = []
    for chunk in _load_chunks():
        text_tokens = _tokenize(chunk['text'])
        if not text_tokens:
            continue
        overlap = len(query_tokens.intersection(text_tokens))
        denom = max(len(query_tokens), 1)
        score = overlap / denom
        if score > 0:
            matches.append(RetrievedChunk(source=chunk['source'], text=chunk['text'], score=score))

    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[:top_k]


def _build_response_focus(message: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in ['risk', 'downside', 'volatility', 'drawdown']):
        return 'risk'
    if any(token in lowered for token in ['sentiment', 'news', 'social', 'buzz']):
        return 'sentiment'
    if any(token in lowered for token in ['buy', 'sell', 'hold', 'position', 'allocation']):
        return 'positioning'
    if any(token in lowered for token in ['forecast', 'predict', 'target', 'price']):
        return 'price_outlook'
    return 'market_overview'


def _format_number(value: float | None, decimals: int = 4) -> str:
    if value is None:
        return 'unknown'
    return f'{value:.{decimals}f}'


def _build_prompt(
    symbol: str,
    message: str,
    chunks: list[RetrievedChunk],
    sentiment_label: str | None,
    sentiment_score: float | None,
    prediction_value: float | None,
    prediction_confidence: float | None,
) -> str:
    focus = _build_response_focus(message)
    retrieved_context = '\n'.join(f'- [{item.source}] {item.text}' for item in chunks)
    if not retrieved_context:
        retrieved_context = '- No indexed context snippets matched the query.'

    system_rules = (
        'You are an expert financial AI assistant for a market intelligence platform. '
        'Generate a context-aware response that is specific to the provided symbol and signals. '
        'Do not produce generic or boilerplate advice. '
        'If any field is unknown, state uncertainty clearly and continue with available evidence.'
    )

    user_template = (
        '[CONTEXT]\n'
        f'symbol: {symbol}\n'
        f'sentiment_label: {sentiment_label or "unknown"}\n'
        f'sentiment_score: {_format_number(sentiment_score)}\n'
        f'prediction_value: {_format_number(prediction_value, 2)}\n'
        f'prediction_confidence: {_format_number(prediction_confidence)}\n'
        f'focus: {focus}\n\n'
        '[RETRIEVED_EVIDENCE]\n'
        f'{retrieved_context}\n\n'
        '[USER_QUESTION]\n'
        f'{message}\n\n'
        '[RESPONSE_FORMAT]\n'
        'Return exactly these sections with concrete references to the context:\n'
        '1) Thesis\n'
        '2) Signal Interpretation\n'
        '3) Risks & Caveats\n'
        '4) Next Action\n'
        'Rules: mention the symbol, sentiment, and prediction explicitly. Keep it concise and specific.'
    )

    return f'{system_rules}\n\n{user_template}'


def _build_fallback_reply(
    symbol: str,
    message: str,
    chunks: list[RetrievedChunk],
    sentiment_label: str | None,
    sentiment_score: float | None,
    prediction_value: float | None,
    prediction_confidence: float | None,
) -> str:
    focus = _build_response_focus(message)
    context_lines = '\n'.join(f'- [{item.source}] {item.text}' for item in chunks[:3])
    if not context_lines:
        context_lines = '- No indexed evidence available. Ensure genai_chunks.json is present.'

    sentiment_text = sentiment_label or 'unknown'
    sentiment_score_text = _format_number(sentiment_score)
    prediction_text = _format_number(prediction_value, 2)
    confidence_text = _format_number(prediction_confidence)

    action_line = {
        'risk': 'Prioritize downside controls and reduce position size if volatility expands.',
        'sentiment': 'Track sentiment drift over the next few intervals before changing exposure.',
        'positioning': 'Scale exposure only when confidence and sentiment are aligned.',
        'price_outlook': 'Use the predicted value as a scenario anchor, not a guaranteed target.',
        'market_overview': 'Combine these signals with volume and trend confirmation before acting.',
    }[focus]

    return (
        f'Thesis: For {symbol}, current sentiment is {sentiment_text} '
        f'(score {sentiment_score_text}) while the latest predicted value is {prediction_text} '
        f'with confidence {confidence_text}.\n'
        f'Signal Interpretation: Your question is centered on {focus}. '
        'This response is tailored to that lens using symbol-specific context.\n'
        'Risks & Caveats: Sentiment and predictive signals are probabilistic and can lag real-time moves.\n'
        f'Next Action: {action_line}\n'
        f'Context Used:\n{context_lines}\n'
        f'Question received: {message}'
    )


async def _load_symbol_context(db: AsyncSession, symbol: str) -> tuple[str | None, float | None, float | None, float | None]:
    cache_key = f'chat_context:{symbol}'
    cached = await CacheService.get_json(cache_key)
    if cached:
        return (
            cached.get('sentiment_label'),
            float(cached['sentiment_score']) if cached.get('sentiment_score') is not None else None,
            float(cached['prediction_value']) if cached.get('prediction_value') is not None else None,
            float(cached['prediction_confidence']) if cached.get('prediction_confidence') is not None else None,
        )

    sentiment_stmt = (
        select(SentimentData.sentiment_label, SentimentData.sentiment_score)
        .where(SentimentData.symbol == symbol)
        .order_by(SentimentData.timestamp.desc())
        .limit(1)
    )
    prediction_stmt = (
        select(Prediction.prediction_value, Prediction.confidence)
        .where(Prediction.symbol == symbol)
        .order_by(Prediction.created_at.desc())
        .limit(1)
    )

    sentiment_row = (await db.execute(sentiment_stmt)).first()
    prediction_row = (await db.execute(prediction_stmt)).first()

    sentiment_label = sentiment_row[0] if sentiment_row else None
    sentiment_score = float(sentiment_row[1]) if sentiment_row and sentiment_row[1] is not None else None
    prediction_value = float(prediction_row[0]) if prediction_row and prediction_row[0] is not None else None
    prediction_confidence = float(prediction_row[1]) if prediction_row and prediction_row[1] is not None else None

    await CacheService.set_json(
        cache_key,
        {
            'sentiment_label': sentiment_label,
            'sentiment_score': sentiment_score,
            'prediction_value': prediction_value,
            'prediction_confidence': prediction_confidence,
        },
        ttl_seconds=60,
    )
    return sentiment_label, sentiment_score, prediction_value, prediction_confidence


def _generate_with_gemini_sync(prompt: str, model_name: str, timeout_seconds: float) -> str | None:
    api_key = settings.gemini_api_key or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return None

    try:
        import google.generativeai as genai
    except Exception:  # noqa: BLE001
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, request_options={'timeout': timeout_seconds})
        text = getattr(response, 'text', None)
        if isinstance(text, str) and text.strip():
            return text.strip()
    except Exception:  # noqa: BLE001
        return None

    return None


async def _generate_with_gemini(prompt: str) -> tuple[str | None, str | None]:
    timeout_primary = float(settings.llm_timeout)
    timeout_secondary = float(settings.llm_secondary_timeout)

    api_key = (settings.gemini_api_key or os.getenv('GOOGLE_API_KEY', '')).strip()
    lowered = api_key.lower()
    if not api_key or 'replace' in lowered or 'changeme' in lowered:
        return None, None

    for idx, model_name in enumerate(settings.gemini_models):
        timeout_seconds = timeout_primary if idx == 0 else timeout_secondary
        try:
            text = await asyncio.wait_for(
                asyncio.to_thread(_generate_with_gemini_sync, prompt, model_name, timeout_seconds),
                timeout=timeout_seconds,
            )
            if text:
                return text, model_name
        except Exception:  # noqa: BLE001
            continue
    return None, None


class ChatService:
    @staticmethod
    async def chat(payload: ChatRequest, db: AsyncSession | None = None) -> ChatData:
        started = time.perf_counter()
        symbol = payload.symbol.upper().strip()
        chunks = _retrieve(payload.message)
        sentiment_label: str | None = None
        sentiment_score: float | None = None
        prediction_value: float | None = None
        prediction_confidence: float | None = None

        if db is not None:
            sentiment_label, sentiment_score, prediction_value, prediction_confidence = await _load_symbol_context(db, symbol)

        prompt = _build_prompt(
            symbol=symbol,
            message=payload.message,
            chunks=chunks,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            prediction_value=prediction_value,
            prediction_confidence=prediction_confidence,
        )

        reply, used_model = await _generate_with_gemini(prompt)
        fallback_used = reply is None
        fallback_reason = 'none'
        if fallback_used:
            fallback_reason = 'gemini_unavailable_or_timeout'
            reply = _build_fallback_reply(
                symbol=symbol,
                message=payload.message,
                chunks=chunks,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                prediction_value=prediction_value,
                prediction_confidence=prediction_confidence,
            )

        if db is not None:
            latency_ms = round((time.perf_counter() - started) * 1000, 3)
            await LogService.create_log(
                db,
                action='chat.request',
                status='success',
                message=json.dumps(
                    {
                        'symbol': symbol,
                        'latency_ms': latency_ms,
                        'model': used_model,
                        'fallback_used': fallback_used,
                        'fallback_reason': fallback_reason,
                    }
                ),
            )
        return ChatData(reply=reply, symbol=symbol)
