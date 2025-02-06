from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from typing import Dict
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import logging

from app.db.session import get_db
from app.services.security import get_current_user
from app.db.models import User
from app.services.whatsapp import whatsapp_service

router = APIRouter(tags=["whatsapp"])

logger = logging.getLogger(__name__)

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
    request: Request,
    db: Session = Depends(get_db)
):
    """Webhook para receber mensagens do WhatsApp via Twilio"""
    try:
        # Valida assinatura do Twilio
        form = await request.form()
        
        # Extrai dados
        sender = form.get("From", "").replace("whatsapp:", "")
        message = form.get("Body", "")
        
        # Busca usuário
        user = db.query(User).filter(User.whatsapp == sender).first()
        
        # Processa comando
        response = await whatsapp_service.process_command(message, user, db)
        
        # Envia resposta
        whatsapp_service.send_message(sender, response)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/qr", response_class=HTMLResponse)
async def get_qr_code():
    """Gera e retorna o QR Code para conexão do WhatsApp"""
    try:
        logger.info("Gerando QR Code...")
        qr = whatsapp_service.get_qr_code()
        logger.info(f"QR Code gerado: {bool(qr)}")
        
        if qr:
            # Cria link direto
            clean_number = whatsapp_service.phone_number.replace("+", "").replace("-", "").replace(" ", "")
            if not clean_number.startswith("55"):
                clean_number = "55" + clean_number
                
            direct_link = f"https://wa.me/{clean_number}?text=oi"
            
            return HTMLResponse(f"""
                <html>
                    <head>
                        <title>FinBot - WhatsApp</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {{
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                max-width: 800px;
                                margin: 0 auto;
                                padding: 20px;
                                text-align: center;
                                background: #f0f2f5;
                            }}
                            .container {{
                                background: white;
                                padding: 30px;
                                border-radius: 12px;
                                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                                margin: 20px 0;
                            }}
                            h1 {{
                                color: #128C7E;
                                margin-bottom: 10px;
                            }}
                            .subtitle {{
                                color: #666;
                                margin-bottom: 30px;
                            }}
                            img {{
                                max-width: 300px;
                                margin: 20px 0;
                                border-radius: 8px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            }}
                            .scan-button {{
                                display: inline-block;
                                background: #128C7E;
                                color: white;
                                padding: 12px 25px;
                                border-radius: 25px;
                                text-decoration: none;
                                margin: 20px 0;
                                font-weight: bold;
                                transition: all 0.3s ease;
                            }}
                            .scan-button:hover {{
                                background: #075E54;
                                transform: translateY(-2px);
                            }}
                            .commands {{
                                text-align: left;
                                background: #f8f9fa;
                                padding: 25px;
                                border-radius: 12px;
                                border: 1px solid #e9ecef;
                            }}
                            .commands h2 {{
                                color: #128C7E;
                                margin-top: 0;
                            }}
                            .commands ul {{
                                list-style: none;
                                padding: 0;
                            }}
                            .commands li {{
                                margin: 10px 0;
                                padding: 8px 0;
                                border-bottom: 1px solid #e9ecef;
                            }}
                            code {{
                                background: #e9ecef;
                                padding: 3px 6px;
                                border-radius: 4px;
                                color: #128C7E;
                            }}
                            .footer {{
                                margin-top: 30px;
                                color: #666;
                                font-size: 0.9em;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>📱 FinBot</h1>
                            <p class="subtitle">Inteligência financeira ao seu alcance</p>
                            
                            <img src="{qr}" alt="WhatsApp QR Code"/>
                            
                            <div>
                                <a href="{direct_link}" target="_blank" class="scan-button">
                                    Abrir WhatsApp ↗
                                </a>
                            </div>
                            
                            <div class="commands">
                                <h2>🤖 Comandos Disponíveis</h2>
                                <ul>
                                    <li>📝 <code>/ajuda</code> - Lista todos os comandos</li>
                                    <li>💸 <code>/despesa 50 Almoço</code> - Registra uma despesa</li>
                                    <li>💰 <code>/receita 1000 Salário</code> - Registra uma receita</li>
                                    <li>💳 <code>/saldo</code> - Mostra o saldo atual</li>
                                    <li>📊 <code>/extrato</code> - Mostra as últimas transações</li>
                                </ul>
                            </div>
                            
                            <p class="footer">
                                Escaneie o QR Code com seu WhatsApp ou clique no botão acima para começar
                            </p>
                        </div>
                    </body>
                </html>
            """)
        return HTMLResponse("QR Code não disponível. Tente novamente em alguns segundos.")
    except Exception as e:
        logger.error(f"Erro ao gerar QR Code: {str(e)}")
        return HTMLResponse(f"Erro ao gerar QR Code: {str(e)}") 