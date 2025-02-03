from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import User, Account, Transaction, Category, Bill

class FinancialAnalytics:
    @staticmethod
    async def monthly_summary(user: User, db: Session) -> Dict:
        """Gera resumo mensal de gastos e receitas"""
        month_start = datetime.now().replace(day=1, hour=0, minute=0)
        
        transactions = db.query(Transaction).join(Account).filter(
            Account.owner_id == user.id,
            Transaction.date >= month_start
        ).all()
        
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        
        by_category = defaultdict(float)
        for t in transactions:
            category_name = t.category.name if t.category else "Sem categoria"
            by_category[category_name] += t.amount
        
        # Calcula percentuais por categoria
        category_percentages = {}
        total = total_income + total_expense
        if total > 0:
            for category, amount in by_category.items():
                category_percentages[category] = (amount / total) * 100
        
        return {
            "period": f"{month_start.strftime('%B/%Y')}",
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "by_category": dict(by_category),
            "category_percentages": category_percentages,
            "savings_rate": ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        }

    @staticmethod
    async def spending_trends(user: User, db: Session, months: int = 6) -> List[Dict]:
        """Analisa tendências de gastos nos últimos meses"""
        start_date = datetime.now() - timedelta(days=30 * months)
        
        # Busca transações agrupadas por mês
        monthly_transactions = db.query(
            func.date_trunc('month', Transaction.date).label('month'),
            Transaction.type,
            func.sum(Transaction.amount).label('total')
        ).join(Account).filter(
            Account.owner_id == user.id,
            Transaction.date >= start_date
        ).group_by(
            func.date_trunc('month', Transaction.date),
            Transaction.type
        ).all()
        
        # Organiza os dados por mês
        trends = []
        for month, type_, total in monthly_transactions:
            trends.append({
                "month": month.strftime("%B/%Y"),
                "type": type_,
                "total": float(total)
            })
        
        return trends

    @staticmethod
    async def budget_analysis(user: User, db: Session) -> Dict:
        """Analisa o orçamento atual vs. gastos reais"""
        month_start = datetime.now().replace(day=1, hour=0, minute=0)
        
        # Busca gastos reais
        actual_expenses = db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).join(Account).filter(
            Account.owner_id == user.id,
            Transaction.date >= month_start,
            Transaction.type == "expense"
        ).group_by(Category.name).all()
        
        # Aqui você implementaria a comparação com o orçamento planejado
        # Por enquanto, retornamos apenas os gastos reais
        return {
            "period": month_start.strftime("%B/%Y"),
            "expenses": {name: float(total) for name, total in actual_expenses}
        }

    @staticmethod
    async def generate_insights(user: User, db: Session) -> List[str]:
        """Gera insights personalizados baseados nos dados financeiros"""
        insights = []
        
        # Análise do mês atual
        summary = await FinancialAnalytics.monthly_summary(user, db)
        
        # Verifica taxa de poupança
        if summary["savings_rate"] < 10:
            insights.append("💡 Sua taxa de poupança está abaixo do recomendado (10%). "
                          "Considere revisar seus gastos.")
        
        # Verifica categorias com gastos altos
        for category, percentage in summary["category_percentages"].items():
            if percentage > 30:
                insights.append(f"⚠️ A categoria {category} representa {percentage:.1f}% "
                              f"dos seus gastos. Considere reduzir.")
        
        # Verifica saldo negativo
        if summary["balance"] < 0:
            insights.append("🚨 Seu saldo está negativo este mês. "
                          "Urgent: revise seus gastos.")
        
        return insights 