import requests
import sys
from test_db import test_connection

def run_local_tests():
    # 1. Testa conexão com banco
    print("\n🔌 Testando conexão com banco...")
    if not test_connection():
        return False
    
    # 2. Inicia aplicação localmente
    print("\n🚀 Iniciando aplicação...")
    try:
        import uvicorn
        from app.main import app
        
        # Inicia servidor em thread separada
        import threading
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=10000)
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Aguarda servidor iniciar
        import time
        time.sleep(5)
        
        # 3. Testa endpoints
        response = requests.get("http://localhost:10000/health")
        if response.status_code == 200:
            print("✅ API respondendo!")
        else:
            print("❌ API com erro")
            return False
            
        print("\n✨ Todos os testes passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_local_tests()
    sys.exit(0 if success else 1) 