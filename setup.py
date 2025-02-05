import os
import logging
from app.main import app
import uvicorn
from app.db.session import initialize_db
from app.db.migrations import run_migrations
from app.services.whatsapp import whatsapp_service
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Inicializa o banco
        initialize_db()
        run_migrations()
        
        # Configura host e porta
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "10000"))
        
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
