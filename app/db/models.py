from typing import Union, Optional, List, Annotated
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


# Properties to receive via API on update
class UserUpdate(SQLModel):
    email: Union[EmailStr, None] = None
    password: Union[str, None] = None
    full_name: Union[str, None] = None


class UserOut(UserBase):
    id: int


# Base Account
class AccountBase(SQLModel):
    name: str
    balance: float = 0.0
    type: str = "checking"  # checking, savings, investment
    description: Optional[str] = None


# Base Category
class CategoryBase(SQLModel):
    name: str = Field(unique=False)
    type: str  # income, expense
    icon: str = "💰"  # Emoji padrão
    description: Optional[str] = None


# Base Transaction
class TransactionBase(SQLModel):
    amount: float
    type: str  # income, expense
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)
    account_id: int = Field(foreign_key="account.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")


# Base Bill
class BillBase(SQLModel):
    description: str
    amount: float
    due_date: datetime
    is_paid: bool = False
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")


# Token models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Union[int, None] = None


# Database Models
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    whatsapp: Optional[str] = None
    accounts: List["Account"] = Relationship(back_populates="owner")
    transactions: List["Transaction"] = Relationship(back_populates="owner")
    bills: List["Bill"] = Relationship(back_populates="owner")
    goals: List["Goal"] = Relationship(back_populates="owner")


class Account(AccountBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    owner: "User" = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(back_populates="account")


class Category(CategoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transactions: List["Transaction"] = Relationship(back_populates="category")
    bills: List["Bill"] = Relationship(back_populates="category")


class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    owner: "User" = Relationship(back_populates="transactions")
    account: "Account" = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")


class Bill(BillBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    owner: "User" = Relationship(back_populates="bills")
    category: Optional["Category"] = Relationship(back_populates="bills")


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: datetime
    owner_id: int = Field(foreign_key="user.id")
    owner: "User" = Relationship(back_populates="goals")


# SQLModel lida com as referências circulares automaticamente
SQLModel.update_forward_refs()
