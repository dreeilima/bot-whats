"""
    Esse código é responsável a criar e gerenciar
o banco de dados utilizando sqlalchemy.

author: github.com/gustavosett
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlmodel import SQLModel
from decouple import config
import urllib.parse
import logging
from sqlalchemy.sql import text
import time
import os

# Configura o logger
logger = logging.getLogger(__name__)

def log_environment():
    """Loga informações do ambiente"""
    logger.info("="*50)
    logger.info("Informações do ambiente:")
    logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'não definido')}")
    logger.info(f"HOST: {os.getenv('HOST', 'não definido')}")
    logger.info(f"PORT: {os.getenv('PORT', 'não definido')}")
    logger.info("="*50)

# No início do arquivo, após os imports
log_environment()
logger.info("URL original do banco: %s", config('DATABASE_URL'))

# Ajusta a URL do banco para usar SSL
DATABASE_URL = config('DATABASE_URL')

# Log da URL (mascarada)
masked_url = DATABASE_URL.replace(DATABASE_URL.split('@')[0], '***:***')
logger.info("URL do banco (mascarada): %s", masked_url)

# Cria engine com configurações para pooler
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
        "keepalives_count": 5,
        "application_name": "pixzinho_bot"
    }
)

# Cria sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return Session(engine)

def initialize_db():
    """Inicializa o banco de dados"""
    try:
        # Importa todos os modelos
        from app.db.models import User, Account, Category, Transaction, Bill, Goal
        
        # Cria todas as tabelas
        SQLModel.metadata.create_all(engine)
        
        # Testa a conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Conexão com banco estabelecida com sucesso")
            
            # Lista tabelas criadas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            logger.info(f"Tabelas existentes: {tables}")
            
        logger.info("Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {str(e)}")
        raise e

# Inicializa o banco
initialize_db()

def get_db():
    """Retorna uma sessão do banco"""
    db = SessionLocal()
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