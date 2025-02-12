from typing import List, Optional
from app.models import Reminder
from app.database import get_session
from sqlmodel import select
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

async def add_reminder(
    user_id: int,
    description: str,
    amount: Decimal,
    due_date: int,
    category: str = None
) -> Reminder:
    """Adiciona um novo lembrete"""
    try:
        async with get_session() as session:
            reminder = Reminder(
                user_id=user_id,
                description=description,
                amount=amount,
                due_date=due_date,
                category=category
            )
            session.add(reminder)
            await session.commit()
            await session.refresh(reminder)
            return reminder
    except Exception as e:
        logger.error(f"Erro ao adicionar lembrete: {e}")
        raise

async def get_reminders(user_id: int) -> List[Reminder]:
    """Retorna todos os lembretes ativos do usuário"""
    try:
        async with get_session() as session:
            query = select(Reminder).where(
                Reminder.user_id == user_id,
                Reminder.is_active == True
            )
            result = await session.execute(query)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Erro ao buscar lembretes: {e}")
        raise

async def deactivate_reminder(reminder_id: int):
    """Desativa um lembrete"""
    try:
        async with get_session() as session:
            query = select(Reminder).where(Reminder.id == reminder_id)
            result = await session.execute(query)
            reminder = result.scalar_one()
            reminder.is_active = False
            await session.commit()
    except Exception as e:
        logger.error(f"Erro ao desativar lembrete: {e}")
        raise