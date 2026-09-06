"""Personalized roadmap generation using the RAG context and local LLM."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import models
from ..deps import current_user
from ..services.llm_client import LLMUnavailable, json_completion
from ..services.rag_client import get_rag

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


class RoadmapWeek(BaseModel):
    label: str
    topic: str
    progress: int


class RoadmapResponse(BaseModel):
    weeks: list[RoadmapWeek]


@router.get("/me", response_model=RoadmapResponse)
def get_roadmap(user: models.User = Depends(current_user)):
    if not user.target_role:
        raise HTTPException(status_code=400, detail="Set a target role in your profile first")
    rag = get_rag()
    if not rag:
        raise HTTPException(status_code=503, detail="The career knowledge base is unavailable")
    try:
        result = json_completion(
            "You create practical learning roadmaps. Return only JSON.",
            f"Target role: {user.target_role}\nCurrent skills: {[s.skill for s in user.skills]}\nCareer context: {rag.search_job(user.target_role, top_k=1)[:1200]}\n"
            "Create exactly four learning weeks. Return JSON only in this shape: "
            "{\"weeks\":[{\"label\":\"Week 1\",\"topic\":\"short topic\",\"progress\":0}, "
            "{\"label\":\"Week 2\",\"topic\":\"short topic\",\"progress\":0}, "
            "{\"label\":\"Week 3\",\"topic\":\"short topic\",\"progress\":0}, "
            "{\"label\":\"Week 4\",\"topic\":\"short topic\",\"progress\":0}]}.",
            max_tokens=700,
        )
        weeks = result["weeks"]
        if not isinstance(weeks, list) or len(weeks) != 4:
            raise ValueError("invalid roadmap")
        for week in weeks:
            week["progress"] = 0
        return RoadmapResponse(**result)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="The roadmap model returned an unusable result") from exc
