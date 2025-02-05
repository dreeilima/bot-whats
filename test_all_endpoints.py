import requests
import logging
import time
from datetime import datetime, timedelta
import threading
import uvicorn
from app.main import app
from test_db_clean import clean_database

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:10000"

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
            "email": "test@example.com",
            "password": "test123",
            "full_name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/users/", json=data)
        assert response.status_code in [200, 400], "Registro falhou"
        logger.info("✅ Registro de usuário OK")
        
    def test_login(self):
        """Testa login"""
        data = {
            "username": "test@example.com",
            "password": "test123"
        }
        response = requests.post(f"{BASE_URL}/login", data=data)
        assert response.status_code == 200, "Login falhou"
        self.token = response.json()["access_token"]
        logger.info("✅ Login OK")
        
    def test_create_account(self):
        """Testa criação de conta"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "name": "Conta Teste",
            "balance": 1000.0,
            "type": "checking",
            "description": "Conta para testes"
        }
        response = requests.post(f"{BASE_URL}/finance/accounts/", json=data, headers=headers)
        assert response.status_code == 200, "Criação de conta falhou"
        self.account_id = response.json()["id"]  # Guarda o ID da conta
        logger.info("✅ Criação de conta OK")
        
    def test_create_category(self):
        """Testa criação de categoria"""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "name": f"Salário {datetime.now().timestamp()}",  # Nome único
            "type": "income",
            "icon": "💵",
            "description": "Renda mensal"
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
            "amount": 100.0,
            "type": "income",
            "description": "Teste",
            "account_id": self.account_id,
            "category_id": self.category_id,
            "date": datetime.now().isoformat()
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
    
    success = run_all_tests()
    exit(0 if success else 1) 