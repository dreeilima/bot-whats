"""
    Esse código é o módulo principal do projeto, responsável por iniciar
todas funcionalidades do sistema.

author: github.com/gustavosett
"""
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import session
from .routes import routers  # Importa a lista de routers
from app.routes import whatsapp
from app.db.session import initialize_db
import logging
from fastapi.responses import RedirectResponse, HTMLResponse
from app.services.whatsapp import WhatsAppService

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinBot",
    description="Inteligência financeira ao seu alcance"
)
# Atualiza/cria os modelos sqlalchemy
session.initialize_db()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routers sem prefix
for router in routers:
    app.include_router(router)

# Adiciona rotas
app.include_router(whatsapp.router)

@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse("/docs#")

# Essa função salva a documentação OpenAPI dos dados do FastApi em um JSON
@app.on_event("startup")
def save_openapi_json():
    openapi_data = app.openapi()
    # salva arquivo
    with open("openapi.json", "w") as file:
        json.dump(openapi_data, file)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "FinBot API"}

# Rota para página inicial com QR code
@app.get("/", response_class=HTMLResponse)
async def home():
    whatsapp_service = WhatsAppService()
    return f"""
    <html>
        <head>
            <title>FinBot - Seu Assistente Financeiro</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }}
                .container {{
                    margin-top: 50px;
                }}
                .steps {{
                    text-align: left;
                    max-width: 500px;
                    margin: 30px auto;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 FinBot - Seu Assistente Financeiro</h1>
                <p>Para começar a usar o FinBot, siga os passos:</p>
                
                <div class="steps">
                    <h3>1. Escaneie o QR Code abaixo:</h3>
                    <img src="{whatsapp_service.get_qr_code()}" alt="WhatsApp QR Code"/>
                    
                    <h3>2. Envie uma mensagem:</h3>
                    <p>Depois de escanear, envie <strong>/ajuda</strong> para ver todos os comandos disponíveis.</p>
                    
                    <h3>Comandos principais:</h3>
                    <ul>
                        <li>/saldo - Ver saldo atual</li>
                        <li>/receita valor descrição #categoria</li>
                        <li>/despesa valor descrição #categoria</li>
                        <li>/extrato - Ver últimas transações</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """
