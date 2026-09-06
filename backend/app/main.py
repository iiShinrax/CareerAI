"""
CareerAI backend entrypoint.

Run locally with:

    cd careerai-backend
    python -m app.init_db          # first time only, creates tables
    uvicorn app.main:app --reload

Then open http://localhost:8000/docs for interactive API docs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, profile, career, chat, cv, interview, jobs, roadmap

app = FastAPI(title="CareerAI API", version="0.1.0")

# Allow the React dev server to call this API. Tighten allow_origins
# to your real frontend domain before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(cv.router)
app.include_router(career.router)
app.include_router(jobs.router)
app.include_router(roadmap.router)
app.include_router(chat.router)
app.include_router(interview.interview_router)
app.include_router(interview.evaluation_router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "careerai-api"}
