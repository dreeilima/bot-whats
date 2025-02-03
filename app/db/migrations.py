from sqlalchemy import text
from app.db.session import engine

def run_migrations():
    """Executa migrações necessárias no banco de dados"""
    with engine.connect() as conn:
        # Verifica se a coluna whatsapp existe
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='user' AND column_name='whatsapp';
        """))
        
        if not result.fetchone():
            # Adiciona a coluna whatsapp
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN whatsapp VARCHAR(20);
            """))
            conn.commit() 