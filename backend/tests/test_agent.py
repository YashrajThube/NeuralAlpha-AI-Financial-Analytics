import numpy as np


class MockEncoder:
    def encode(self, texts, convert_to_numpy=True):
        _ = convert_to_numpy
        return np.random.rand(len(texts), 64).astype(np.float32)


def test_add_and_search(monkeypatch):
    from app.ml.vector_store import VectorStore

    vs = VectorStore()
    monkeypatch.setattr(vs, "_get_encoder", lambda: MockEncoder())
    vs.add_documents(["Apple revenue grew 10%"], [{"ticker": "AAPL", "date": "2024-01-01"}])
    results = vs.search("Apple revenue")
    assert len(results) == 1
    assert "text" in results[0]


def test_search_empty_index():
    from app.ml.vector_store import VectorStore

    vs = VectorStore()
    assert vs.search("anything") == []


def test_retrieve_context_format(monkeypatch):
    from app.services import document_service

    monkeypatch.setattr(document_service.vector_store, "_get_encoder", lambda: MockEncoder())
    document_service.vector_store.clear()
    document_service.ingest_financial_report("AAPL", "Apple earnings beat expectations.", "2024-01-01")
    ctx = document_service.retrieve_context("Apple earnings")
    assert ctx.startswith("[1]")


def test_clear_resets_index():
    from app.ml.vector_store import VectorStore

    vs = VectorStore()
    vs.clear()
    assert vs._index is None
    assert vs._docs == []
