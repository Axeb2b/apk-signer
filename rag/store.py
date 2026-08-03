"""Local vector store (numpy + JSON, no native deps)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from rag.config import EMBEDDING_MODEL, INDEX_DIR

_MODEL: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBEDDING_MODEL)
    return _MODEL


class VectorStore:
    def __init__(self) -> None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self._meta_path = INDEX_DIR / "metadata.json"
        self._embeddings_path = INDEX_DIR / "embeddings.npy"
        self._model = _get_model()
        self._ids: list[str] = []
        self._documents: list[str] = []
        self._metadatas: list[dict[str, Any]] = []
        self._embeddings: np.ndarray | None = None
        self._load()

    def _load(self) -> None:
        if not self._meta_path.exists():
            return
        data = json.loads(self._meta_path.read_text(encoding="utf-8"))
        self._ids = data.get("ids", [])
        self._documents = data.get("documents", [])
        self._metadatas = data.get("metadatas", [])
        if self._embeddings_path.exists() and self._ids:
            self._embeddings = np.load(self._embeddings_path)

    def _save(self) -> None:
        payload = {
            "ids": self._ids,
            "documents": self._documents,
            "metadatas": self._metadatas,
        }
        self._meta_path.write_text(json.dumps(payload), encoding="utf-8")
        if self._embeddings is not None and len(self._embeddings):
            np.save(self._embeddings_path, self._embeddings)

    @property
    def count(self) -> int:
        return len(self._ids)

    def reset(self) -> None:
        self._ids.clear()
        self._documents.clear()
        self._metadatas.clear()
        self._embeddings = None
        for path in (self._meta_path, self._embeddings_path):
            path.unlink(missing_ok=True)

    def add_chunks(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not ids:
            return

        vectors = self._model.encode(documents, normalize_embeddings=True)
        vectors = np.asarray(vectors, dtype=np.float32)

        self._ids.extend(ids)
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)
        if self._embeddings is None or len(self._embeddings) == 0:
            self._embeddings = vectors
        else:
            self._embeddings = np.vstack([self._embeddings, vectors])
        self._save()

    def query(self, text: str, *, top_k: int) -> dict[str, Any]:
        if self.count == 0 or self._embeddings is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        query_vec = self._model.encode([text], normalize_embeddings=True)[0]
        query_vec = np.asarray(query_vec, dtype=np.float32)

        # Cosine similarity (vectors are normalized): dot product.
        scores = self._embeddings @ query_vec
        k = min(top_k, len(scores))
        top_indices = np.argpartition(-scores, k - 1)[:k]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        docs = [self._documents[i] for i in top_indices]
        metas = [self._metadatas[i] for i in top_indices]
        distances = [float(1.0 - scores[i]) for i in top_indices]

        return {
            "documents": [docs],
            "metadatas": [metas],
            "distances": [distances],
        }
