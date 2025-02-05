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

def log_environment():
    """Loga informações do ambiente"""
    logger = logging.getLogger(__name__)
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

# Força usar o pooler em vez do db direto
if 'db.xkepzvrnevgeifexcizr.supabase.co' in DATABASE_URL:
    logger.warning("Convertendo URL do banco para usar pooler...")
    DATABASE_URL = DATABASE_URL.replace(
        'db.xkepzvrnevgeifexcizr.supabase.co:5432',
        'aws-0-us-west-1.pooler.supabase.com:6543'
    )

# Adiciona SSL se necessário
if 'sslmode' not in DATABASE_URL:
    parsed = urllib.parse.urlparse(DATABASE_URL)
    if parsed.scheme in ('postgres', 'postgresql'):
        params = dict(urllib.parse.parse_qsl(parsed.query))
        params['sslmode'] = 'require'
        DATABASE_URL = parsed._replace(
            query=urllib.parse.urlencode(params)
        ).geturl()

logger.info("URL final do banco: %s", DATABASE_URL)

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
    """Atualiza/cria modelos"""
    from app.db.models import User, Category, Account, Transaction, Bill, Goal
    
    max_retries = 5
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            # Testa conexão primeiro
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logging.info("Conexão com banco estabelecida com sucesso")
                
                # Cria as tabelas em ordem específica
                tables = [
                    User.__table__,
                    Category.__table__,
                    Account.__table__,
                    Transaction.__table__,
                    Bill.__table__,
                    Goal.__table__
                ]
                
                # Cria uma tabela por vez na ordem correta
                for table in tables:
                    try:
                        table.create(engine)
                        logging.info(f"Tabela {table.name} criada com sucesso")
                    except Exception as e:
                        if "already exists" not in str(e):
                            logging.error(f"Erro ao criar {table.name}: {str(e)}")
                            raise e
                        logging.info(f"Tabela {table.name} já existe")
                        
                # Executa migrações após criar as tabelas
                from app.db.migrations import run_migrations
                run_migrations()
                        
                logging.info("Banco de dados inicializado com sucesso!")
                return
                
        except Exception as e:
            retry_count += 1
            last_error = e
            if retry_count < max_retries:
                wait_time = retry_count * 5  # Aumenta o tempo de espera a cada tentativa
                logging.warning(f"Tentativa {retry_count} falhou, tentando novamente em {wait_time}s... Erro: {str(e)}")
                time.sleep(wait_time)
            else:
                logging.error(f"Todas as {max_retries} tentativas falharam. Último erro: {str(last_error)}")
                raise last_error

# Inicializa o banco
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