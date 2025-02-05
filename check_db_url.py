import os
import logging
from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_url():
    """Verifica se a URL do banco está correta"""
    DATABASE_URL = config('DATABASE_URL', default='')
    
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL não está definida!")
        return False
        
    if 'db.xkepzvrnevgeifexcizr.supabase.co' in DATABASE_URL:
        logger.error("❌ URL está usando conexão direta ao invés do pooler!")
        return False
        
    if 'aws-0-us-west-1.pooler.supabase.com' not in DATABASE_URL:
        logger.error("❌ URL não está usando o pooler!")
        return False
        
    if ':6543' not in DATABASE_URL:
        logger.error("❌ Porta incorreta! Deve ser 6543")
        return False
        
    if 'sslmode=require' not in DATABASE_URL:
        logger.warning("⚠️ SSL não está configurado!")
        
    logger.info("✅ URL do banco parece correta!")
    logger.info(f"URL: {DATABASE_URL}")
    return True

if __name__ == "__main__":
    check_database_url() 