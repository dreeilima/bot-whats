"""Serviços compartilhados entre módulos"""
from app.services.transactions import get_balance, add_transaction, get_transactions
from app.services.whatsapp import WhatsAppService

# Serviços globais
whatsapp_service = None

def get_whatsapp_service():
    """Retorna o serviço WhatsApp inicializado"""
    global whatsapp_service
    if whatsapp_service is None:
        whatsapp_service = WhatsAppService()
    return whatsapp_service

def init_services():
    """Inicializa serviços compartilhados"""
    return {
        "whatsapp": WhatsAppService()
    } 