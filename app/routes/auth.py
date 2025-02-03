from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.db.session import get_db
from app.db.models import User, Token
from app.services.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.services.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["auth"])

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Login OAuth2 com username e password.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Email ou senha incorretos"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=400, detail="Usuário inativo"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    } 