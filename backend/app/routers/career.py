"""RAG-informed career analysis with no static role-to-skill mapping."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import models
from ..deps import current_user
from ..services.llm_client import LLMUnavailable, json_completion
from ..services.rag_client import get_rag

router = APIRouter(prefix="/api/career", tags=["career"])


class CareerAnalysis(BaseModel):
    target_role: str
    readiness_percent: int
    matched_skills: list[str]
    missing_skills: list[str]


@router.post("/analyze", response_model=CareerAnalysis)
def analyze_career(user: models.User = Depends(current_user)):
    if not user.target_role:
        raise HTTPException(status_code=400, detail="Set a target role in your profile first")
    rag = get_rag()
    if not rag:
        raise HTTPException(status_code=503, detail="The career knowledge base is unavailable")
    try:
        result = json_completion(
            "You are a precise career-readiness analyst. Return only JSON and do not invent candidate skills.",
            f"Target role: {user.target_role}\nCandidate skills: {[s.skill for s in user.skills]}\n"
            f"Career context: {rag.search_job(user.target_role, top_k=2)[:1800]}\n"
            "Return {\"target_role\": string, \"readiness_percent\": integer 0-100, \"matched_skills\": [string], \"missing_skills\": [string]}.",
            max_tokens=400,
        )
        result["readiness_percent"] = max(0, min(100, int(result["readiness_percent"])))
        return CareerAnalysis(**result)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="The career model returned an unusable result") from exc
