from typing import Optional, List
from app.models import Transaction
from app.database import get_session
from sqlmodel import select
import logging
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_balance(user_id: int) -> Decimal:
    """Calcula o saldo atual do usuário"""
    try:
        async with get_session() as session:
            # Busca receitas
            query = select(Transaction.amount).where(
                Transaction.user_id == user_id,
                Transaction.type == "income"
            )
            result = await session.execute(query)
            income = sum([r[0] for r in result]) or Decimal(0)
            
            # Busca despesas
            query = select(Transaction.amount).where(
                Transaction.user_id == user_id,
                Transaction.type == "expense"
            )
            result = await session.execute(query)
            expenses = sum([r[0] for r in result]) or Decimal(0)
            
            return income - expenses
            
    except Exception as e:
        logger.error(f"Erro ao calcular saldo: {e}")
        raise

async def get_transactions(user_id: int, limit: int = 10) -> List[Transaction]:
    """Retorna as últimas transações do usuário"""
    try:
        async with get_session() as session:
            query = (
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.date.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()
            
    except Exception as e:
        logger.error(f"Erro ao buscar transações: {e}")
        raise

async def add_transaction(
    user_id: int,
    amount: Decimal,
    description: str,
    type: str,
    category: str = "outros"
) -> Transaction:
    """Adiciona uma nova transação"""
    try:
        async with get_session() as session:
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                description=description,
                type=type,
                category=category
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            return transaction
            
    except Exception as e:
        logger.error(f"Erro ao adicionar transação: {e}")
        raise

async def delete_transaction(user_id: int, transaction_id: int) -> Optional[Transaction]:
    """Exclui uma transação"""
    try:
        async with get_session() as session:
            # Busca transação
            query = select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
            result = await session.execute(query)
            transaction = result.scalar_one_or_none()
            
            if transaction:
                await session.delete(transaction)
                await session.commit()
                
            return transaction
            
    except Exception as e:
        logger.error(f"Erro ao excluir transação: {e}")
        raise 