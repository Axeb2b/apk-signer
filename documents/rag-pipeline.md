# RAG Pipeline

Retrieval-Augmented Generation over project documentation.

## Architecture

```
documents/  →  chunker  →  embeddings  →  local index (.rag/chroma/)
                                              ↓
question  →  retriever (top-k)  →  LLM (optional)  →  answer
```

## Components

- **Ingest** — loads `.md`, `.txt`, `.py`, `.rst`, `.json` files, splits into overlapping chunks
- **Embeddings** — `all-MiniLM-L6-v2` via sentence-transformers (local, no API key)
- **Vector store** — local numpy index at `.rag/chroma/` (JSON metadata + `.npy` embeddings)
- **Retriever** — cosine similarity search, returns top-k chunks
- **Generator** — OpenAI chat completion when `OPENAI_API_KEY` is set; otherwise returns retrieved context

## CLI

```bash
python rag_cli.py ingest              # index documents/
python rag_cli.py ingest --reset      # rebuild index
python rag_cli.py query "your question"
python rag_cli.py status
python rag_cli.py reset -y
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Enables LLM answer generation |
| `RAG_LLM_MODEL` | `gpt-4o-mini` | OpenAI model for answers |

Chunk size: 800 chars, overlap: 120 chars, top-k: 4.
