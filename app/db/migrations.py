from sqlalchemy import text
from app.db.session import engine
import logging

def run_migrations():
    """Executa migrações necessárias no banco de dados"""
    try:
        with engine.connect() as conn:
            # Remove coluna antiga 'category' se existir
            try:
                conn.execute(text("""
                    ALTER TABLE transaction 
                    DROP COLUMN IF EXISTS category;
                """))
            except:
                pass

            # Adiciona coluna owner_id em transaction se não existir
            conn.execute(text("""
                ALTER TABLE transaction 
                ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES "user"(id);
            """))
            
            # Adiciona coluna category_id em transaction se não existir
            conn.execute(text("""
                ALTER TABLE transaction 
                ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES category(id);
            """))
            
            # Adiciona coluna category_id em bill se não existir
            conn.execute(text("""
                ALTER TABLE bill 
                ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES category(id);
            """))
            
            # Adiciona coluna owner_id em bill se não existir
            conn.execute(text("""
                ALTER TABLE bill 
                ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES "user"(id);
            """))
            
            # Adiciona outras colunas necessárias
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS whatsapp VARCHAR(20);
            """))
            
            conn.commit()
            logging.info("Migrações executadas com sucesso")
    except Exception as e:
        logging.warning(f"Erro ao executar migração (pode ser ignorado na primeira execução): {str(e)}")
        # Não propaga o erro
        pass 