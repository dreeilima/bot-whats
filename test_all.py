import subprocess
import requests
import time
import sys

def run_tests():
    # 1. Testa build do Docker
    print("🔨 Testando build do Docker...")
    result = subprocess.run(["docker", "build", "-t", "bot-whats", "."], capture_output=True)
    if result.returncode != 0:
        print("❌ Erro no build do Docker")
        print(result.stderr.decode())
        return False
    print("✅ Build do Docker OK!")

    # 2. Testa conexão com banco
    print("\n🔌 Testando conexão com banco...")
    from test_db import test_connection
    if not test_connection():
        return False
    
    # 3. Inicia container em background
    print("\n🚀 Iniciando container...")
    container = subprocess.Popen([
        "docker", "run", "-p", "10000:10000",
        "-e", "DATABASE_URL=postgresql://postgres.xkepzvrnevgeifexcizr:Drey1992.@db.xkepzvrnevgeifexcizr.supabase.co:5432/postgres?sslmode=require",
        "-e", "JWT_SECRET_KEY=5VkIR4wdaoZUzk1004AHE7d8Qd9JtK/+UvDmuWrvbuU=",
        "-e", "WHATSAPP_NUMBER=5511953238980",
        "-e", "PORT=10000",
        "-e", "IP=0.0.0.0",
        "bot-whats"
    ])

    # Aguarda API iniciar
    print("⏳ Aguardando API iniciar...")
    time.sleep(10)

    # 4. Testa endpoints
    try:
        response = requests.get("http://localhost:10000/health")
        if response.status_code == 200:
            print("✅ API respondendo!")
        else:
            print("❌ API com erro")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar API: {str(e)}")
        return False
    finally:
        # Limpa
        container.terminate()
        subprocess.run(["docker", "rm", "-f", "$(docker ps -aq)"], shell=True)

    print("\n✨ Todos os testes passaram!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 