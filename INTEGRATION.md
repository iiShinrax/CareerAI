# CareerAI integration

This version removes frontend demo fallbacks and connects the web API to Jamal's local Qwen/Llama-cpp interview approach and the JobRAG knowledge base.

## Required runtime setup

1. Put the O*NET source CSV files in `rag-service/data/raw/onet/`, run `python src/preprocess_onet.py`, then run `python src/build_vector_db.py`. This creates `rag-service/vector_db/index.faiss` and `metadata.json`. Without this, `services/rag_client.py` returns `None` and every AI route responds `503 The career knowledge base is unavailable`.
2. Copy `backend/.env.example` to `backend/.env` and set `LLM_MODEL_PATH` to your local GGUF model file (also set `DATABASE_URL` and `SECRET_KEY` for anything beyond local dev). `backend/app/__init__.py` loads this `.env` automatically — no manual `export` needed. The model itself is loaded lazily on the first AI request.
3. Install `backend/requirements.txt` — this now also pulls in `llama-cpp-python`, `faiss-cpu`, `sentence-transformers`, and `PyPDF2`, which the backend needs directly (not just `rag-service/requirements.txt`). Start the API, then start the Vite app in `frontend/` (copy `frontend/.env.example` to `frontend/.env` first).

AI endpoints return an explicit error if the model or vector database is unavailable. They do not substitute mock results.
