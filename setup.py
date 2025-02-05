from app.main import app
from app.db.session import initialize_db
from app.db.migrations import run_migrations
from app.services.whatsapp import whatsapp_service
import os
import logging
import time

async def setup():
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Tenta inicializar banco
            initialize_db()
            run_migrations()
            break
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                logging.error(f"Falha ao conectar ao banco após {max_retries} tentativas")
                raise e
            logging.warning(f"Tentativa {retry_count} falhou, tentando novamente em 5s...")
            time.sleep(5)
    
    # Inicializa WhatsApp
    await whatsapp_service.initialize()
    
    # Inicia servidor
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        reload=False  # Desativa reload em produção
    )

if __name__ == "__main__":
    import asyncio
    
    try:
        asyncio.run(setup())
    except Exception as e:
        logging.error(f"Erro fatal na inicialização: {str(e)}")
        raise
