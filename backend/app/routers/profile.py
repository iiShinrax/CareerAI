"""
/api/profile — profile fields (education, experience, target role, goals)
and the user's self-reported skills list.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/me", response_model=schemas.UserOut)
def get_profile(user: models.User = Depends(current_user)):
    return user


@router.put("/me", response_model=schemas.UserOut)
def update_profile(
    payload: schemas.ProfileUpdate,
    user: models.User = Depends(current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/skills", response_model=list[schemas.SkillOut])
def list_skills(user: models.User = Depends(current_user)):
    return user.skills


@router.post("/skills", response_model=schemas.SkillOut, status_code=201)
def add_skill(
    payload: schemas.SkillCreate,
    user: models.User = Depends(current_user),
    db: Session = Depends(get_db),
):
    skill = models.Skill(user_id=user.id, skill=payload.skill, level=payload.level)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
def delete_skill(
    skill_id: str,
    user: models.User = Depends(current_user),
    db: Session = Depends(get_db),
):
    skill = db.get(models.Skill, skill_id)
    if not skill or skill.user_id != user.id:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
