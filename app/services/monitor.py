import time
import subprocess
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_monitor.log'),
        logging.StreamHandler()
    ]
)

class BotMonitor:
    def __init__(self):
        self.process = None
        self.last_restart = None
        self.max_restarts = 5
        self.restart_count = 0
        self.restart_interval = 3600  # 1 hora

    def start_bot(self):
        """Inicia o bot"""
        try:
            self.process = subprocess.Popen(
                ["python", "setup.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.info("Bot iniciado com sucesso")
            self.last_restart = datetime.now()
            return True
        except Exception as e:
            logging.error(f"Erro ao iniciar bot: {str(e)}")
            return False

    def check_bot_health(self):
        """Verifica se o bot está respondendo"""
        if self.process and self.process.poll() is not None:
            logging.warning("Bot não está respondendo")
            return False
        return True

    def restart_bot(self):
        """Reinicia o bot"""
        now = datetime.now()
        
        # Verifica limite de reinicializações
        if (self.last_restart and 
            (now - self.last_restart).total_seconds() < self.restart_interval):
            self.restart_count += 1
            if self.restart_count >= self.max_restarts:
                logging.error("Muitas tentativas de reinicialização. Aguardando intervalo.")
                time.sleep(self.restart_interval)
                self.restart_count = 0
                return False
        else:
            self.restart_count = 0

        # Mata o processo atual se existir
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()

        # Inicia novo processo
        return self.start_bot()

    def run(self):
        """Loop principal do monitor"""
        logging.info("Iniciando monitor do bot")
        
        if not self.start_bot():
            logging.error("Falha ao iniciar bot")
            return

        while True:
            try:
                if not self.check_bot_health():
                    logging.warning("Reiniciando bot...")
                    if not self.restart_bot():
                        logging.error("Falha ao reiniciar bot")
                        time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
                        continue

                time.sleep(30)  # Verifica a cada 30 segundos
                
            except KeyboardInterrupt:
                logging.info("Monitor encerrado pelo usuário")
                if self.process:
                    self.process.terminate()
                break
            except Exception as e:
                logging.error(f"Erro no monitor: {str(e)}")
                time.sleep(60) 