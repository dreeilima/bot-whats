import logging
from app.config import config
import qrcode
import io
import base64
from sqlmodel import Session
from app.db.models import User, Account, Transaction, Bill, Goal, Category
import webbrowser
from datetime import datetime
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        # Carrega número do bot
        self.phone_number = config('WHATSAPP_NUMBER', default=None)
        if self.phone_number:
            # Garante formato correto
            self.phone_number = self.phone_number.replace("+", "").replace("-", "").replace(" ", "")
            if not self.phone_number.startswith("55"):
                self.phone_number = "55" + self.phone_number
        
        self.qr_code = None
        self.is_initialized = False
        logger.info(f"Iniciando WhatsApp com número: {self.phone_number}")
        
    def get_qr_code(self):
        """Gera QR Code para conexão do WhatsApp"""
        try:
            # Força o número do bot
            bot_number = config('WHATSAPP_NUMBER', default=None)
            
            if not bot_number:
                logger.error("WHATSAPP_NUMBER não configurado no .env")
                return None
            
            # Remove formatação e adiciona 55 se necessário
            bot_number = bot_number.replace("+", "").replace("-", "").replace(" ", "")
            if not bot_number.startswith("55"):
                bot_number = "55" + bot_number
            
            logger.info(f"Gerando QR para número: {bot_number}")
            
            # Cria URL do WhatsApp
            whatsapp_url = f"https://wa.me/{bot_number}?text=oi"
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
            return self.qr_code
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar QR code: {str(e)}")
            logger.exception(e)  # Mostra o stack trace completo
            return None
            
    def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem via WhatsApp"""
        try:
            # Remove formatação do número
            clean_number = to.replace("+", "").replace("-", "").replace(" ", "")
            if not clean_number.startswith("55"):
                clean_number = "55" + clean_number
            
            # Codifica a mensagem para URL (preservando emojis)
            encoded_message = quote(message)
            
            # Cria URL do WhatsApp
            whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_number}&text={encoded_message}"
            
            logger.info(f"URL para envio: {whatsapp_url}")
            
            # Abre URL no navegador padrão
            webbrowser.open(whatsapp_url)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
            return False
            
    def process_message(self, text: str, user: User, db: Session) -> str:
        """Processa mensagens recebidas"""
        try:
            text = text.lower().strip()
            logger.info(f"Processando mensagem: '{text}' do usuário {user.whatsapp}")
            
            # Comandos básicos
            if text in ["oi", "olá", "ola"]:
                logger.info("Comando: boas vindas")
                return (
                    "👋 Olá! Eu sou o FinBot!\n\n"
                    "Para começar, envie:\n"
                    "📝 /ajuda - Ver todos os comandos"
                )
            
            # Comando de ajuda
            if text == "/ajuda":
                logger.info("Comando: ajuda")
                return self.get_help_message()

            # Comando de saldo
            if text == "/saldo":
                logger.info("Comando: saldo")
                return self.check_balance(user, db)

            # Comando de despesa
            if text.startswith("/despesa"):
                logger.info("Comando: despesa")
                return self.register_transaction(text, user, db, "expense")

            # Comando de receita
            if text.startswith("/receita"):
                logger.info("Comando: receita")
                return self.register_transaction(text, user, db, "income")
            
            # Comando de extrato
            if text == "/extrato":
                logger.info("Comando: extrato")
                return self.get_statement(user, db)
            
            # Comando de categorias
            if text == "/categorias":
                logger.info("Comando: categorias")
                return self.get_category_summary(user, db)
            
            # Comando de resumo (alias para categorias)
            if text == "/resumo":
                logger.info("Comando: resumo (alias para categorias)")
                return self.get_category_summary(user, db)
            
            # Comando não reconhecido
            logger.warning(f"Comando não reconhecido: {text}")
            return "❓ Comando não reconhecido. Digite /ajuda para ver os comandos disponíveis."
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            logger.exception(e)  # Isso mostra o stack trace completo
            return "❌ Desculpe, ocorreu um erro ao processar sua mensagem."

    def register_transaction(self, text: str, user: User, db: Session, type_: str) -> str:
        """Registra uma transação (despesa ou receita)"""
        try:
            # Formato: /tipo valor descrição #categoria
            parts = text.split(" ", 2)
            if len(parts) < 3:
                return f"❌ Formato inválido. Use: {parts[0]} valor descrição #categoria"
            
            valor = float(parts[1].replace(",", "."))
            descricao_full = parts[2]
            
            logger.info(f"Processando transação: {descricao_full}")
            
            # Extrai categoria se existir
            if "#" in descricao_full:
                descricao, categoria_nome = descricao_full.split("#")
                descricao = descricao.strip()
                categoria_nome = categoria_nome.strip().lower()  # Normaliza categoria
                
                logger.info(f"Categoria encontrada: {categoria_nome}")
                
                # Busca ou cria categoria
                categoria = db.query(Category).filter(
                    Category.name == categoria_nome,
                    Category.type == type_
                ).first()
                
                if not categoria:
                    logger.info(f"Criando nova categoria: {categoria_nome}")
                    categoria = Category(
                        name=categoria_nome,
                        type=type_,
                        icon="💰" if type_ == "income" else "💸"
                    )
                    db.add(categoria)
                    db.commit()
                    db.refresh(categoria)
            else:
                descricao = descricao_full
                categoria = None
                logger.info("Sem categoria")
            
            logger.info(f"Registrando {type_}: R$ {valor} - {descricao}")
            
            # Busca/cria conta padrão
            account = db.query(Account).filter(
                Account.owner_id == user.id,
                Account.type == "checking"
            ).first()
            
            logger.info(f"Conta encontrada: {account is not None}")
            
            if not account:
                # Cria conta padrão
                logger.info("Criando conta padrão...")
                account = Account(
                    owner_id=user.id,
                    name="Conta Principal",
                    type="checking",
                    balance=0
                )
                db.add(account)
                db.commit()
                db.refresh(account)
                logger.info(f"Conta criada: {account.id}")
            
            # Ajusta valor para despesa
            amount = valor if type_ == "income" else -valor
            
            # Cria transação
            transaction = Transaction(
                owner_id=user.id,
                account_id=account.id,
                amount=amount,
                type=type_,
                description=descricao,
                category_id=categoria.id if categoria else None,
                date=datetime.now()
            )
            
            # Atualiza saldo
            account.balance += amount
            
            db.add(transaction)
            db.commit()
            
            icon = "💰" if type_ == "income" else "💸"
            tipo = "Receita" if type_ == "income" else "Despesa"
            
            return (
                f"{icon} {tipo} registrada!\n\n"
                f"Valor: R$ {valor:.2f}\n"
                f"Descrição: {descricao}\n"
                f"Categoria: {categoria.name if categoria else 'Sem categoria'}\n"
                f"💳 Saldo atual: R$ {account.balance:.2f}"
            )
            
        except ValueError:
            return "❌ Valor inválido. Use números (ex: 50.90)"
        except Exception as e:
            logger.error(f"Erro ao registrar transação: {str(e)}")
            return f"❌ Erro ao registrar {type_}."

    def get_welcome_message(self) -> str:
        """Retorna mensagem de boas vindas"""
        return """
👋 Olá! Eu sou o FinBot, seu assistente financeiro!

💰 Posso te ajudar a:
- Registrar despesas e receitas
- Consultar seu saldo
- Ver extrato
- E muito mais!

📝 Digite /ajuda para ver todos os comandos disponíveis.
        """

    def get_help_message(self) -> str:
        """Retorna lista de comandos disponíveis"""
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

    def check_balance(self, user: User, db: Session) -> str:
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

    def get_statement(self, user: User, db: Session) -> str:
        """Retorna extrato das transações"""
        transactions = db.query(Transaction).filter(
            Transaction.owner_id == user.id
        ).order_by(Transaction.date.desc()).limit(10).all()
        
        if not transactions:
            return "❌ Não há transações registradas."
        
        statement = "📊 Últimas Transações:\n\n"
        for t in transactions:
            icon = "💰" if t.type == "income" else "💸"
            valor = abs(t.amount)
            data = t.date.strftime("%d/%m/%Y %H:%M")
            statement += f"{icon} {t.description}: R$ {valor:.2f} ({data})\n"
        
        return statement

    def get_category_summary(self, user: User, db: Session) -> str:
        """Retorna resumo de gastos por categoria"""
        try:
            logger.info("Iniciando get_category_summary")
            
            # Busca transações do mês atual
            start_date = datetime.now().replace(day=1, hour=0, minute=0)
            logger.info(f"Buscando transações desde: {start_date}")
            
            transactions = db.query(Transaction).filter(
                Transaction.owner_id == user.id,
                Transaction.date >= start_date
            ).all()
            
            logger.info(f"Transações encontradas: {len(transactions)}")
            
            if not transactions:
                return "❌ Não há transações este mês."
            
            # Agrupa por categoria
            categories = {"receitas": {}, "despesas": {}}
            total_receitas = 0
            total_despesas = 0
            
            for t in transactions:
                try:
                    categoria = t.category.name if t.category else "Sem categoria"
                    if t.type == "income":
                        total_receitas += t.amount
                        categories["receitas"].setdefault(categoria, 0)
                        categories["receitas"][categoria] += t.amount
                    else:
                        total_despesas += abs(t.amount)
                        categories["despesas"].setdefault(categoria, 0)
                        categories["despesas"][categoria] += abs(t.amount)
                except Exception as e:
                    logger.error(f"Erro ao processar transação {t.id}: {str(e)}")
            
            # Monta resposta
            response = "📊 Resumo do Mês:\n\n"
            
            # Receitas
            if categories["receitas"]:
                response += "💰 Receitas:\n"
                for cat, valor in categories["receitas"].items():
                    porcentagem = (valor / total_receitas * 100) if total_receitas > 0 else 0
                    response += f"{cat}: R$ {valor:.2f} ({porcentagem:.1f}%)\n"
                response += f"Total: R$ {total_receitas:.2f}\n\n"
            
            # Despesas
            if categories["despesas"]:
                response += "💸 Despesas:\n"
                for cat, valor in categories["despesas"].items():
                    porcentagem = (valor / total_despesas * 100) if total_despesas > 0 else 0
                    response += f"{cat}: R$ {valor:.2f} ({porcentagem:.1f}%)\n"
                response += f"Total: R$ {total_despesas:.2f}\n\n"
            
            # Saldo
            saldo = total_receitas - total_despesas
            economia = (saldo / total_receitas * 100) if total_receitas > 0 else 0
            response += f"💳 Saldo: R$ {saldo:.2f}\n"
            response += f"💹 Economia: {economia:.1f}%"
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}")
            return "❌ Erro ao gerar resumo por categorias."

# Instância global
whatsapp_service = WhatsAppService() 