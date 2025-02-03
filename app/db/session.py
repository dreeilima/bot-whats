"""
    Esse código é responsável a criar e gerenciar
o banco de dados utilizando sqlalchemy.

author: github.com/gustavosett
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel
from sqlalchemy_utils import database_exists, create_database

from app.services.config import DATABASE_URL, FORCE_DB_INIT

# Conexão
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

def get_session():
    return Session(engine)

SessionLocal = get_session

def initialize_db():
    """Atualiza/cria modelos"""
    from app.db.models import User, Account, Transaction, Bill  # Importa todos os modelos
    
    # Cria/atualiza todas as tabelas
    SQLModel.metadata.create_all(engine)

# Dependencia
if not database_exists(engine.url):
    create_database(engine.url)

# Sempre inicializa/atualiza o banco
initialize_db()

def get_db():
    """certifica que o banco de dados seja fechado ao final de cada request"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """certifica que o banco de dados seja fechado ao final de cada request"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()