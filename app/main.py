"""
    Esse código é o módulo principal do projeto, responsável por iniciar
todas funcionalidades do sistema.

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging
from app.database import init_db

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria aplicação FastAPI
app = FastAPI(
    title="Bot WhatsApp",
    description="API para bot de WhatsApp com gestão financeira",
    version="1.0.0"
)

# Configuração CORS mais permissiva
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Rota raiz redirecionando para docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Rota de status
@app.get("/status")
async def status():
    return {
        "status": "online",
        "version": "1.0.0"
    }

# Importa e registra as rotas
from app.routes.whatsapp import router as whatsapp_router
logger.info(f"🔄 Registrando router WhatsApp: {whatsapp_router}")
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])

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
