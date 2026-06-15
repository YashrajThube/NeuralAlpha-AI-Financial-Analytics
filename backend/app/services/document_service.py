from __future__ import annotations

from app.ml.vector_store import VectorStore

vector_store = VectorStore()


def ingest_financial_report(ticker: str, text: str, report_date: str) -> None:
    vector_store.add_documents([text], [{'ticker': ticker.upper(), 'date': report_date}])


def retrieve_context(query: str, top_k: int = 3) -> str:
    results = vector_store.search(query, top_k=top_k)
    if not results:
        return ''
    lines = [f"[{idx}] {row['text']}" for idx, row in enumerate(results, start=1)]
    return '\n'.join(lines)