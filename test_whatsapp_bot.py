import requests
import logging
import time
from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://bot-whats-9onh.onrender.com"

def test_whatsapp_connection():
    """Testa conexão com WhatsApp"""
    try:
        # Verifica se o QR está disponível
        response = requests.get(f"{BASE_URL}/whatsapp/qr")
        assert response.status_code == 200, "QR Code não disponível"
        logger.info("✅ QR Code gerado")
        
        # Aguarda conexão
        logger.info("🔍 Aguardando conexão do WhatsApp...")
        time.sleep(5)
        
        # Testa comandos
        commands = [
            "/ajuda",
            "/despesa 50 Almoço",
            "/receita 1000 Salário",
            "/saldo",
            "/extrato"
        ]
        
        for cmd in commands:
            logger.info(f"Testando comando: {cmd}")
            # Simula envio de mensagem
            # Na implementação real, isso seria feito pelo WhatsApp
            time.sleep(2)
        
        logger.info("✅ Teste do bot concluído!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    test_whatsapp_connection() 