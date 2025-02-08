from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from typing import Dict
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.services.whatsapp import whatsapp_service

router = APIRouter(tags=["whatsapp"])
logger = logging.getLogger(__name__)

class MessageRequest(BaseModel):
    phone: str
    message: str

class WebhookRequest(BaseModel):
    message: Dict

@router.post("/webhook")  # Rota para receber mensagens do WhatsApp
async def webhook(request: WebhookRequest):
    try:
        logger.info(f"Mensagem recebida: {request.message}")
        
        # Extrai dados
        text = request.message.get("text", "")
        from_number = request.message.get("from", "")
        
        if not text or not from_number:
            raise HTTPException(status_code=400, detail="Mensagem inválida")
            
        logger.info(f"Processando mensagem de {from_number}: {text}")
        
        # Processa a mensagem
        response = whatsapp_service.process_message(text)
        
        # Retorna resposta
        return {"message": response} if response else {"status": "success"}
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-message")  # Rota para enviar mensagens
async def send_whatsapp_message(message_data: MessageRequest):
    """
    Enviar mensagem via WhatsApp
    
    O número deve estar no formato: 11999999999 (DDD + número)
    A mensagem pode conter texto livre
    """
    try:
        success = whatsapp_service.send_message(
            message_data.phone,
            message_data.message
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Mensagem enviada para {message_data.phone}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Erro ao enviar mensagem"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 