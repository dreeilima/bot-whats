from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: Decimal
    description: str
    type: str = Field(...)  # "income" ou "expense"
    category: str
    date: datetime = Field(default_factory=datetime.utcnow) 