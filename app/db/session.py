"""
    Esse código é responsável a criar e gerenciar
o banco de dados utilizando sqlalchemy.

author: github.com/gustavosett
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlmodel import SQLModel
from sqlalchemy_utils import database_exists, create_database
from decouple import config
import urllib.parse

from app.services.config import DATABASE_URL, FORCE_DB_INIT

# Ajusta a URL do banco para usar SSL
DATABASE_URL = config('DATABASE_URL')
if 'sslmode' not in DATABASE_URL:
    parsed = urllib.parse.urlparse(DATABASE_URL)
    if parsed.scheme == 'postgres':
        # Adiciona sslmode se não existir
        params = dict(urllib.parse.parse_qsl(parsed.query))
        params['sslmode'] = 'require'
        DATABASE_URL = parsed._replace(
            query=urllib.parse.urlencode(params)
        ).geturl()

# Cria engine com timeout maior
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 30,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

# Cria sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return Session(engine)

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