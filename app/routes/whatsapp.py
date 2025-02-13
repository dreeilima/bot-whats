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
templates = Jinja2Templates(directory="app/templates")

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
async def admin_connect_page(request: Request):
    """Página administrativa para conectar o BOT ao WhatsApp"""
    return templates.TemplateResponse(
        "admin_connect.html",
        {"request": request}
    )

@router.get("/connect", response_class=HTMLResponse)
async def user_connect_page(request: Request):
    """Página para usuários se conectarem ao BOT"""
    return templates.TemplateResponse(
        "connect.html",
        {
            "request": request,
            "whatsapp_number": WHATSAPP_NUMBER
        }
    ) 