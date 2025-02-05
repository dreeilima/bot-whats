import logging
import time
import psycopg2
import requests
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
DATABASE_URL = "postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
API_URL = "http://localhost:10000"

def test_database():
    """Testa conexão com banco de dados"""
    try:
        logger.info("\n🔍 Testando conexão com banco...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Testa SELECT
        cur.execute('SELECT version()')
        version = cur.fetchone()
        logger.info(f"✅ Conexão OK! Versão: {version[0]}")
        
        # Testa permissões
        cur.execute('SELECT current_user, current_database()')
        user, db = cur.fetchone()
        logger.info(f"✅ Usuário: {user}, Banco: {db}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Erro no banco: {str(e)}")
        return False

def test_api_endpoints():
    """Testa todos os endpoints da API"""
    try:
        logger.info("\n🔍 Testando endpoints...")
        
        # Health check
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200, "Health check falhou"
        logger.info("✅ Health check OK")
        
        # Registro de usuário
        user_data = {
            "email": f"test_{int(time.time())}@test.com",
            "password": "Test@123",
            "name": "Test User"
        }
        response = requests.post(f"{API_URL}/users/", json=user_data)
        assert response.status_code == 200, "Registro falhou"
        logger.info("✅ Registro OK")
        
        # Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        response = requests.post(f"{API_URL}/login", data=login_data)
        assert response.status_code == 200, "Login falhou"
        token = response.json()["access_token"]
        logger.info("✅ Login OK")
        
        # Headers com token
        headers = {"Authorization": f"Bearer {token}"}
        
        # Criar categoria
        category_data = {"name": "Test Category", "type": "expense"}
        response = requests.post(f"{API_URL}/finance/categories/", json=category_data, headers=headers)
        assert response.status_code == 200, "Criação de categoria falhou"
        category_id = response.json()["id"]
        logger.info("✅ Categoria OK")
        
        # Criar conta
        account_data = {"name": "Test Account", "balance": 1000.0}
        response = requests.post(f"{API_URL}/finance/accounts/", json=account_data, headers=headers)
        assert response.status_code == 200, "Criação de conta falhou"
        account_id = response.json()["id"]
        logger.info("✅ Conta OK")
        
        # Criar transação
        transaction_data = {
            "amount": 100.0,
            "type": "expense",
            "description": "Test Transaction",
            "date": datetime.now().isoformat(),
            "account_id": account_id,
            "category_id": category_id
        }
        response = requests.post(f"{API_URL}/finance/transactions/", json=transaction_data, headers=headers)
        assert response.status_code == 200, "Criação de transação falhou"
        logger.info("✅ Transação OK")
        
        # Criar meta
        goal_data = {
            "name": "Test Goal",
            "target_amount": 1000.0,
            "current_amount": 0.0,
            "deadline": (datetime.now() + timedelta(days=30)).isoformat()
        }
        response = requests.post(f"{API_URL}/finance/goals/", json=goal_data, headers=headers)
        assert response.status_code == 200, "Criação de meta falhou"
        logger.info("✅ Meta OK")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro na API: {str(e)}")
        return False

def main():
    """Executa todos os testes"""
    try:
        # Testa banco
        db_ok = test_database()
        if not db_ok:
            return False
            
        # Inicia servidor em background (se necessário)
        # ...
        
        # Aguarda servidor
        time.sleep(2)
        
        # Testa API
        api_ok = test_api_endpoints()
        if not api_ok:
            return False
            
        logger.info("\n✨ Todos os testes passaram!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 