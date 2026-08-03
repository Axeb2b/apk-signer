"""End-to-end RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag.config import TOP_K
from rag.generator import GenerationResult, generate_answer
from rag.ingest import ingest_directory, ingest_paths
from rag.retriever import RetrievedChunk, Retriever
from rag.store import VectorStore


@dataclass
class QueryResult:
    question: str
    answer: str
    mode: str
    model: str | None
    chunks: list[RetrievedChunk]


class RAGPipeline:
    def __init__(self, store: VectorStore | None = None) -> None:
        self._store = store or VectorStore()
        self._retriever = Retriever(self._store)

    @property
    def document_count(self) -> int:
        return self._store.count

    def ingest_directory(self, root: Path, *, reset: bool = False) -> dict[str, int]:
        return ingest_directory(root, reset=reset)

    def ingest_files(self, paths: list[Path], *, reset: bool = False) -> dict[str, int]:
        return ingest_paths(paths, reset=reset)

    def reset(self) -> None:
        self._store.reset()

    def query(self, question: str, *, top_k: int = TOP_K) -> QueryResult:
        chunks = self._retriever.retrieve(question, top_k=top_k)
        generated: GenerationResult = generate_answer(question, chunks)
        return QueryResult(
            question=question,
            answer=generated.answer,
            mode=generated.mode,
            model=generated.model,
            chunks=chunks,
        )
