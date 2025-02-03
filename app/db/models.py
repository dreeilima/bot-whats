from typing import Union, Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


class UserCreateOpen(SQLModel):
    email: EmailStr
    password: str
    full_name: Union[str, None] = None


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: Union[EmailStr, None] = None
    password: Union[str, None] = None


class UserUpdateMe(BaseModel):
    password: Union[str, None] = None
    full_name: Union[str, None] = None
    email: Union[EmailStr, None] = None

# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    whatsapp: Optional[str] = None  # Número do WhatsApp do usuário
    items: List["Item"] = Relationship(back_populates="owner")
    accounts: List["Account"] = Relationship(back_populates="owner")
    bills: List["Bill"] = Relationship(back_populates="owner")
    goals: List["Goal"] = Relationship(back_populates="owner")


# Properties to return via API, id is always required
class UserOut(UserBase):
    id: int


# Shared properties
class ItemBase(SQLModel):
    title: str
    description: Optional[str] = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: Union[str, None] = None


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemOut(ItemBase):
    id: int


# Generic message
class Message(BaseModel):
    message: str


# JSON payload containing access token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: Union[int, None] = None


class NewPassword(BaseModel):
    token: str
    new_password: str


class AccountBase(SQLModel):
    name: str
    balance: float = Field(default=0.0)
    type: str  # (corrente, poupança, investimento, etc)
    description: Optional[str] = None


class TransactionBase(SQLModel):
    amount: float
    description: str
    type: str  # "income" ou "expense"
    category: str
    date: datetime = Field(default_factory=datetime.utcnow)


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    type: str  # "expense" ou "income"
    icon: str = "💰"  # Emoji padrão
    description: Optional[str] = None
    
    transactions: List["Transaction"] = Relationship(back_populates="category")


# Atualizar Transaction
class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: Optional[int] = Field(foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="transactions")


class BillBase(SQLModel):
    description: str
    amount: float
    due_date: datetime
    is_paid: bool = False
    category: str


class Bill(BillBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    owner: User = Relationship(back_populates="bills")


# Atualizar Account para incluir transações
class Account(AccountBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    owner: User = Relationship(back_populates="accounts")
    transactions: List[Transaction] = Relationship(back_populates="account")


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: datetime
    owner_id: int = Field(foreign_key="user.id")
    owner: User = Relationship(back_populates="goals")


# Evita referência circular
User.update_forward_refs()
