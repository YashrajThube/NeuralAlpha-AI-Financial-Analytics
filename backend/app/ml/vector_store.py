from __future__ import annotations

import math
from typing import Any

import numpy as np


class _FallbackEncoder:
    def encode(self, texts: list[str], convert_to_numpy: bool = True):
        vectors = []
        for text in texts:
            seed = abs(hash(text)) % (2**32)
            rng = np.random.default_rng(seed)
            vectors.append(rng.random(64, dtype=np.float32))
        arr = np.vstack(vectors) if vectors else np.empty((0, 64), dtype=np.float32)
        return arr if convert_to_numpy else arr.tolist()


class VectorStore:
    def __init__(self) -> None:
        self._index: np.ndarray | None = None
        self._docs: list[dict[str, Any]] = []
        self._encoder: Any | None = None

    def _get_encoder(self):
        if self._encoder is None:
            self._encoder = _FallbackEncoder()
        return self._encoder

    def clear(self) -> None:
        self._index = None
        self._docs = []

    def add_documents(self, texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> None:
        if not texts:
            return
        metadatas = metadatas or [{} for _ in texts]
        encoder = self._get_encoder()
        embeddings = np.asarray(encoder.encode(texts, convert_to_numpy=True), dtype=np.float32)

        if self._index is None:
            self._index = embeddings
        else:
            self._index = np.vstack([self._index, embeddings])

        for text, metadata in zip(texts, metadatas):
            self._docs.append({'text': text, 'metadata': metadata or {}})

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._index is None or not self._docs:
            return []

        encoder = self._get_encoder()
        query_vec = np.asarray(encoder.encode([query], convert_to_numpy=True), dtype=np.float32)[0]

        doc_vectors = self._index
        q_norm = float(np.linalg.norm(query_vec)) or 1.0
        d_norms = np.linalg.norm(doc_vectors, axis=1)
        sims = (doc_vectors @ query_vec) / np.maximum(d_norms * q_norm, 1e-8)

        k = max(1, min(top_k, len(self._docs)))
        indices = np.argsort(-sims)[:k]
        results: list[dict[str, Any]] = []
        for idx in indices.tolist():
            item = self._docs[idx]
            results.append(
                {
                    'text': item['text'],
                    'metadata': item.get('metadata', {}),
                    'score': float(sims[idx]) if not math.isnan(float(sims[idx])) else 0.0,
                }
            )
        return results