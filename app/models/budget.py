from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    category: str
    limit_amount: Decimal
    period: str = Field(default="monthly")  # monthly, yearly
    created_at: datetime = Field(default_factory=datetime.utcnow) 