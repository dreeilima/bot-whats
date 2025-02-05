import psycopg2
import logging
import time
from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pega a URL do .env
DATABASE_URL = config('DATABASE_URL')

def test_connection(url):
    try:
        # Mascara a senha para o log
        masked_url = url.replace(url.split('@')[0], '***:***')
        logger.info(f"\n🔍 Testando conexão com: {masked_url}")
        
        # Tenta conectar
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        # Testa SELECT básico
        cur.execute('SELECT 1')
        logger.info("✅ SELECT básico OK")
        
        # Verifica usuário e banco
        cur.execute('SELECT current_user, current_database()')
        user, db = cur.fetchone()
        logger.info(f"✅ Usuário: {user}, Banco: {db}")
        
        # Verifica versão
        cur.execute('SELECT version()')
        version = cur.fetchone()[0]
        logger.info(f"✅ Versão: {version}")
        
        # Testa permissões
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        logger.info(f"✅ Tabelas encontradas: {len(tables)}")
        
        cur.close()
        conn.close()
        logger.info("✅ Conexão fechada com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")
        return False

def main():
    logger.info("="*50)
    logger.info("Iniciando teste de conexão")
    logger.info("="*50)
    
    success = test_connection(DATABASE_URL)
    
    logger.info("="*50)
    if success:
        logger.info("✨ Teste completado com sucesso!")
    else:
        logger.error("❌ Teste falhou!")
    logger.info("="*50)

if __name__ == "__main__":
    main() 