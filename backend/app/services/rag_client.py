"""
Thin bridge to Member 1's JobRAG (../../rag-service/rag_search.py).

get_rag() returns a cached JobRAG instance, or None if the vector
database hasn't been built yet, or the RAG dependencies (faiss,
sentence-transformers) aren't installed. Every router that calls
this checks for None and raises HTTPException(503) — there is no
mock/rule-based fallback anywhere; this function itself never raises.
"""

import sys
from pathlib import Path

_rag = None
_attempted = False


def get_rag():
    global _rag, _attempted
    if _attempted:
        return _rag
    _attempted = True

    # backend/app/services/rag_client.py -> project root -> rag-service/
    rag_service_dir = Path(__file__).resolve().parents[3] / "rag-service"
    if str(rag_service_dir) not in sys.path:
        sys.path.insert(0, str(rag_service_dir))

    try:
        from rag_search import JobRAG
        _rag = JobRAG()
    except Exception as exc:
        print(f"[rag_client] RAG unavailable: {exc}")
        _rag = None

    return _rag
