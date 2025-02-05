from sqlalchemy import text
from app.db.session import engine
import logging

def recreate_database():
    """Recria o banco do zero"""
    try:
        with engine.connect() as conn:
            # Desabilita verificação de chave estrangeira temporariamente
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED;"))
            
            # Remove todas as tabelas
            tables = [
                "transaction",
                "bill",
                "goal",
                "account",
                "category",
                "user"
            ]
            
            for table in tables:
                try:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                except:
                    pass
            
            conn.commit()
            logging.info("Tabelas removidas com sucesso")
            
            # Recria as tabelas
            from app.db.session import initialize_db
            initialize_db()
            
            return True
    except Exception as e:
        logging.error(f"Erro ao recriar banco: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = recreate_database()
    exit(0 if success else 1) 