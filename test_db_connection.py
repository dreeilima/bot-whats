import psycopg2
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs para testar
urls = [
    # URL normal
    "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@db.xkepzvrnevgeifexcizr.supabase.co:5432/postgres",
    
    # URL com pooler
    "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
    
    # URL com SSL
    "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@db.xkepzvrnevgeifexcizr.supabase.co:5432/postgres?sslmode=require",
    
    # URL com pooler e SSL
    "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require",
    
    # URL com IP direto e SSL
    "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@54.177.55.191:6543/postgres?sslmode=require"
]

def test_connection(url):
    try:
        logger.info(f"Testando conexão com: {url}")
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()
        logger.info(f"✅ Conexão bem sucedida! Versão: {version}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao conectar: {str(e)}")
        return False

def main():
    for url in urls:
        logger.info("\n" + "="*50)
        success = test_connection(url)
        if success:
            logger.info(f"✨ URL que funcionou: {url}")
        time.sleep(2)  # Espera 2s entre tentativas

if __name__ == "__main__":
    main() 