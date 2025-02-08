from sqlalchemy import text
from app.db.session import engine
import logging

def run_migrations():
    """Executa migrações necessárias no banco de dados"""
    try:
        # Usa begin() para gerenciar a transação automaticamente
        with engine.begin() as conn:
            # Recria as tabelas (com aspas duplas no "user")
            tables = [
                'bill',
                'transaction',
                'category',
                'account',
                '"user"',  # Entre aspas por ser palavra reservada
                'goal'
            ]
            
            for table in tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    logging.info(f"Tabela {table} removida")
                except Exception as e:
                    logging.warning(f"Erro ao remover {table}: {str(e)}")
            
            # Não precisa do commit, o begin() já gerencia a transação
            logging.info("Tabelas antigas removidas")
            
            # As novas tabelas serão criadas automaticamente pelo SQLModel
            
    except Exception as e:
        logging.error(f"Erro ao executar migração: {str(e)}")
        raise e 