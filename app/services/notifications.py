from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import User, Bill, Transaction, Goal
from app.services.whatsapp import WhatsAppService

class NotificationService:
    def __init__(self, whatsapp_service: WhatsAppService):
        self.whatsapp = whatsapp_service

    async def check_bills(self, user: User, db: Session):
        """Verifica contas próximas do vencimento"""
        tomorrow = datetime.now() + timedelta(days=1)
        
        bills = db.query(Bill).filter(
            Bill.owner_id == user.id,
            Bill.is_paid == False,
            Bill.due_date <= tomorrow
        ).all()
        
        if bills:
            message = "⚠️ Contas próximas do vencimento:\n\n"
            for bill in bills:
                message += f"- {bill.description}: R$ {bill.amount:.2f} "
                message += f"(vence em {bill.due_date.strftime('%d/%m')})\n"
            
            await self.whatsapp.send_message(user.whatsapp, message)

    async def check_balance_alerts(self, user: User, db: Session):
        """Verifica alertas de saldo"""
        for account in user.accounts:
            if account.balance < 100:
                message = f"⚠️ Alerta de saldo baixo na conta {account.name}:\n"
                message += f"Saldo atual: R$ {account.balance:.2f}"
                await self.whatsapp.send_message(user.whatsapp, message)

    async def check_goals(self, user: User, db: Session):
        """Verifica progresso das metas"""
        for goal in user.goals:
            days_left = (goal.deadline - datetime.now()).days
            if days_left <= 30:
                progress = (goal.current_amount / goal.target_amount) * 100
                message = f"🎯 Meta: {goal.name}\n"
                message += f"Progresso: {progress:.1f}%\n"
                message += f"Faltam {days_left} dias para o prazo final!"
                await self.whatsapp.send_message(user.whatsapp, message)

    async def send_monthly_report(self, user: User, db: Session):
        """Envia relatório mensal"""
        from app.services.analytics import FinancialAnalytics
        
        summary = await FinancialAnalytics.monthly_summary(user, db)
        insights = await FinancialAnalytics.generate_insights(user, db)
        
        message = "📊 Relatório Mensal\n\n"
        message += f"💰 Receitas: R$ {summary['total_income']:.2f}\n"
        message += f"💸 Despesas: R$ {summary['total_expense']:.2f}\n"
        message += f"📈 Saldo: R$ {summary['balance']:.2f}\n\n"
        
        if insights:
            message += "💡 Insights:\n"
            for insight in insights:
                message += f"- {insight}\n"
        
        await self.whatsapp.send_message(user.whatsapp, message)

    async def send_alert(self, user: User, message: str):
        """Envia alerta genérico"""
        await self.whatsapp.send_message(user.whatsapp, message) 