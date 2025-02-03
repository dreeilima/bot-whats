from sqlalchemy.orm import Session
from app.db.models import Transaction, Category
from app.services.notifications import NotificationService

class AutomationRules:
    @staticmethod
    async def apply_rules(transaction: Transaction, db: Session):
        """Aplica regras automáticas em transações"""
        # Categorização automática
        if "mercado" in transaction.description.lower():
            category = db.query(Category).filter(Category.name == "Alimentação").first()
            transaction.category = category
        
        # Alertas de gastos
        if transaction.type == "expense" and transaction.amount > 1000:
            await NotificationService.send_alert(
                transaction.account.owner,
                f"🚨 Alerta de gasto alto: R$ {transaction.amount:.2f} em {transaction.description}"
            ) 