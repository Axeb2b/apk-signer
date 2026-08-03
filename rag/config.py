"""RAG pipeline configuration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "documents"
INDEX_DIR = ROOT / ".rag" / "chroma"
COLLECTION_NAME = "knowledge"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 4

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gpt-4o-mini"

SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".rst", ".json"}
