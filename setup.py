import os
import logging
import time
from app.db.session import initialize_db
from app.db.migrations import run_migrations
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Aguarda banco inicializar
        time.sleep(5)
        
        # Inicializa banco
        initialize_db()
        
        # Executa migrações
        run_migrations()
        
        # Inicia servidor
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        
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
