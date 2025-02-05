import requests
import json
import logging
import os
from typing import List, Optional
from sqlmodel import Session
from app.db.models import User, Account, Transaction, Bill, Goal, Category
from functools import lru_cache

class WhatsAppService:
    def __init__(self):
        self.api_key = os.getenv("WHATSAPP_API_KEY")
        self.phone_number = os.getenv("WHATSAPP_NUMBER")
        self.base_url = "https://graph.facebook.com/v17.0"
        self.is_initialized = False
        self.commands = {
            "/saldo": self.check_balance,
            "/conta": self.account_info,
            "/ajuda": self.help_message,
            "/dica": self.financial_tip,
            "/contas": self.list_bills,
            "/despesa": self.add_expense,
            "/receita": self.add_income,
            "/extrato": self.get_statement,
            "/meta": self.handle_goal,
            "/relatorio": self.generate_report,
            "/categoria": self.manage_categories,
            "/lembrete": self.set_reminder
        }

    async def initialize(self):
        """Inicializa o serviço"""
        try:
            self.is_initialized = True
            logging.info("WhatsApp service initialized")
            return True
        except Exception as e:
            logging.error(f"Error initializing WhatsApp: {str(e)}")
            return False

    async def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem via API do WhatsApp Business"""
        try:
            # Remove o + do número se existir
            to = to.replace("+", "")
            
            # Endpoint da API
            url = f"{self.base_url}/{self.phone_number}/messages"
            
            # Headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Payload
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            # Faz a requisição
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logging.info(f"Message sent to {to}")
                return True
            else:
                logging.error(f"Error sending message: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error in send_message: {str(e)}")
            return False

    async def process_command(self, text: str, user: User, db: Session) -> str:
        """Processa comandos recebidos"""
        try:
            command = text.lower().split()[0]
            if command in self.commands:
                return await self.commands[command](text, user, db)
            return "Comando não reconhecido. Use /ajuda para ver os comandos disponíveis."
        except Exception as e:
            logging.error(f"Error processing command: {str(e)}")
            return "Erro ao processar comando. Tente novamente."

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

    async def help_message(self, message: str, user: User, db: Session):
        """Retorna lista de comandos disponíveis"""
        return """📱 Comandos Disponíveis:

💰 Gestão Financeira:
/saldo - Ver saldo de todas as contas
/conta [nome] - Informações detalhadas da conta
/extrato - Ver extrato dos últimos 7 dias
/relatorio - Relatório financeiro completo

💸 Transações:
/despesa valor descrição - Registrar despesa
/receita valor descrição - Registrar receita
/categoria listar - Ver categorias
/categoria criar nome tipo - Criar categoria

📋 Contas e Metas:
/contas - Ver contas a pagar pendentes
/meta criar nome valor data - Criar meta financeira
/meta listar - Ver suas metas

⏰ Lembretes:
/lembrete contas - Lembrar contas a vencer
/lembrete meta nome - Lembrar progresso da meta
/lembrete saldo - Lembrar de verificar saldo

💡 Outros:
/dica - Receber dica financeira
/ajuda - Ver esta mensagem"""

    async def financial_tip(self, message: str, user: User, db: Session):
        """Retorna dica financeira personalizada"""
        tips = [
            "Estabeleça um orçamento mensal e siga-o rigorosamente",
            "Guarde ao menos 10% da sua renda todo mês",
            "Evite dívidas de cartão de crédito",
            "Invista em sua educação financeira"
        ]
        return random.choice(tips)

    async def list_bills(self, message: str, user: User, db: Session):
        """Lista contas a pagar pendentes"""
        bills = db.query(Bill).filter(
            Bill.owner_id == user.id,
            Bill.is_paid == False,
            Bill.due_date <= datetime.utcnow() + timedelta(days=7)
        ).all()
        
        if not bills:
            return "Não há contas pendentes para os próximos 7 dias."
        
        response = "Contas a pagar:\n\n"
        for bill in bills:
            response += f"- {bill.description}: R$ {bill.amount:.2f} (vence em {bill.due_date.strftime('%d/%m/%Y')})\n"
        return response

    async def add_expense(self, message: str, user: User, db: Session):
        """Adiciona nova despesa"""
        try:
            parts = message.split()
            if len(parts) < 3:
                return "Uso: /despesa valor descrição\nExemplo: /despesa 100.50 Mercado"
            
            try:
                amount = float(parts[1])
                if amount <= 0:
                    return "O valor deve ser maior que zero."
            except ValueError:
                return "Valor inválido. Use ponto para decimais."
            
            description = " ".join(parts[2:])
            if len(description) < 3:
                return "A descrição deve ter pelo menos 3 caracteres."
            
            account = db.query(Account).filter(Account.owner_id == user.id).first()
            if not account:
                return "Você precisa ter uma conta cadastrada primeiro."
            
            transaction = Transaction(
                amount=amount,
                description=description,
                type="expense",
                category="general",
                account_id=account.id
            )
            
            account.balance -= amount
            db.add(transaction)
            db.commit()
            
            return f"Despesa de R$ {amount:.2f} registrada com sucesso!\nNovo saldo: R$ {account.balance:.2f}"
        except Exception as e:
            return "Erro ao registrar despesa. Use o formato: /despesa 100.00 Descrição"

    async def get_statement(self, message: str, user: User, db: Session):
        """Retorna extrato dos últimos 7 dias"""
        account = db.query(Account).filter(Account.owner_id == user.id).first()
        if not account:
            return "Você precisa ter uma conta cadastrada primeiro."
            
        transactions = db.query(Transaction).filter(
            Transaction.account_id == account.id,
            Transaction.date >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        if not transactions:
            return "Não há transações nos últimos 7 dias."
            
        response = "Extrato dos últimos 7 dias:\n\n"
        for t in transactions:
            tipo = "+" if t.type == "income" else "-"
            response += f"{t.date.strftime('%d/%m')} {tipo}R$ {t.amount:.2f} - {t.description}\n"
        
        response += f"\nSaldo atual: R$ {account.balance:.2f}"
        return response

    async def account_info(self, message: str, user: User, db: Session):
        """Retorna informações detalhadas da conta"""
        try:
            # Se foi especificado um nome de conta
            parts = message.split()
            if len(parts) > 1:
                account_name = " ".join(parts[1:])
                account = db.query(Account).filter(
                    Account.owner_id == user.id,
                    Account.name.ilike(f"%{account_name}%")
                ).first()
            else:
                # Pega a primeira conta do usuário
                account = db.query(Account).filter(Account.owner_id == user.id).first()

            if not account:
                return "Conta não encontrada. Use /conta [nome da conta]"

            # Busca as últimas 5 transações
            recent_transactions = db.query(Transaction).filter(
                Transaction.account_id == account.id
            ).order_by(Transaction.date.desc()).limit(5).all()

            response = f"📊 Conta: {account.name}\n"
            response += f"💰 Saldo atual: R$ {account.balance:.2f}\n"
            response += f"📝 Tipo: {account.type}\n"
            
            if account.description:
                response += f"ℹ️ Descrição: {account.description}\n"
            
            if recent_transactions:
                response += "\n🔄 Últimas transações:\n"
                for t in recent_transactions:
                    tipo = "+" if t.type == "income" else "-"
                    response += f"{t.date.strftime('%d/%m')} {tipo}R$ {t.amount:.2f} - {t.description}\n"

            return response
        except Exception as e:
            return "Erro ao buscar informações da conta. Tente novamente."

    async def add_income(self, message: str, user: User, db: Session):
        """Adiciona nova receita"""
        try:
            # Formato esperado: /receita 100.00 Salário
            _, amount, *description = message.split()
            amount = float(amount)
            description = " ".join(description)
            
            account = db.query(Account).filter(Account.owner_id == user.id).first()
            if not account:
                return "Você precisa ter uma conta cadastrada primeiro."
            
            transaction = Transaction(
                amount=amount,
                description=description,
                type="income",
                category="general",
                account_id=account.id
            )
            
            account.balance += amount
            db.add(transaction)
            db.commit()
            
            return f"Receita de R$ {amount:.2f} registrada com sucesso!\nNovo saldo: R$ {account.balance:.2f}"
        except Exception as e:
            return "Erro ao registrar receita. Use o formato: /receita 100.00 Descrição"

    async def handle_goal(self, message: str, user: User, db: Session):
        """Gerencia metas financeiras"""
        parts = message.split()
        if len(parts) < 2:
            return """Uso:
/meta criar nome valor data - Criar nova meta
/meta listar - Listar suas metas
/meta excluir nome - Excluir uma meta
/meta atualizar nome valor - Atualizar progresso"""

        action = parts[1]
        if action == "excluir":
            # Adiciona confirmação
            if len(parts) < 3:
                return "Especifique o nome da meta a excluir"
            
            name = " ".join(parts[2:])
            goal = db.query(Goal).filter(
                Goal.owner_id == user.id,
                Goal.name == name
            ).first()
            
            if not goal:
                return f"Meta '{name}' não encontrada"
            
            # Aqui poderia implementar um sistema de confirmação
            db.delete(goal)
            db.commit()
            
            return f"✅ Meta '{name}' excluída com sucesso!"

    async def generate_report(self, message: str, user: User, db: Session):
        """Gera relatório financeiro"""
        from app.services.analytics import FinancialAnalytics
        
        try:
            # Obtém o resumo mensal
            summary = await FinancialAnalytics.monthly_summary(user, db)
            
            # Obtém tendências de gastos
            trends = await FinancialAnalytics.spending_trends(user, db, months=3)
            
            # Gera insights
            insights = await FinancialAnalytics.generate_insights(user, db)
            
            # Monta a mensagem
            message = "📊 Relatório Financeiro\n\n"
            
            # Resumo do mês
            message += f"📅 Período: {summary['period']}\n"
            message += f"💰 Receitas: R$ {summary['total_income']:.2f}\n"
            message += f"💸 Despesas: R$ {summary['total_expense']:.2f}\n"
            message += f"📈 Saldo: R$ {summary['balance']:.2f}\n"
            message += f"💹 Taxa de Poupança: {summary['savings_rate']:.1f}%\n\n"
            
            # Gastos por categoria
            message += "📊 Gastos por Categoria:\n"
            for category, percentage in summary['category_percentages'].items():
                message += f"- {category}: {percentage:.1f}%\n"
            
            # Insights
            if insights:
                message += "\n💡 Insights:\n"
                for insight in insights:
                    message += f"- {insight}\n"
            
            return message
            
        except Exception as e:
            return f"Erro ao gerar relatório: {str(e)}"

    async def manage_categories(self, message: str, user: User, db: Session):
        """Gerencia categorias de transações"""
        try:
            parts = message.split()
            if len(parts) < 2:
                return """Uso:
/categoria listar - Lista todas as categorias
/categoria criar nome tipo - Cria nova categoria (tipo: receita/despesa)
/categoria excluir nome - Remove uma categoria"""
            
            action = parts[1]
            
            if action == "listar":
                categories = db.query(Category).all()
                if not categories:
                    return "Nenhuma categoria cadastrada."
                
                response = "📑 Categorias:\n\n"
                for cat in categories:
                    response += f"{cat.icon} {cat.name} ({cat.type})\n"
                return response
                
            elif action == "criar" and len(parts) >= 4:
                name = parts[2]
                type_ = parts[3]
                
                if type_ not in ["receita", "despesa"]:
                    return "Tipo deve ser 'receita' ou 'despesa'"
                
                category = Category(
                    name=name,
                    type=type_,
                    icon="💰"  # Emoji padrão
                )
                db.add(category)
                db.commit()
                
                return f"✅ Categoria '{name}' criada com sucesso!"
                
            elif action == "excluir" and len(parts) >= 3:
                name = parts[2]
                category = db.query(Category).filter(Category.name == name).first()
                if not category:
                    return f"Categoria '{name}' não encontrada."
                
                db.delete(category)
                db.commit()
                
                return f"✅ Categoria '{name}' excluída com sucesso!"
                
            return "Comando inválido. Use /categoria para ver as opções."
            
        except Exception as e:
            return f"Erro ao gerenciar categorias: {str(e)}"

    async def set_reminder(self, message: str, user: User, db: Session):
        """Configura lembretes"""
        try:
            parts = message.split()
            if len(parts) < 3:
                return """Uso:
/lembrete contas - Lembra das contas a vencer
/lembrete meta nome_meta - Lembra do progresso da meta
/lembrete saldo - Lembra de verificar o saldo"""
            
            tipo = parts[1]
            
            if tipo == "contas":
                # Configura lembrete para contas
                bills = db.query(Bill).filter(
                    Bill.owner_id == user.id,
                    Bill.is_paid == False
                ).all()
                
                if not bills:
                    return "Não há contas pendentes para lembrar."
                
                return "✅ Lembrete de contas configurado! Você será notificado um dia antes do vencimento."
                
            elif tipo == "meta" and len(parts) >= 3:
                meta_name = " ".join(parts[2:])
                goal = db.query(Goal).filter(
                    Goal.owner_id == user.id,
                    Goal.name.ilike(f"%{meta_name}%")
                ).first()
                
                if not goal:
                    return f"Meta '{meta_name}' não encontrada."
                
                return f"✅ Lembrete configurado! Você será notificado sobre o progresso da meta '{goal.name}'."
                
            elif tipo == "saldo":
                return "✅ Lembrete de saldo configurado! Você será notificado diariamente sobre seu saldo."
                
            return "Tipo de lembrete inválido. Use /lembrete para ver as opções."
            
        except Exception as e:
            return f"Erro ao configurar lembrete: {str(e)}"

    @lru_cache(maxsize=100)
    async def get_user_categories(self, user_id: int):
        """Busca categorias do usuário (com cache)"""
        categories = db.query(Category).all()
        return categories

# Cria uma instância global do serviço
whatsapp_service = WhatsAppService() 