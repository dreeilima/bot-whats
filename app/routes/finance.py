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
    BillBase,
    Category,
    CategoryBase,
    Goal
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
    transaction: TransactionBase
):
    """Criar nova transação"""
    # Verifica se a conta existe e pertence ao usuário
    account = db.query(Account).filter(
        Account.id == transaction.account_id,
        Account.owner_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    # Verifica se a categoria existe (se fornecida)
    if transaction.category_id:
        category = db.query(Category).filter(Category.id == transaction.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")

    # Cria a transação
    db_transaction = Transaction(
        **transaction.dict(),
        owner_id=current_user.id
    )
    
    # Atualiza o saldo da conta
    if transaction.type == "income":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount
    
    db.add(db_transaction)
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

# Rotas de Categorias
@router.post("/categories/")
def create_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: CategoryBase
):
    """Criar nova categoria"""
    # Verifica se já existe
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        return existing
        
    # Cria nova categoria
    db_category = Category(
        name=category.name,
        type=category.type,
        icon=category.icon,
        description=category.description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[Category])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar todas as categorias"""
    return db.query(Category).all()

@router.get("/categories/{category_id}", response_model=Category)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter categoria por ID"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return category

# Rotas de Metas
@router.post("/goals/")
def create_goal(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    goal: Goal
):
    """Criar nova meta"""
    db_goal = Goal(
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        deadline=goal.deadline,
        owner_id=current_user.id
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.get("/goals/", response_model=List[Goal])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar todas as metas do usuário"""
    return db.query(Goal).filter(Goal.owner_id == current_user.id).all()

@router.get("/goals/{goal_id}", response_model=Goal)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter meta por ID"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.owner_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    return goal

@router.put("/goals/{goal_id}/update-amount")
def update_goal_amount(
    goal_id: int,
    amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar valor atual da meta"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.owner_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
        
    goal.current_amount = amount
    db.commit()
    db.refresh(goal)
    return goal 