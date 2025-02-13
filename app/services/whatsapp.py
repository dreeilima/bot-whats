import logging
import requests
from app.config import config
import os
import httpx

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.phone_number = config("WHATSAPP_NUMBER")
        self.api_url = "http://localhost:3001"  # URL do servidor Node.js
        if os.getenv("NODE_ENV") == "production":
            self.api_url = "https://bot-whats-9onh.onrender.com"
        self.qr_code = None
        logger.info(f"Iniciando WhatsApp com número: {self.phone_number}")
        
    async def get_qr_code(self):
        """Obtém QR code do servidor Node.js"""
        try:
            logger.info(f"🔍 Tentando obter QR code de {self.api_url}/whatsapp/qr")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/whatsapp/qr")
                logger.info(f"✅ Resposta recebida: {response.status_code}")
                data = response.json()
                logger.info(f"📱 QR Code presente: {bool(data.get('qr'))}")
                return data.get("qr")
        except Exception as e:
            logger.error(f"❌ Erro ao obter QR code: {str(e)}")
            logger.exception(e)
            return None
            
    async def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem via servidor Node.js"""
        try:
            logger.info(f"\n📤 Tentando enviar mensagem:")
            logger.info(f"Para: {to}")
            logger.info(f"Mensagem: {message}")

            # Remove formatação do número
            clean_number = to.replace("+", "").replace("-", "").replace(" ", "")
            if not clean_number.startswith("55"):
                clean_number = "55" + clean_number
            
            logger.info(f"Número formatado: {clean_number}")

            # Envia para o servidor Node.js
            response = requests.post(
                f"{self.api_url}/send-message",
                json={
                    "to": clean_number,
                    "message": message
                }
            )
            
            if response.status_code == 200:
                logger.info(f"\n✅ Mensagem enviada com sucesso:")
                logger.info(f"Para: {clean_number}")
                logger.info(f"Status: {response.status_code}")
                return True
            else:
                logger.error(f"\n❌ Erro ao enviar mensagem:")
                logger.error(f"Para: {clean_number}")
                logger.error(f"Status: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"\n❌ Erro ao enviar mensagem:")
            logger.error(f"Para: {to}")
            logger.error(f"Erro: {str(e)}")
            logger.exception(e)
            return False
            
    def process_message(self, text: str) -> str:
        """Processa mensagens recebidas"""
        try:
            text = text.lower().strip()
            logger.info(f"\n📨 Processando mensagem:")
            logger.info(f"Texto original: {text}")
            logger.info(f"Texto processado: {text.lower().strip()}")
            
            # Comandos básicos
            if text in ["oi", "olá", "ola"]:
                logger.info("✅ Comando identificado: Saudação")
                return (
                    "👋 Olá! Eu sou o FinBot!\n\n"
                    "Para começar, envie:\n"
                    "📝 /ajuda - Ver todos os comandos"
                )
            
            # Comando de ajuda
            if text == "/ajuda":
                return (
                    "🤖 Comandos disponíveis:\n\n"
                    "💰 Finanças:\n"
                    "/saldo - Ver saldo atual\n"
                    "/extrato - Ver últimas transações\n"
                    "/categorias - Resumo por categoria\n\n"
                    "💸 Registros:\n"
                    "/despesa valor descrição #categoria\n"
                    "Exemplo: /despesa 50 Almoço #alimentação\n\n"
                    "/receita valor descrição #categoria\n"
                    "Exemplo: /receita 1000 Salário #salário\n\n"
                    "💡 A categoria é opcional"
                )
            
            # Comando não reconhecido
            return "❓ Comando não reconhecido. Digite /ajuda para ver os comandos disponíveis."
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            logger.exception(e)
            return "❌ Desculpe, ocorreu um erro ao processar sua mensagem."

# Instância global
whatsapp_service = WhatsAppService() 