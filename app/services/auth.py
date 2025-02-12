from fastapi import HTTPException
from app.models import User
from app.database import get_session
from sqlmodel import select

async def authenticate_user(phone: str) -> User:
    """Autentica ou registra um usuário pelo número do WhatsApp"""
    async with get_session() as session:
        # Busca usuário
        query = select(User).where(User.phone == phone)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Registra novo usuário
            user = User(phone=phone, name=f"User_{phone[-4:]}")
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
        return user 