"""
CareerAI database models.

Maps to the tables from the project spec:
    User, Skills, CV, Interviews, Conversation

A few additions beyond the bare spec (marked with comments) are there
because the dashboard / results pages need them — e.g. per-category
interview scores, CV weaknesses/recommendations as structured data
instead of plain text.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Integer,
    Float,
    DateTime,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    education: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    career_goals: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # relationships
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    cvs: Mapped[list["CV"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Skills (self-reported profile skills — feeds the dashboard skill bar
# and the job-matching "Matched / Missing" comparison)
# ---------------------------------------------------------------------------

class SkillLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

    skill: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[SkillLevel] = mapped_column(
        SAEnum(SkillLevel), default=SkillLevel.beginner
    )

    user: Mapped["User"] = relationship(back_populates="skills")


# ---------------------------------------------------------------------------
# CV
# ---------------------------------------------------------------------------

class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    parsed_content: Mapped[str | None] = mapped_column(Text, nullable=True)  # raw extracted text

    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    extracted_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="cvs")


# ---------------------------------------------------------------------------
# Interviews
# ---------------------------------------------------------------------------

class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

    target_role: Mapped[str] = mapped_column(String(120), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # per-category breakdown shown on the Interview Results page
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    projects_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    problem_solving_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    improvements: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["Deployment", ...]

    # full Q&A transcript for this interview session, e.g.
    # [{"question": "...", "answer": "...", "feedback": "..."}]
    transcript: Mapped[list | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="interviews")


# ---------------------------------------------------------------------------
# Conversation (AI chat interface sessions)
# ---------------------------------------------------------------------------

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(36), default=new_uuid, index=True)

    # [{"role": "user"|"assistant", "content": "...", "timestamp": "..."}]
    messages: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
