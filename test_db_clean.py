from sqlalchemy import text
from app.db.session import engine
import logging

def clean_database():
    """Limpa todas as tabelas do banco"""
    try:
        with engine.connect() as conn:
            # Desabilita verificação de chave estrangeira temporariamente
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED;"))
            
            # Limpa todas as tabelas
            tables = [
                "transaction",
                "bill",
                "goal",
                "account",
                "category",
                "user"
            ]
            
            for table in tables:
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))
            
            conn.commit()
            logging.info("Banco de dados limpo com sucesso")
            return True
    except Exception as e:
        logging.error(f"Erro ao limpar banco: {str(e)}")
        return False 