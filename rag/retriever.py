"""Semantic retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from rag.config import TOP_K
from rag.store import VectorStore


@dataclass
class RetrievedChunk:
    text: str
    source: str
    filename: str
    chunk_index: int
    score: float


class Retriever:
    def __init__(self, store: VectorStore | None = None) -> None:
        self._store = store or VectorStore()

    def retrieve(self, query: str, *, top_k: int = TOP_K) -> list[RetrievedChunk]:
        if self._store.count == 0:
            raise RuntimeError("Index is empty. Run: python rag_cli.py ingest")

        result = self._store.query(query, top_k=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[RetrievedChunk] = []
        for doc, meta, distance in zip(documents, metadatas, distances):
            # Chroma cosine distance: lower is better; convert to similarity score.
            score = 1.0 - float(distance)
            chunks.append(
                RetrievedChunk(
                    text=doc,
                    source=meta.get("source", ""),
                    filename=meta.get("filename", ""),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    score=score,
                )
            )
        return chunks
