import os
import sys
import logging
from check_db_url import check_database_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Verifica variáveis de ambiente necessárias"""
    required_vars = ['DATABASE_URL']  # Sempre requerida
    
    # Variáveis adicionais apenas em produção
    if os.getenv('ENVIRONMENT') == 'production':
        required_vars.extend([
            'PORT',
            'HOST',
            'ENVIRONMENT'
        ])
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            
    if missing:
        logger.error(f"❌ Variáveis de ambiente faltando: {', '.join(missing)}")
        return False
        
    # Log das variáveis encontradas
    logger.info("Variáveis de ambiente encontradas:")
    for var in ['DATABASE_URL', 'PORT', 'HOST', 'ENVIRONMENT']:
        value = os.getenv(var, 'não definido')
        # Mascara a senha na DATABASE_URL
        if var == 'DATABASE_URL' and value != 'não definido':
            masked = value.replace(value.split('@')[0], '***:***')
            logger.info(f"{var}: {masked}")
        else:
            logger.info(f"{var}: {value}")
            
    return True

def main():
    """Executa todas as verificações"""
    logger.info("="*50)
    logger.info("Iniciando verificações de pré-deploy...")
    logger.info("="*50)
    
    checks = [
        ('Variáveis de ambiente', check_environment()),
        ('URL do banco', check_database_url())
    ]
    
    failed = False
    for name, result in checks:
        if not result:
            logger.error(f"❌ {name} falhou!")
            failed = True
            
    if failed:
        logger.error("="*50)
        logger.error("❌ Verificações falharam!")
        logger.error("="*50)
        sys.exit(1)
    else:
        logger.info("="*50)
        logger.info("✅ Todas as verificações passaram!")
        logger.info("="*50)

if __name__ == "__main__":
    main() 