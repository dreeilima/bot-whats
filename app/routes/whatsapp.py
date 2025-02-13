from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from typing import Dict, Optional
from pydantic import BaseModel
import logging
import os

from app.db.session import get_db
from app.services.whatsapp import whatsapp_service, WhatsAppService
from app.config import WHATSAPP_NUMBER

router = APIRouter(tags=["whatsapp"])
logger = logging.getLogger(__name__)
whatsapp_service = WhatsAppService()

# Configura templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"))

class MessageRequest(BaseModel):
    phone: str
    message: str

class WebhookRequest(BaseModel):
    message: Dict

@router.post("/webhook")  # Rota para receber mensagens do WhatsApp
async def webhook(request: WebhookRequest):
    try:
        logger.info("\n📨 Webhook recebido:")
        logger.info(f"Mensagem: {request.message}")
        
        # Extrai dados
        text = request.message.get("text", "")
        from_number = request.message.get("from", "")
        
        logger.info(f"De: {from_number}")
        logger.info(f"Texto: {text}")
        
        if not text or not from_number:
            logger.error("❌ Mensagem inválida - campos faltando")
            raise HTTPException(status_code=400, detail="Mensagem inválida")
            
        # Processa a mensagem
        response = whatsapp_service.process_message(text)
        
        logger.info("\n✅ Mensagem processada:")
        logger.info(f"Resposta: {response}")
        
        # Retorna resposta
        return {"message": response} if response else {"status": "success"}
        
    except Exception as e:
        logger.error("\n❌ Erro no webhook:")
        logger.error(f"Erro: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr")
async def get_qr():
    """Obter QR code para conexão do WhatsApp"""
    try:
        qr = whatsapp_service.get_qr_code()
        if qr:
            return {
                "status": "success",
                "qr": qr
            }
        return {
            "status": "error",
            "message": "QR Code não disponível"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/send-message")
async def send_message(message: MessageRequest):
    """Enviar mensagem via WhatsApp"""
    try:
        success = await whatsapp_service.send_message(
            message.phone,
            message.message
        )
        if success:
            return {
                "status": "success",
                "message": f"Mensagem enviada para {message.phone}"
            }
        raise HTTPException(
            status_code=500,
            detail="Erro ao enviar mensagem"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/admin/connect", response_class=HTMLResponse)
async def admin_connect(request: Request):
    logger.info("🔐 Acesso à página admin")
    try:
        return templates.TemplateResponse(
            "admin_connect.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"❌ Erro na página admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connect", response_class=HTMLResponse)
async def user_connect(request: Request):
    logger.info("👤 Acesso à página usuário")
    try:
        return templates.TemplateResponse(
            "connect.html",
            {
                "request": request,
                "whatsapp_number": os.getenv("WHATSAPP_NUMBER")
            }
        )
    except Exception as e:
        logger.error(f"❌ Erro na página usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test():
    logger.info("🧪 Teste de rota")
    return {"status": "ok", "message": "Rota de teste funcionando"} 