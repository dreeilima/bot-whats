from app.main import app
from app.db.session import initialize_db
from app.db.migrations import run_migrations
from app.services.whatsapp import whatsapp_service

async def setup():
    # Inicializa banco
    initialize_db()
    run_migrations()
    
    # Inicializa WhatsApp
    await whatsapp_service.initialize()
    
    # Inicia servidor
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup())
