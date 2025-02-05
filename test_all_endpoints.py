import requests
import logging
import time
from datetime import datetime, timedelta
import threading
import uvicorn
from app.main import app
from test_db_clean import clean_database
import json

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://bot-whats-9onh.onrender.com"

def run_server():
    """Inicia o servidor em uma thread separada"""
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")

class APITester:
    @classmethod
    def setup_class(cls):
        """Inicia o servidor antes dos testes"""
        cls.server_thread = threading.Thread(target=run_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        # Aguarda o servidor iniciar
        time.sleep(3)
    
    def __init__(self):
        self.token = None
        self.user_id = None
    
    def test_health(self):
        """Testa endpoint de health check"""
        for _ in range(3):  # Tenta 3 vezes
            try:
                response = requests.get(f"{BASE_URL}/health")
                assert response.status_code == 200, "Health check falhou"
                logger.info("✅ Health check OK")
                return
            except Exception as e:
                logger.warning(f"Tentativa de health check falhou: {str(e)}")
                time.sleep(2)
        raise Exception("Health check falhou após 3 tentativas")
        
    def test_register_user(self):
        """Testa registro de usuário"""
        data = {
            "email": "teste@exemplo.com",
            "password": "Senha123!",
            "name": "Usuário Teste"
        }
        response = requests.post(f"{BASE_URL}/users/", json=data)
        assert response.status_code in [200, 400], "Registro falhou"
        logger.info("✅ Registro de usuário OK")
        
    def test_login(self):
        """Testa login"""
        data = {
            "username": "teste@exemplo.com",
            "password": "Senha123!"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        assert response.status_code == 200, "Login falhou"
        self.token = response.json()["access_token"]
        logger.info("✅ Login OK")
        
    def test_create_account(self):
        """Testa criação de conta"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "name": "Conta Principal",
            "balance": 1000.00
        }
        response = requests.post(f"{BASE_URL}/finance/accounts/", json=data, headers=headers)
        assert response.status_code == 200, "Criação de conta falhou"
        self.account_id = response.json()["id"]  # Guarda o ID da conta
        logger.info("✅ Criação de conta OK")
        
    def test_create_category(self):
        """Testa criação de categoria"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "name": "Alimentação",
            "type": "expense"
        }
        response = requests.post(f"{BASE_URL}/finance/categories/", json=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Erro na criação da categoria: {response.json()}")
        assert response.status_code == 200, "Criação de categoria falhou"
        self.category_id = response.json()["id"]
        logger.info("✅ Criação de categoria OK")
        
    def test_create_transaction(self):
        """Testa criação de transação"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "amount": 50.00,
            "type": "expense",
            "description": "Almoço",
            "account_id": self.account_id,
            "category_id": self.category_id
        }
        response = requests.post(f"{BASE_URL}/finance/transactions/", json=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Erro na criação da transação: {response.json()}")
            logger.error(f"Dados enviados: {data}")
        assert response.status_code == 200, "Criação de transação falhou"
        logger.info("✅ Criação de transação OK")
        
    def test_create_bill(self):
        """Testa criação de conta a pagar"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "description": "Conta Teste",
            "amount": 50.0,
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        response = requests.post(f"{BASE_URL}/finance/bills/", json=data, headers=headers)
        assert response.status_code == 200, "Criação de conta a pagar falhou"
        logger.info("✅ Criação de conta a pagar OK")
        
    def test_create_goal(self):
        """Testa criação de meta"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "name": "Meta Teste",
            "target_amount": 1000.0,
            "current_amount": 0.0,  # Adicionado valor inicial
            "deadline": (datetime.now() + timedelta(days=30)).isoformat()
        }
        response = requests.post(f"{BASE_URL}/finance/goals/", json=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Erro na criação da meta: {response.json()}")
            logger.error(f"Dados enviados: {data}")
        assert response.status_code == 200, "Criação de meta falhou"
        logger.info("✅ Criação de meta OK")

def test_api():
    # 1. Registro
    register_data = {
        "email": "teste@exemplo.com",
        "password": "Senha123!",
        "name": "Usuário Teste"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=register_data)
    logger.info(f"Registro: {response.status_code}")
    
    # 2. Login
    login_data = {
        "username": "teste@exemplo.com",
        "password": "Senha123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    logger.info(f"Login: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Criar categoria
        category_data = {
            "name": "Alimentação",
            "type": "expense"
        }
        response = requests.post(
            f"{BASE_URL}/finance/categories/",
            headers=headers,
            json=category_data
        )
        logger.info(f"Criar categoria: {response.status_code}")
        
        # 4. Criar conta
        account_data = {
            "name": "Conta Principal",
            "balance": 1000.00
        }
        response = requests.post(
            f"{BASE_URL}/finance/accounts/",
            headers=headers,
            json=account_data
        )
        logger.info(f"Criar conta: {response.status_code}")
        
        # 5. Criar transação
        transaction_data = {
            "amount": 50.00,
            "type": "expense",
            "description": "Almoço",
            "account_id": 1,
            "category_id": 1
        }
        response = requests.post(
            f"{BASE_URL}/finance/transactions/",
            headers=headers,
            json=transaction_data
        )
        logger.info(f"Criar transação: {response.status_code}")

def run_all_tests():
    """Executa todos os testes em sequência"""
    try:
        # Limpa o banco antes dos testes
        if not clean_database():
            raise Exception("Falha ao limpar banco de dados")
        
        # Inicializa o servidor
        tester = APITester()
        APITester.setup_class()
        
        # Aguarda o servidor estar pronto
        logger.info("Aguardando servidor iniciar...")
        time.sleep(3)
        
        # Testes em ordem
        tester.test_health()
        time.sleep(1)
        
        # Autenticação
        tester.test_register_user()
        time.sleep(1)
        tester.test_login()
        time.sleep(1)
        
        # Categorias primeiro
        tester.test_create_category()
        time.sleep(1)
        
        # Depois contas
        tester.test_create_account()
        time.sleep(1)
        
        # Então transações e contas a pagar
        tester.test_create_transaction()
        time.sleep(1)
        tester.test_create_bill()
        time.sleep(1)
        
        # Por fim, metas
        tester.test_create_goal()
        
        logger.info("\n✨ Todos os testes passaram!")
        return True
        
    except AssertionError as e:
        logger.error(f"❌ Teste falhou: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    # Configura logging mais detalhado
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_api()
    success = run_all_tests()
    exit(0 if success else 1) 