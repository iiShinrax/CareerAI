"""Live job matching using the user's profile, RAG context, and Jamal's LLM."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import models
from ..deps import current_user
from ..services.llm_client import LLMUnavailable, json_completion
from ..services.rag_client import get_rag

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobMatchRequest(BaseModel):
    description: str


@router.post("/match")
def match_job(payload: JobMatchRequest, user: models.User = Depends(current_user)):
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="A job description is required")
    rag = get_rag()
    if not rag:
        raise HTTPException(status_code=503, detail="The career knowledge base is unavailable")
    try:
        context = rag.search_job(payload.description[:1000])
        result = json_completion(
            "You are CareerAI's precise job-matching analyst. Return only JSON.",
            f"Candidate skills: {[skill.skill for skill in user.skills]}\n"
            f"Candidate profile: education={user.education or ''}; experience={user.experience or ''}; target role={user.target_role or ''}\n"
            f"Job description: {payload.description[:6000]}\nRelevant O*NET context: {context[:5000]}\n"
            "Return exactly: {\"match_percent\": integer 0-100, \"matched_skills\": [string], "
            "\"missing_skills\": [string], \"recommendation\": string}. Do not invent candidate skills.",
        )
        result["match_percent"] = max(0, min(100, int(result["match_percent"])))
        return result
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="The matching model returned an unusable result") from exc
