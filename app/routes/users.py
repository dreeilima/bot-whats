from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_db
from app.db.models import User, UserCreate, UserOut
from app.services.security import get_password_hash, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserOut)
def create_user(*, db: Session = Depends(get_db), user_in: UserCreate):
    """
    Criar novo usuário.
    """
    # Verifica se já existe usuário com este email
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Este email já está registrado no sistema.",
        )
    
    # Cria novo usuário
    db_obj = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/me", response_model=UserOut)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obter usuário atual.
    """
    return current_user 