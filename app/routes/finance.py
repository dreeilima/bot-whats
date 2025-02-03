from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import (
    User, 
    Account, 
    AccountBase,
    Transaction, 
    TransactionBase,
    Bill, 
    BillBase
)
from app.services.security import get_current_user

router = APIRouter(prefix="/finance", tags=["finance"])

# Rotas de Contas
@router.post("/accounts/")
def create_account(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    account: AccountBase
):
    """Criar nova conta"""
    db_account = Account(**account.dict(), owner_id=current_user.id)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.get("/accounts/", response_model=List[Account])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar todas as contas do usuário"""
    return db.query(Account).filter(Account.owner_id == current_user.id).all()

# Rotas de Transações
@router.post("/transactions/")
def create_transaction(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    transaction: TransactionBase,
    account_id: int
):
    """Criar nova transação"""
    # Verifica se a conta pertence ao usuário
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.owner_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    # Cria a transação
    db_transaction = Transaction(**transaction.dict(), account_id=account_id)
    db.add(db_transaction)
    
    # Atualiza o saldo da conta
    if transaction.type == "income":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# Rotas de Contas a Pagar
@router.post("/bills/")
def create_bill(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bill: BillBase
):
    """Criar nova conta a pagar"""
    db_bill = Bill(**bill.dict(), owner_id=current_user.id)
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill

@router.get("/bills/pending")
def get_pending_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar contas a pagar pendentes"""
    return db.query(Bill).filter(
        Bill.owner_id == current_user.id,
        Bill.is_paid == False
    ).all()

@router.get("/export/transactions")
async def export_transactions(
    start_date: datetime,
    end_date: datetime,
    format: str = "csv",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exporta transações em CSV ou Excel"""
    transactions = db.query(Transaction).join(Account).filter(
        Account.owner_id == current_user.id,
        Transaction.date.between(start_date, end_date)
    ).all()
    
    if format == "csv":
        return create_csv(transactions)
    elif format == "excel":
        return create_excel(transactions) 