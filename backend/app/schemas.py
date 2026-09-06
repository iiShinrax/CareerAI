"""
Pydantic schemas — request/response shapes for the FastAPI layer.

Kept separate from models.py on purpose: models.py is the DB shape,
schemas.py is the API shape. E.g. we never return hashed_password,
and creation payloads don't include server-generated fields like id.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

from .models import SkillLevel


# ---------------- User ----------------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    education: str | None = None
    experience: str | None = None
    target_role: str | None = None
    career_goals: str | None = None
    created_at: datetime


class ProfileUpdate(BaseModel):
    education: str | None = None
    experience: str | None = None
    target_role: str | None = None
    career_goals: str | None = None


# ---------------- Skill ----------------

class SkillCreate(BaseModel):
    skill: str
    level: SkillLevel = SkillLevel.beginner


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    skill: str
    level: SkillLevel


# ---------------- CV ----------------

class CVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    score: float | None = None
    extracted_skills: list | None = None
    weaknesses: list | None = None
    recommendations: list | None = None
    uploaded_at: datetime


# ---------------- Interview ----------------

class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_role: str
    date: datetime
    score: float | None = None
    technical_score: float | None = None
    communication_score: float | None = None
    projects_score: float | None = None
    problem_solving_score: float | None = None
    strengths: list | None = None
    improvements: list | None = None


class InterviewStartResponse(BaseModel):
    interview_id: str
    questions: list[str]


class InterviewAnswer(BaseModel):
    question: str
    answer: str


class InterviewSubmitRequest(BaseModel):
    answers: list[InterviewAnswer]


class EvaluationResult(BaseModel):
    score: int
    technical_score: int
    communication_score: int
    projects_score: int
    problem_solving_score: int
    strengths: list[str]
    improvements: list[str]


# ---------------- Conversation ----------------

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime | None = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    messages: list[ChatMessage] | None = None
    updated_at: datetime
