"""
    Esse código é o módulo principal do projeto, responsável por iniciar
todas funcionalidades do sistema.

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.database import init_db

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria aplicação FastAPI
app = FastAPI()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Importa e registra as rotas
from app.routes.whatsapp import router as whatsapp_router
logger.info(f"🔄 Registrando router WhatsApp: {whatsapp_router}")
app.include_router(whatsapp_router, prefix="/whatsapp")  # Com prefixo

@app.get("/")
def root():
    return {
        "message": "success",
        "response": "API is running"
    }

@app.get("/health")
def health():
    return {
        "message": "success",
        "response": "ok"
    }

# Eventos
@app.on_event("startup")
async def startup():
    try:
        await init_db()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
