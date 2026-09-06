"""
/api/auth — signup, login, logout.

Logout is stateless here (JWTs aren't stored server-side, so "logout"
just means the client discards its token). If you later want real
server-side session invalidation, add a token-blocklist table — not
needed for the MVP.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import hash_password, verify_password, create_access_token
from ..deps import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Uses OAuth2PasswordRequestForm so this also works directly from the
    FastAPI /docs "Authorize" button. The frontend just needs to POST
    form-encoded `username` (= email) and `password` fields.
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(user: models.User = Depends(current_user)):
    # Stateless JWT — nothing to invalidate server-side for the MVP.
    return {"detail": "Logged out"}


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(user: models.User = Depends(current_user)):
    return user
