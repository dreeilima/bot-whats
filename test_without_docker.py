import requests
import sys
import logging
import time
from test_db import test_connection

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_local_tests():
    # 1. Testa conexão com banco com retry
    print("\n🔌 Testando conexão com banco...")
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if test_connection():
                break
            retry_count += 1
            if retry_count == max_retries:
                print("❌ Falha ao conectar ao banco após várias tentativas")
                return False
            print(f"Tentativa {retry_count} falhou, tentando novamente em 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False
    
    # 2. Inicia aplicação localmente
    print("\n🚀 Iniciando aplicação...")
    try:
        import uvicorn
        from app.main import app
        from app.db.session import initialize_db
        from app.db.migrations import run_migrations
        
        # Tenta inicializar banco
        initialize_db()
        run_migrations()
        
        # Inicia servidor em thread separada
        import threading
        def run_server():
            uvicorn.run(
                app, 
                host="0.0.0.0", 
                port=10000,
                log_level="info",
                reload=False
            )
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Aguarda servidor iniciar
        time.sleep(5)
        
        # 3. Testa endpoints
        print("\n🔍 Testando endpoints...")
        
        # Health check
        response = requests.get("http://localhost:10000/health")
        if response.status_code == 200:
            print("✅ Health check OK!")
        else:
            print("❌ Health check falhou")
            return False
            
        # Login (opcional)
        try:
            response = requests.post(
                "http://localhost:10000/login",
                data={
                    "username": "test@example.com",
                    "password": "test123"
                }
            )
            print(f"Login status: {response.status_code}")
        except:
            print("⚠️ Login não testado (esperado em ambiente de teste)")
            
        print("\n✨ Todos os testes passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_local_tests()
    sys.exit(0 if success else 1) 