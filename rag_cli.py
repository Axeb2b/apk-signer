#!/usr/bin/env python3
"""CLI for the RAG pipeline.

Examples:
  python rag_cli.py ingest
  python rag_cli.py ingest --path documents/ --reset
  python rag_cli.py query "How does APK signing work?"
  python rag_cli.py status
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from env_loader import load_dotenv

load_dotenv()

from rag.config import DATA_DIR, TOP_K
from rag.pipeline import RAGPipeline


def cmd_ingest(args: argparse.Namespace) -> None:
    pipeline = RAGPipeline()
    root = Path(args.path)
    if args.files:
        paths = [Path(p) for p in args.files]
        stats = pipeline.ingest_files(paths, reset=args.reset)
    else:
        stats = pipeline.ingest_directory(root, reset=args.reset)

    print(
        f"Indexed {stats['files']} file(s), {stats['chunks']} chunk(s). "
        f"Collection size: {stats['total']}"
    )


def cmd_query(args: argparse.Namespace) -> None:
    pipeline = RAGPipeline()
    result = pipeline.query(args.question, top_k=args.top_k)

    print(f"Mode: {result.mode}" + (f" ({result.model})" if result.model else ""))
    print()
    print(result.answer)

    if args.show_sources:
        print("\n--- Sources ---")
        for i, chunk in enumerate(result.chunks, start=1):
            print(
                f"{i}. {chunk.filename} [#{chunk.chunk_index}] "
                f"score={chunk.score:.3f}"
            )


def cmd_status(_: argparse.Namespace) -> None:
    pipeline = RAGPipeline()
    print(f"Index path:   {Path('.rag/chroma').resolve()}")
    print(f"Documents dir: {DATA_DIR.resolve()}")
    print(f"Chunks indexed: {pipeline.document_count}")


def cmd_reset(args: argparse.Namespace) -> None:
    if not args.yes:
        answer = input("Delete the vector index? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled.")
            return
    RAGPipeline().reset()
    print("Index cleared.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG pipeline CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="Index documents into the vector store")
    p.add_argument("--path", default=str(DATA_DIR), help="Directory to ingest")
    p.add_argument("--files", nargs="*", help="Specific files to ingest")
    p.add_argument("--reset", action="store_true", help="Clear index before ingest")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("query", help="Ask a question against the index")
    p.add_argument("question", help="Natural language question")
    p.add_argument("--top-k", type=int, default=TOP_K, dest="top_k")
    p.add_argument("--show-sources", action="store_true", help="Print source chunks")
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("status", help="Show index status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("reset", help="Delete the vector index")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p.set_defaults(func=cmd_reset)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
