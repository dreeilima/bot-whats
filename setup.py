import os
import logging
from app.main import app
import uvicorn
from app.db.session import initialize_db
from app.db.migrations import run_migrations
from app.services.whatsapp import whatsapp_service
import time

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Aguarda mais tempo para o banco estar pronto em produção
        if os.getenv('ENVIRONMENT') == 'production':
            logger.info("Ambiente de produção detectado, aguardando 30s...")
            time.sleep(30)
        else:
            logger.info("Aguardando banco de dados inicializar...")
            time.sleep(10)
        
        # Inicializa o banco
        initialize_db()
        run_migrations()
        
        # Configura host e porta
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "10000"))
        
        logger.info(f"Iniciando servidor em {host}:{port}")
        
        # Inicia o servidor
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False
        )
        
    except Exception as e:
        logger.error(f"Erro fatal na inicialização: {str(e)}")
        raise e

if __name__ == "__main__":
    main()
