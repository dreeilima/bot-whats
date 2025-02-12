from fastapi import FastAPI, Request
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Webhook recebido: {data}")
        return {"message": "Mensagem recebida", "data": data}
    except Exception as e:
        logger.error(f"Erro: {e}")
        return {"error": str(e)}

@app.get("/test")
def test():
    return {"message": "test ok"} 