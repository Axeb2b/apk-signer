"""Document loading and indexing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from rag.chunker import chunk_text
from rag.config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR, SUPPORTED_EXTENSIONS
from rag.store import VectorStore


def _load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def discover_documents(root: Path) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def _chunk_id(source: str, chunk_index: int, text: str) -> str:
    digest = hashlib.sha1(f"{source}:{chunk_index}:{text[:64]}".encode()).hexdigest()[:12]
    return f"{Path(source).name}-{chunk_index}-{digest}"


def ingest_paths(
    paths: list[Path],
    *,
    store: VectorStore | None = None,
    reset: bool = False,
) -> dict[str, int]:
    store = store or VectorStore()
    if reset:
        store.reset()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str | int]] = []
    files_indexed = 0
    chunks_indexed = 0

    for path in paths:
        text = _load_file(path)
        source = str(path.resolve())
        chunks = chunk_text(
            text,
            source,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        if not chunks:
            continue

        files_indexed += 1
        for chunk in chunks:
            ids.append(_chunk_id(source, chunk.chunk_index, chunk.text))
            documents.append(chunk.text)
            metadatas.append(
                {
                    "source": source,
                    "chunk_index": chunk.chunk_index,
                    "filename": path.name,
                }
            )
            chunks_indexed += 1

    store.add_chunks(ids, documents, metadatas)
    return {"files": files_indexed, "chunks": chunks_indexed, "total": store.count}


def ingest_directory(
    root: Path | None = None,
    *,
    reset: bool = False,
) -> dict[str, int]:
    root = root or DATA_DIR
    paths = discover_documents(root)
    if not paths:
        raise FileNotFoundError(f"No supported documents found under {root}")
    return ingest_paths(paths, reset=reset)
