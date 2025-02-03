from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Dict
from pydantic import BaseModel

from app.db.session import get_db
from app.services.security import get_current_user
from app.db.models import User
from app.services.whatsapp import whatsapp_service

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

class MessageRequest(BaseModel):
    phone: str
    message: str

@router.post("/send-message")
async def send_whatsapp_message(
    message_data: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
                "message": f"Mensagem enviada para {message_data.phone}",
                "sender": current_user.email
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

@router.post("/webhook")
async def whatsapp_webhook(
    data: Dict,
    db: Session = Depends(get_db)
):
    """
    Webhook para receber mensagens do WhatsApp
    """
    try:
        # Extrai informações da mensagem
        message = data.get("message", {})
        sender = message.get("from")
        text = message.get("text", "")

        # Busca usuário pelo número do WhatsApp
        user = db.query(User).filter(User.whatsapp == sender).first()
        if not user:
            return {"status": "error", "message": "Usuário não encontrado"}

        # Processa o comando
        response = await whatsapp_service.process_command(text, user, db)
        
        # Envia resposta
        whatsapp_service.send_message(sender, response)

        return {"status": "success", "message": "Mensagem processada"}
    except Exception as e:
        return {"status": "error", "message": str(e)} 