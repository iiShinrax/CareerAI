"""PDF CV analysis using Jamal's local LLM, with no canned assessment."""

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import current_user
from ..services.llm_client import LLMUnavailable, json_completion

router = APIRouter(prefix="/api/cv", tags=["cv"])


def extract_text(file_bytes: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
        return "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(file_bytes)).pages)
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PyPDF2 is not installed") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The PDF could not be read") from exc


@router.post("/upload", response_model=schemas.CVOut, status_code=201)
async def upload_cv(file: UploadFile = File(...), user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    text = extract_text(await file.read())
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text was found in this PDF")
    try:
        analysis = json_completion(
            "You are a strict ATS and career reviewer. Return only JSON and base findings solely on the supplied CV.",
            f"Target role: {user.target_role or 'not provided'}\nCV:\n{text[:18000]}\n"
            "Return {\"score\": integer 0-100, \"extracted_skills\": [string], \"weaknesses\": [string], \"recommendations\": [string]}. Provide concise, specific feedback.",
        )
        analysis["score"] = max(0, min(100, int(analysis["score"])))
        for field in ("extracted_skills", "weaknesses", "recommendations"):
            if not isinstance(analysis[field], list):
                raise ValueError(f"invalid {field}")
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="The CV model returned an unusable result") from exc
    cv = models.CV(user_id=user.id, filename=file.filename, parsed_content=text[:20000], **analysis)
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


@router.get("/", response_model=list[schemas.CVOut])
def list_cvs(user: models.User = Depends(current_user)):
    return user.cvs
