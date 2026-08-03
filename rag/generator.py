"""LLM answer generation with retrieved context."""

from __future__ import annotations

import os
from dataclasses import dataclass

from rag.config import LLM_MODEL
from rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question using ONLY the provided context.
If the context does not contain enough information, say you don't know and suggest what document might help.
Be concise and cite source filenames when relevant."""


@dataclass
class GenerationResult:
    answer: str
    mode: str  # "llm" or "extractive"
    model: str | None = None


def _format_context(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[{i}] ({chunk.filename}, score={chunk.score:.3f})\n{chunk.text}"
        )
    return "\n\n".join(parts)


def _extractive_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant documents found in the index."

    lines = [
        "No OPENAI_API_KEY set — returning retrieved context instead of an LLM answer.",
        f"Question: {query}",
        "",
        "Top matches:",
    ]
    for i, chunk in enumerate(chunks, start=1):
        preview = chunk.text.replace("\n", " ")
        if len(preview) > 300:
            preview = preview[:297] + "..."
        lines.append(
            f"{i}. [{chunk.filename}] (score={chunk.score:.3f}) {preview}"
        )
    return "\n".join(lines)


def generate_answer(query: str, chunks: list[RetrievedChunk]) -> GenerationResult:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    context = _format_context(chunks)

    if not api_key:
        return GenerationResult(
            answer=_extractive_answer(query, chunks),
            mode="extractive",
        )

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("RAG_LLM_MODEL", LLM_MODEL),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ],
        temperature=0.2,
    )
    answer = response.choices[0].message.content or ""
    return GenerationResult(
        answer=answer.strip(),
        mode="llm",
        model=response.model,
    )
