"""Text chunking utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    chunk_index: int


def chunk_text(
    text: str,
    source: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    text = text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        piece = text[start:end]

        if end < len(text):
            # Prefer breaking on paragraph or sentence boundaries.
            for sep in ("\n\n", "\n", ". ", " "):
                pos = piece.rfind(sep)
                if pos > chunk_size // 2:
                    piece = piece[: pos + len(sep)]
                    end = start + len(piece)
                    break

        piece = piece.strip()
        if piece:
            chunks.append(Chunk(text=piece, source=source, chunk_index=index))
            index += 1

        if end >= len(text):
            break
        start = max(end - chunk_overlap, start + 1)

    return chunks
