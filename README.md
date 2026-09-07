# CareerAI

CareerAI is an AI career assistant for career profiling, job matching, interview practice, CV analysis, and personalized learning roadmaps.

This branch contains the CareerAI RAG prototype and O*NET knowledge-base tooling. The integrated FastAPI + React application is available on the `jamal2` branch.

## Repository Areas

- `rag-service/`: O*NET data processing, document generation, vector search, and RAG assets.
- `src/`: prototype career and interview workflows.
- `career_ai_training_data.json`: training data used by the prototype.
- `KNOWLEDGE_BASE_PLAN.md`: knowledge-base design notes.
- `rag_search.py`: lightweight RAG search entry point.
- `requirements.txt`: Python dependencies for the RAG/prototype environment.

## Integrated Application

To work with the complete web application, switch to the integrated branch:

```powershell
git checkout jamal2
```

The integrated application contains:

- FastAPI backend in `backend/`
- React/Vite frontend in `frontend/`
- Local SQLite development database
- Local Qwen GGUF model support through `llama-cpp-python`
- FAISS and `sentence-transformers` retrieval over O*NET data

## RAG Prototype Setup

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Build the O*NET knowledge base when the raw files are available:

```powershell
cd rag-service
python src/preprocess_onet.py
python src/build_documents.py
python src/build_vector_db.py
```

The vector index is generated under `rag-service/vector_db/`. Large model files, virtual environments, databases, build output, and other local artifacts are intentionally excluded by `.gitignore`.

## Integrated Application Setup

From the `jamal2` branch, install backend dependencies in `backend/.venv` and frontend dependencies in `frontend/`.

Start the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.init_db
python -m uvicorn app.main:app --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npx vite --host=127.0.0.1
```

Open the application at <http://127.0.0.1:5173/>.

The API health endpoint is <http://127.0.0.1:8000/> and interactive API documentation is available at <http://127.0.0.1:8000/docs>.

## Local AI Requirements

The integrated application requires:

1. A local `.env` file with `LLM_MODEL_PATH` pointing to a local Qwen GGUF model.
2. A built FAISS index and O*NET metadata for retrieval-backed features.
3. `llama-cpp-python`, `faiss-cpu`, and `sentence-transformers` installed in the backend environment.

Model files and credentials must remain local and should not be committed.

## Testing

Frontend build:

```powershell
cd frontend
npm run build
```

Backend syntax check:

```powershell
cd backend
python -m compileall -q app
```

API smoke test:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

Expected response:

```json
{"status":"ok","service":"careerai-api"}
```
