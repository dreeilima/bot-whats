from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import qrcode
import json
import base64
from io import BytesIO

class PixPayload(BaseModel):
    merchant_name: str
    merchant_city: str
    postal_code: str
    amount: float
    transaction_id: str
    description: str

class PixService:
    @staticmethod
    def create_payload(data: PixPayload) -> str:
        """Cria o payload do PIX seguindo o padrão do Banco Central"""
        payload = f"""00020126580014br.gov.bcb.pix0136{data.transaction_id}5204000053039865802BR5913{data.merchant_name}6008{data.merchant_city}62200516{data.postal_code}6304"""
        
        # Adiciona o valor se existir
        if data.amount:
            payload = payload.replace("5204000053039865", f"520400005303986540{data.amount:.2f}")
        
        return payload

    @staticmethod
    async def generate_qr_code(
        amount: float,
        description: str,
        merchant_name: str = "PixzinhoBot",
        merchant_city: str = "SAO PAULO",
        postal_code: str = "01000000"
    ) -> dict:
        """Gera QR Code do PIX"""
        try:
            # Cria ID único para a transação
            transaction_id = f"PIX{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Cria payload
            payload = PixPayload(
                merchant_name=merchant_name,
                merchant_city=merchant_city,
                postal_code=postal_code,
                amount=amount,
                transaction_id=transaction_id,
                description=description
            )
            
            # Gera o QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(PixService.create_payload(payload))
            qr.make(fit=True)
            
            # Converte para imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converte para base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "transaction_id": transaction_id,
                "amount": amount,
                "description": description,
                "qr_code": qr_code_base64,
                "payload": PixService.create_payload(payload)
            }
        except Exception as e:
            raise Exception(f"Erro ao gerar QR Code: {str(e)}")

    @staticmethod
    async def process_payment(payment_data: dict) -> dict:
        """Processa pagamento PIX recebido"""
        try:
            # Validar dados recebidos
            required_fields = ["transaction_id", "amount", "payer_name", "payer_document"]
            for field in required_fields:
                if field not in payment_data:
                    raise ValueError(f"Campo obrigatório ausente: {field}")
            
            # Aqui você implementaria a integração com seu banco
            # Por enquanto, simulamos o processamento
            success = True
            
            if success:
                return {
                    "status": "success",
                    "message": "Pagamento processado com sucesso",
                    "transaction_id": payment_data["transaction_id"],
                    "amount": payment_data["amount"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception("Falha no processamento do pagamento")
                
        except Exception as e:
            raise Exception(f"Erro ao processar pagamento: {str(e)}") 