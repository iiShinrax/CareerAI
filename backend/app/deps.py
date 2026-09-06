"""
Shared FastAPI dependencies — currently just current-user resolution.

Use `current_user` as a dependency on any route that should be
"protected" (require login):

    @router.get("/api/profile/me")
    def read_profile(user: models.User = Depends(current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_access_token
from . import models

# tokenUrl just documents where a client gets a token (for the OpenAPI docs UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(models.User, user_id)
    if user is None:
        raise credentials_error

    return user
