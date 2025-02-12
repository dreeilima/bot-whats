from app.models import Budget, Transaction
from app.database import get_session
from sqlmodel import select
from decimal import Decimal
from typing import List, Dict
from datetime import datetime, timedelta

async def set_budget(
    user_id: int,
    category: str,
    limit_amount: Decimal,
    period: str = "monthly"
) -> Budget:
    async with get_session() as session:
        budget = Budget(
            user_id=user_id,
            category=category,
            limit_amount=limit_amount,
            period=period
        )
        session.add(budget)
        await session.commit()
        await session.refresh(budget)
        return budget

async def get_budgets(user_id: int) -> List[Budget]:
    async with get_session() as session:
        query = select(Budget).where(Budget.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().all()

async def get_budget_status(user_id: int) -> Dict:
    async with get_session() as session:
        # Busca orçamentos
        budgets = await get_budgets(user_id)
        
        # Calcula gastos do mês atual
        start_date = datetime.now().replace(day=1)
        query = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= start_date
        )
        result = await session.execute(query)
        transactions = result.scalars().all()
        
        # Agrupa gastos por categoria
        expenses = {}
        for t in transactions:
            if t.category:
                expenses[t.category] = expenses.get(t.category, Decimal(0)) + t.amount
        
        # Compara com limites
        status = {}
        for budget in budgets:
            spent = expenses.get(budget.category, Decimal(0))
            status[budget.category] = {
                "limit": budget.limit_amount,
                "spent": spent,
                "remaining": budget.limit_amount - spent,
                "percentage": (spent / budget.limit_amount * 100) if budget.limit_amount else 0
            }
        
        return status 