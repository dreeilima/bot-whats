from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FinBot API")

class Message(BaseModel):
    from_: str
    text: str

class WebhookRequest(BaseModel):
    message: Message

class WebhookResponse(BaseModel):
    message: str = "success"
    response: str

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: WebhookRequest):
    try:
        logger.info(f"Mensagem recebida: {request.message.text}")
        
        # Lógica simples de resposta
        if request.message.text.lower() == "oi":
            response = "Olá! Como posso ajudar?"
        else:
            response = "Desculpe, ainda não sei processar este comando."
            
        return WebhookResponse(response=response)
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 