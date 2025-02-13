"""
    Esse código é o módulo principal do projeto, responsável por iniciar
todas funcionalidades do sistema.

"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
from app.database import init_db

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configura diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Cria diretório de templates se não existir
os.makedirs(TEMPLATES_DIR, exist_ok=True)

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

# Configura templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Rota raiz redirecionando para docs
@app.get("/")
async def root():
    logger.info("👋 Acesso à rota raiz")
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
logger.info("🔄 Registrando rotas WhatsApp")
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])

@app.get("/health")
async def health():
    logger.info("💓 Verificação de saúde")
    return {"status": "healthy"}

# Eventos
@app.on_event("startup")
async def startup():
    try:
        logger.info("🚀 Iniciando aplicação...")
        logger.info(f"📁 Templates dir: {TEMPLATES_DIR}")
        await init_db()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        logger.exception(e)
        raise

# Log de inicialização
logger.info("🚀 Aplicação iniciada")
logger.info(f"📁 Diretório de templates: {TEMPLATES_DIR}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
