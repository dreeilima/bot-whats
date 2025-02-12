from typing import List, Optional
from app.models import Goal
from app.database import get_session
from sqlmodel import select
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

async def add_goal(
    user_id: int,
    name: str,
    target_amount: Decimal,
    category: str = "outros"
) -> Goal:
    """Adiciona uma nova meta"""
    try:
        async with get_session() as session:
            goal = Goal(
                user_id=user_id,
                name=name,
                target_amount=target_amount,
                category=category
            )
            session.add(goal)
            await session.commit()
            await session.refresh(goal)
            return goal
    except Exception as e:
        logger.error(f"Erro ao adicionar meta: {e}")
        raise

async def get_goals(user_id: int) -> List[Goal]:
    """Retorna todas as metas do usuário"""
    try:
        async with get_session() as session:
            query = select(Goal).where(Goal.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Erro ao buscar metas: {e}")
        raise

async def update_goal_progress(goal_id: int, amount: Decimal) -> Goal:
    """Atualiza progresso de uma meta"""
    try:
        async with get_session() as session:
            query = select(Goal).where(Goal.id == goal_id)
            result = await session.execute(query)
            goal = result.scalar_one()
            goal.current_amount += amount
            await session.commit()
            await session.refresh(goal)
            return goal
    except Exception as e:
        logger.error(f"Erro ao atualizar meta: {e}")
        raise