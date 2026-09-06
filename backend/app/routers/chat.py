"""Grounded AI chat backed by the RAG database and Jamal's local model."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import current_user
from ..services.llm_client import LLMUnavailable, complete
from ..services.rag_client import get_rag

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    grounded: bool


@router.post("/message", response_model=ChatResponse)
def send_chat_message(payload: ChatRequest, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="A message is required")
    rag = get_rag()
    if not rag:
        raise HTTPException(status_code=503, detail="The career knowledge base is unavailable")
    try:
        context = rag.search_job(payload.message[:1000])
        if not context.strip():
            raise HTTPException(status_code=404, detail="No relevant career context was found")
        reply = complete(
            "You are CareerAI, a concise and supportive career coach. Answer only from the supplied career context. If the context cannot support a claim, say that clearly and suggest a focused next question.",
            f"User profile: target role={user.target_role or 'not provided'}; skills={[skill.skill for skill in user.skills]}; experience={user.experience or 'not provided'}\nCareer context:\n{context[:6000]}\n\nUser question: {payload.message}",
            max_tokens=450,
        )
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    convo = None
    if payload.session_id:
        convo = db.query(models.Conversation).filter(models.Conversation.user_id == user.id, models.Conversation.session_id == payload.session_id).first()
    if not convo:
        convo = models.Conversation(user_id=user.id, messages=[])
        db.add(convo)
    now = datetime.now(timezone.utc).isoformat()
    convo.messages = (convo.messages or []) + [{"role": "user", "content": payload.message, "timestamp": now}, {"role": "assistant", "content": reply, "timestamp": now}]
    db.commit()
    db.refresh(convo)
    return ChatResponse(reply=reply, session_id=convo.session_id, grounded=True)
