import logging
from app.services.whatsapp import whatsapp_service
import time
import webbrowser
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_qr_html(qr_code):
    """Salva QR code em arquivo HTML"""
    html = f"""
    <html>
        <head>
            <title>WhatsApp QR Code</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }}
                img {{
                    max-width: 300px;
                    margin: 20px 0;
                }}
                .commands {{
                    text-align: left;
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <h1>Conectar ao WhatsApp</h1>
            <p>Escaneie o QR Code abaixo com seu WhatsApp</p>
            <img src="{qr_code}" alt="WhatsApp QR Code"/>
            <div class="commands">
                <h2>Depois de escanear, envie:</h2>
                <ul>
                    <li><code>oi</code> - Para começar</li>
                    <li><code>/ajuda</code> - Ver todos os comandos</li>
                </ul>
            </div>
        </body>
    </html>
    """
    
    with open("whatsapp_qr.html", "w") as f:
        f.write(html)
    
    return os.path.abspath("whatsapp_qr.html")

def main():
    try:
        logger.info("🤖 Iniciando WhatsApp Bot...")
        
        # Gera QR Code
        qr = whatsapp_service.initialize()
        if qr:
            # Salva e abre QR code
            qr_file = save_qr_html(qr)
            webbrowser.open(f"file://{qr_file}")
            logger.info("✅ QR Code gerado! Escaneie com seu WhatsApp")
        else:
            logger.error("❌ Erro ao gerar QR Code")
            return
            
        logger.info("⚡ Pressione Ctrl+C para finalizar")
        
        # Mantém rodando
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Bot finalizado pelo usuário")
        # Remove arquivo temporário
        if os.path.exists("whatsapp_qr.html"):
            os.remove("whatsapp_qr.html")
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    main() 