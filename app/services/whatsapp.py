import logging
from decouple import config
import qrcode
import io
import base64
from sqlmodel import Session
from app.db.models import User, Account, Transaction, Bill, Goal, Category
import webbrowser
import pyautogui
from threading import Thread

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.phone_number = config('WHATSAPP_NUMBER', default=None)
        self.qr_code = None
        self.is_initialized = False
        
    def initialize(self):
        """Inicializa o serviço"""
        try:
            self.is_initialized = True
            logger.info("✅ WhatsApp service initialized")
            return self.get_qr_code()
        except Exception as e:
            logger.error(f"❌ Error initializing WhatsApp: {str(e)}")
            return None
            
    def get_qr_code(self):
        """Gera QR Code para conexão do WhatsApp"""
        try:
            # Remove formatação do número
            clean_number = self.phone_number.replace("+", "").replace("-", "").replace(" ", "")
            if not clean_number.startswith("55"):
                clean_number = "55" + clean_number
            
            # Cria URL do WhatsApp
            whatsapp_url = f"https://wa.me/{clean_number}?text=oi"
            logger.info(f"URL do WhatsApp: {whatsapp_url}")
            
            # Gera QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(whatsapp_url)
            qr.make(fit=True)
            
            # Converte para imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converte para base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            self.qr_code = f"data:image/png;base64,{img_str}"
            logger.info(f"✅ QR Code gerado para {clean_number}")
            return self.qr_code
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar QR code: {str(e)}")
            return None
            
    def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem via WhatsApp"""
        try:
            # Formata número
            if not to.startswith('whatsapp:'):
                to = f"whatsapp:+{to}"
                
            # Envia via Twilio
            self.client.messages.create(
                from_=f"whatsapp:{self.twilio_number}",
                body=message,
                to=to
            )
            
            logger.info(f"✅ Mensagem enviada para {to}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
            return False
            
    async def process_command(self, text: str, user: User, db: Session) -> str:
        """Processa comandos recebidos"""
        try:
            # Se não for um comando, verifica se é primeira mensagem
            if not text.startswith('/'):
                if "olá" in text.lower() or "oi" in text.lower() or "quero gerenciar" in text.lower():
                    return """
                    👋 Olá! Bem-vindo ao Pixzinho Bot!

                    Para começar a usar, você precisa:
                    1️⃣ Criar uma conta: /registrar seu@email.com senha123
                    2️⃣ Fazer login: /login seu@email.com senha123
                    3️⃣ Criar uma conta bancária: /conta "Nubank" 1000
                    
                    Depois é só usar os comandos:
                    📝 /ajuda - Ver todos os comandos
                    💰 /saldo - Ver seu saldo
                    📊 /extrato - Ver transações
                    
                    Precisa de ajuda? Digite /ajuda
                    """
                return "Use / para comandos. Digite /ajuda para ver a lista."
                
            cmd = text.lower().split()
            command = cmd[0]
            
            if command == '/ajuda':
                return """
                📋 Comandos disponíveis:

                🔐 Conta:
                /registrar [email] [senha] - Cria novo usuário
                /login [email] [senha] - Faz login
                
                💳 Contas bancárias:
                /conta [nome] [saldo] - Cria conta bancária
                /contas - Lista suas contas
                
                💰 Transações:
                /despesa [valor] [descrição] - Registra despesa
                /receita [valor] [descrição] - Registra receita
                /saldo - Mostra saldo atual
                /extrato - Últimas transações
                
                🎯 Metas:
                /meta [valor] [descrição] - Cria meta
                /metas - Lista metas
                """
                
            elif command == '/registrar':
                if len(cmd) < 3:
                    return "Formato: /registrar seu@email.com senha123"
                    
                email = cmd[1]
                password = cmd[2]
                
                # Cria usuário
                user = User(
                    email=email,
                    password=password,
                    whatsapp=config('WHATSAPP_NUMBER')  # Número do WhatsApp
                )
                db.add(user)
                db.commit()
                
                return """
                ✅ Conta criada com sucesso!
                
                Agora faça login com:
                /login seu@email.com senha123
                """
                
            elif command == '/login':
                if len(cmd) < 3:
                    return "Formato: /login seu@email.com senha123"
                    
                email = cmd[1]
                password = cmd[2]
                
                # Verifica login
                user = db.query(User).filter(
                    User.email == email,
                    User.password == password
                ).first()
                
                if not user:
                    return "❌ Email ou senha incorretos"
                    
                return """
                ✅ Login realizado com sucesso!
                
                Agora crie uma conta bancária:
                /conta "Nubank" 1000
                
                Ou veja seus comandos:
                /ajuda
                """
                
            elif command == '/conta':
                if not user:
                    return "❌ Faça login primeiro com /login"
                    
                if len(cmd) < 3:
                    return "Formato: /conta \"Nubank\" 1000"
                    
                nome = cmd[1].strip('"')
                saldo = float(cmd[2])
                
                # Cria conta
                account = Account(
                    name=nome,
                    balance=saldo,
                    owner_id=user.id
                )
                db.add(account)
                db.commit()
                
                return f"""
                ✅ Conta "{nome}" criada com saldo R$ {saldo:.2f}
                
                Agora você pode:
                • Ver saldo: /saldo
                • Registrar despesa: /despesa 50 Almoço
                • Registrar receita: /receita 1000 Salário
                """
                
            elif command == '/saldo':
                return await self.check_balance(text, user, db)
                
            elif command in ['/despesa', '/receita']:
                if len(cmd) < 3:
                    return "Formato: /despesa 50 Almoço"
                    
                valor = float(cmd[1])
                descricao = " ".join(cmd[2:])
                
                # Registra transação
                transaction = Transaction(
                    amount=valor,
                    type="expense" if command == '/despesa' else "income",
                    description=descricao,
                    user_id=user.id
                )
                db.add(transaction)
                db.commit()
                
                tipo = "Despesa" if command == '/despesa' else "Receita"
                return f"✅ {tipo} registrada:\nValor: R$ {valor:.2f}\nDescrição: {descricao}"
                
            else:
                return "Comando não reconhecido. Use /ajuda para ver a lista."
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar comando: {str(e)}")
            return "❌ Erro ao processar comando"

    async def check_balance(self, message: str, user: User, db: Session):
        """Retorna saldo total das contas"""
        accounts = db.query(Account).filter(Account.owner_id == user.id).all()
        
        if not accounts:
            return "❌ Você ainda não tem nenhuma conta cadastrada."
        
        total = sum(account.balance for account in accounts)
        
        response = "💰 Saldo das Contas:\n\n"
        for acc in accounts:
            icon = "🔴" if acc.balance < 0 else "🟢"
            response += f"{icon} {acc.name}: R$ {acc.balance:.2f}\n"
        
        response += f"\n📊 Total: R$ {total:.2f}"
        return response

# Instância global
whatsapp_service = WhatsAppService() 