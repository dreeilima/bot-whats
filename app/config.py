from decouple import config as decouple_config
import logging

def config(key: str, default=None, cast=None):
    """Wrapper para decouple.config com logging"""
    try:
        value = decouple_config(key, default=default, cast=cast)
        logging.debug(f"Config loaded: {key}={value}")
        return value
    except Exception as e:
        logging.error(f"Error loading config {key}: {str(e)}")
        return default

# Carrega configurações principais
ENVIRONMENT = config("ENVIRONMENT", default="development")
DATABASE_URL = config("DATABASE_URL")
WHATSAPP_NUMBER = config("WHATSAPP_NUMBER")
WHATSAPP_WEBHOOK_SECRET = config("WHATSAPP_WEBHOOK_SECRET")

# URLs dos webhooks
WEBHOOK_URL_DEV = config("WEBHOOK_URL_DEV")
WEBHOOK_URL_PROD = config("WEBHOOK_URL_PROD")

# Define URL do webhook baseado no ambiente
WEBHOOK_URL = WEBHOOK_URL_PROD if ENVIRONMENT == "production" else WEBHOOK_URL_DEV 