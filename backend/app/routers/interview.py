"""Dynamic interview generation and strict evaluation from Jamal's LLM flow."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import current_user
from ..services.llm_client import LLMUnavailable, json_completion
from ..services.rag_client import get_rag

interview_router = APIRouter(prefix="/api/interview", tags=["interview"])
evaluation_router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


def _fallback_questions(user: models.User) -> list[str]:
    role = user.target_role or "your target role"
    return [
        f"What are the most important technical skills for a {role}, and how have you used them?",
        f"Describe a difficult technical problem you solved while preparing for {role}.",
        "Tell me about a project you built, your responsibilities, and the result.",
        "Describe a time you received difficult feedback and how you responded.",
        "How would you investigate and fix a feature that works locally but fails in production?",
    ]


def _context_for(user: models.User) -> str:
    rag = get_rag()
    if not rag:
        raise HTTPException(status_code=503, detail="The career knowledge base is unavailable")
    return rag.search_job(user.target_role or "", top_k=1)[:1400]


@interview_router.post("/start", response_model=schemas.InterviewStartResponse)
def start_interview(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    # Start immediately with role-aware questions; local model scoring happens after answers are submitted.
    questions = _fallback_questions(user)
    interview = models.Interview(user_id=user.id, target_role=user.target_role or "Unspecified role", transcript=[])
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return schemas.InterviewStartResponse(interview_id=interview.id, questions=questions)


@interview_router.post("/{interview_id}/submit", response_model=schemas.EvaluationResult)
def submit_interview(interview_id: str, payload: schemas.InterviewSubmitRequest, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    interview = db.get(models.Interview, interview_id)
    if not interview or interview.user_id != user.id:
        raise HTTPException(status_code=404, detail="Interview not found")
    if not payload.answers:
        raise HTTPException(status_code=400, detail="At least one answer is required")
    try:
        context = _context_for(user)
        result = json_completion(
            "You are a strict technical and HR evaluator. Return only JSON; do not reward unsupported claims.",
            f"Role: {interview.target_role}\nRelevant job context: {context}\nInterview answers: {[answer.model_dump() for answer in payload.answers]}\nReturn exactly {{\"score\": integer 0-100, \"technical_score\": integer 0-100, \"communication_score\": integer 0-100, \"projects_score\": integer 0-100, \"problem_solving_score\": integer 0-100, \"strengths\": [string], \"improvements\": [string]}}. Give specific evidence-based strengths and improvements.",
            max_tokens=700,
        )
        for field in ("score", "technical_score", "communication_score", "projects_score", "problem_solving_score"):
            result[field] = max(0, min(100, int(result[field])))
        if not isinstance(result["strengths"], list) or not isinstance(result["improvements"], list):
            raise ValueError("invalid feedback lists")
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="The evaluation model returned an unusable result") from exc
    interview.transcript = [answer.model_dump() for answer in payload.answers]
    for field, value in result.items():
        setattr(interview, field, value)
    db.commit()
    return schemas.EvaluationResult(**result)


@evaluation_router.get("/{interview_id}", response_model=schemas.EvaluationResult)
def get_evaluation(interview_id: str, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    interview = db.get(models.Interview, interview_id)
    if not interview or interview.user_id != user.id:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.score is None:
        raise HTTPException(status_code=409, detail="Interview not submitted yet")
    return schemas.EvaluationResult(score=int(interview.score), technical_score=int(interview.technical_score), communication_score=int(interview.communication_score), projects_score=int(interview.projects_score), problem_solving_score=int(interview.problem_solving_score), strengths=interview.strengths, improvements=interview.improvements)
