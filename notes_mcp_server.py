"""
MCP server exposing a semantic search tool over a local folder of your own
notes (markdown or text files). This is a RAG backend: Llama 3 retrieves
relevant notes at inference time instead of having book content trained
into its weights. Nothing here trains on or stores copyrighted text --
it only searches files you write yourself.

Install:
    pip install mcp sentence-transformers numpy

Usage:
    Put your own note files (.md or .txt) in ./notes/
    python notes_mcp_server.py
"""

import os
import glob
import numpy as np
from sentence_transformers import SentenceTransformer
from mcp.server.fastmcp import FastMCP

NOTES_DIR = "./notes"
EMBED_MODEL = "all-MiniLM-L6-v2"

mcp = FastMCP("notes-search")
model = SentenceTransformer(EMBED_MODEL)

_chunks = []
_embeddings = None


def _load_notes():
    global _chunks, _embeddings
    _chunks = []
    paths = (
        glob.glob(os.path.join(NOTES_DIR, "**/*.md"), recursive=True)
        + glob.glob(os.path.join(NOTES_DIR, "**/*.txt"), recursive=True)
    )
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
            _chunks.append({"source": path, "text": para})

    if _chunks:
        texts = [c["text"] for c in _chunks]
        _embeddings = model.encode(texts, normalize_embeddings=True)
    else:
        _embeddings = np.zeros((0, model.get_sentence_embedding_dimension()))


_load_notes()


@mcp.tool()
def search_notes(query: str, top_k: int = 5) -> str:
    """Search your personal notes for passages relevant to a query.

    Args:
        query: the search query or question
        top_k: how many passages to return
    """
    if not _chunks:
        return "No notes found. Add .md or .txt files to ./notes/ and restart."

    query_vec = model.encode([query], normalize_embeddings=True)[0]
    scores = _embeddings @ query_vec
    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in top_idx:
        chunk = _chunks[i]
        fname = os.path.basename(chunk["source"])
        results.append(f"[{fname}] (score {scores[i]:.2f})\n{chunk['text']}")
    return "\n\n---\n\n".join(results)


@mcp.tool()
def reload_notes() -> str:
    """Reload notes from disk, picking up any new or edited files."""
    _load_notes()
    return f"Reloaded {len(_chunks)} note chunks from {NOTES_DIR}."


if __name__ == "__main__":
    mcp.run()
