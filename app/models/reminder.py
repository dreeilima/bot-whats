from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    description: str
    amount: Decimal
    due_date: int  # Dia do mês
    category: Optional[str]
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)