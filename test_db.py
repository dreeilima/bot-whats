from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import urllib.parse

# Use a URL do pooler do Supabase com SSL
DATABASE_URL = "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def test_connection():
    try:
        # Cria engine com configurações básicas
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Cria uma sessão
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Testa a conexão com uma query simples
        try:
            result = session.execute(text("SELECT 1"))
            print("✅ Conexão com banco OK!")
            return True
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 