import socket
import logging
import time
import dns.resolver  # Para teste de DNS mais robusto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hosts para testar
hosts = [
    ("db.xkepzvrnevgeifexcizr.supabase.co", 5432),
    ("aws-0-us-west-1.pooler.supabase.com", 6543)
]

def test_connection(host, port):
    sock = None
    try:
        logger.info(f"\nTestando conexão com {host}:{port}")
        start = time.time()
        
        # Tenta resolver o DNS de várias formas
        try:
            # Tenta resolver usando dns.resolver
            answers = dns.resolver.resolve(host, 'A')
            ip = answers[0].to_text()
            logger.info(f"DNS resolvido (via resolver): {ip}")
        except Exception as dns_error:
            try:
                # Tenta resolver usando socket
                ip = socket.gethostbyname(host)
                logger.info(f"DNS resolvido (via socket): {ip}")
            except Exception as e:
                logger.error(f"❌ Erro ao resolver DNS: {str(e)}")
                return False
        
        # Tenta conectar
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        logger.info(f"Tentando conectar em {ip}:{port}...")
        result = sock.connect_ex((ip, port))
        
        end = time.time()
        duration = round(end - start, 2)
        
        if result == 0:
            logger.info(f"✅ Porta {port} está aberta! (tempo: {duration}s)")
            return True
        else:
            logger.error(f"❌ Porta {port} está fechada (erro: {result})")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao conectar: {str(e)}")
        return False
    finally:
        if sock:
            sock.close()

def test_ping(host):
    """Testa ping para o host"""
    try:
        logger.info(f"\nTestando ping para {host}")
        import subprocess
        
        # Ajusta comando ping para Windows/Linux
        if os.name == 'nt':  # Windows
            ping_cmd = ['ping', '-n', '3', host]
        else:  # Linux/Mac
            ping_cmd = ['ping', '-c', '3', host]
            
        result = subprocess.run(ping_cmd, 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True)
        
        if result.returncode == 0:
            logger.info("✅ Ping successful!")
            logger.info(result.stdout)
        else:
            logger.error("❌ Ping failed!")
            logger.error(result.stderr)
            
    except Exception as e:
        logger.error(f"❌ Erro ao executar ping: {str(e)}")

def main():
    # Primeiro testa DNS e ping
    for host, _ in hosts:
        logger.info("\n" + "="*50)
        test_ping(host)
        
    # Depois testa conexões
    for host, port in hosts:
        logger.info("\n" + "="*50)
        test_connection(host, port)
        time.sleep(2)

if __name__ == "__main__":
    # Instala dnspython se necessário
    try:
        import dns.resolver
    except ImportError:
        logger.info("Instalando dnspython...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'dnspython'])
        import dns.resolver
        
    import os
    main() 