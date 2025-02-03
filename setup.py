from app.main import app
from app.db.session import initialize_db
from app.db.migrations import run_migrations

if __name__ == "__main__":
    # Inicializa/atualiza o banco
    initialize_db()
    
    # Executa migrações adicionais se necessário
    run_migrations()
    
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
