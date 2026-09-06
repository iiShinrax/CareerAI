"""
Loads backend/.env (if present) into the process environment before any
submodule reads os.environ — database.py, security.py, and llm_client.py
all depend on this having already run. Running this here, in the package
__init__, means it fires no matter which entrypoint is used
(`uvicorn app.main:app`, `python -m app.init_db`, etc.).
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
