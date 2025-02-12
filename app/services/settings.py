from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.db.models import (
    User, CategoryLimit, NotificationSettings, 
    FinancialGoal, NotificationHistory
)

class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_or_create_notification_settings(self, user_id: int) -> NotificationSettings:
        """Obtém ou cria configurações de notificação para o usuário"""
        settings = self.db.query(NotificationSettings).filter(
            NotificationSettings.user_id == user_id
        ).first()
        
        if not settings:
            settings = NotificationSettings(user_id=user_id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            
        return settings

    async def update_category_limit(
        self, user_id: int, category: str, amount: float
    ) -> CategoryLimit:
        """Atualiza ou cria limite para categoria"""
        limit = self.db.query(CategoryLimit).filter(
            CategoryLimit.user_id == user_id,
            CategoryLimit.category == category
        ).first()
        
        if limit:
            limit.limit_amount = amount
            limit.updated_at = datetime.now()
        else:
            limit = CategoryLimit(
                user_id=user_id,
                category=category,
                limit_amount=amount
            )
            self.db.add(limit)
            
        self.db.commit()
        self.db.refresh(limit)
        return limit

    async def create_financial_goal(
        self, 
        user_id: int,
        name: str,
        target_amount: float,
        deadline: datetime,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> FinancialGoal:
        """Cria nova meta financeira"""
        goal = FinancialGoal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            deadline=deadline,
            category=category,
            description=description
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    async def update_goal_progress(
        self, goal_id: int, current_amount: float
    ) -> FinancialGoal:
        """Atualiza progresso de uma meta"""
        goal = self.db.get(FinancialGoal, goal_id)
        if goal:
            goal.current_amount = current_amount
            goal.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(goal)
        return goal

    async def log_notification(
        self, user_id: int, type: str, message: str
    ) -> NotificationHistory:
        """Registra nova notificação no histórico"""
        notification = NotificationHistory(
            user_id=user_id,
            type=type,
            message=message
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    async def mark_notification_as_read(
        self, notification_id: int
    ) -> NotificationHistory:
        """Marca notificação como lida"""
        notification = self.db.get(NotificationHistory, notification_id)
        if notification:
            notification.read = True
            self.db.commit()
            self.db.refresh(notification)
        return notification 