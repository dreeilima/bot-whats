from decouple import config as _config
import logging

def get_config(key: str, default=None):
    """Wrapper para carregar configurações com log de erros"""
    try:
        return _config(key, default=default)
    except Exception as e:
        logging.error(f"Error loading config {key}: {str(e)}")
        return default

# Exporta como 'config' para manter compatibilidade
config = get_config

# Carrega configurações principais
ENVIRONMENT = config("ENVIRONMENT", default="development")
DATABASE_URL = config("DATABASE_URL", default="sqlite:///./test.db")

# Adiciona parâmetros SSL para o PostgreSQL
if "postgresql" in DATABASE_URL:
    DATABASE_URL = f"{DATABASE_URL}?sslmode=require"

WHATSAPP_NUMBER = config("WHATSAPP_NUMBER")
WHATSAPP_WEBHOOK_SECRET = config("WHATSAPP_WEBHOOK_SECRET")

# URLs dos webhooks
WEBHOOK_URL_DEV = config("WEBHOOK_URL_DEV")
WEBHOOK_URL_PROD = config("WEBHOOK_URL_PROD")

# Define URL do webhook baseado no ambiente
WEBHOOK_URL = WEBHOOK_URL_PROD if ENVIRONMENT == "production" else WEBHOOK_URL_DEV 