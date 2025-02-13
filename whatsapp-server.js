const express = require("express");
const { create } = require("venom-bot");
const qrcode = require("qrcode");
const axios = require("axios");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3001; // Usa a porta do ambiente ou 3001 como fallback
let currentQR = null;
let clientReady = false;
let client = null;

// Configurações de sessão
const SESSION_DIR =
  process.env.NODE_ENV === "production"
    ? "/app/sessions" // Diretório persistente no Render
    : "./sessions"; // Diretório local para desenvolvimento

// Garante que o diretório de sessões existe
if (!fs.existsSync(SESSION_DIR)) {
  fs.mkdirSync(SESSION_DIR, { recursive: true });
}

// Ajuste a URL do webhook baseado no ambiente
const webhookUrl =
  process.env.NODE_ENV === "production"
    ? "https://finbot-api-9onh.onrender.com/webhook" // URL correta sem /whatsapp
    : "http://localhost:8000/webhook"; // URL local

// Adiciona log para debug do ambiente
console.log("🌍 Ambiente:", process.env.NODE_ENV);
console.log("🔗 Webhook URL:", webhookUrl);

// No início do arquivo, após os requires
console.log("🚀 Iniciando servidor...");

// Configurações do Venom para produção
const venomOptions = {
  session: "finbot-session",
  headless: true,
  useChrome: false,
  debug: false,
  logQR: true,
  createPathFileToken: true,
  folderNameToken: SESSION_DIR,
  browserArgs: [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--single-process",
    "--disable-gpu",
  ],
  catchQR: (base64Qr, asciiQR) => {
    console.log("\n\n==== QR CODE ====\n");
    console.log(asciiQR); // Exibe QR code em ASCII no console
    console.log("\n================\n");
    currentQR = base64Qr;
  },
  statusFind: (statusSession) => {
    console.log("Status da Sessão:", statusSession);
    if (statusSession === "inChat" || statusSession === "isLogged") {
      console.log("✅ WhatsApp conectado!");
      clientReady = true;
      currentQR = null;
    }
  },
};

// Função para inicializar o cliente WhatsApp
async function initializeWhatsApp() {
  try {
    console.log("🚀 Iniciando cliente WhatsApp...");
    client = await create(venomOptions);

    // Configurar listener de mensagens
    client.onMessage(async (message) => {
      if (message.isGroupMsg) return;

      try {
        console.log("📩 Mensagem recebida:", message.body);
        console.log("🔗 Usando webhook:", webhookUrl);

        // Ajusta estrutura do payload conforme API Python espera
        const payload = {
          message: {
            from: message.from.replace("@c.us", ""),
            text: message.body,
          },
        };

        console.log("📤 Enviando para webhook:", payload);

        const response = await axios({
          method: "post",
          url: webhookUrl,
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          data: payload,
          validateStatus: function (status) {
            return status >= 200 && status < 500; // Aceita qualquer status 2xx-4xx
          },
        });

        console.log("📥 Status da resposta:", response.status);
        console.log("📥 Dados da resposta:", response.data);

        if (
          response.data &&
          response.data.message === "success" &&
          response.data.response
        ) {
          await client.sendText(message.from, response.data.response);
          console.log("✅ Resposta enviada:", response.data.response);
        } else {
          console.log("⚠️ Estrutura da resposta inválida:", response.data);
          await client.sendText(
            message.from,
            "Desculpe, ocorreu um erro ao processar sua mensagem."
          );
        }
      } catch (error) {
        console.error("❌ Erro ao processar mensagem:", error);
        if (error.response) {
          console.error("Status:", error.response.status);
          console.error("Headers:", error.response.headers);
          console.error("Data:", error.response.data);
        }
      }
    });
  } catch (error) {
    console.error("❌ Erro ao iniciar cliente:", error);
    setTimeout(initializeWhatsApp, 5000);
  }
}

// Adiciona prefixo para as rotas do WhatsApp
const whatsappRouter = express.Router();

// Move a rota do QR Code para o router
whatsappRouter.get("/", (req, res) => {
  console.log("📱 Rota principal acessada");
  res.send(`
    <html>
      <head>
        <title>FinBot Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { 
            font-family: Arial; 
            text-align: center; 
            padding: 20px;
            background: #f5f5f5;
          }
          .qr-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px auto;
            max-width: 400px;
          }
          img {
            max-width: 100%;
            height: auto;
          }
          .error {
            color: red;
            margin: 10px 0;
          }
          .success {
            color: green;
            margin: 10px 0;
          }
          .qr-container img {
            border: 10px solid white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🤖 FinBot Admin</h1>
          
          <div class="qr-container">
            ${
              clientReady
                ? '<h2 class="success">✅ Bot Conectado!</h2>'
                : currentQR
                ? `<h2>📱 Escaneie o QR Code</h2>
                     <img src="${currentQR}" alt="QR Code" />`
                : `<h2 class="error">⏳ Gerando QR Code...</h2>
                     <p>Se o QR Code não aparecer em 30 segundos, atualize a página.</p>`
            }
          </div>

          <div id="status"></div>
          
          <button onclick="location.reload()" class="whatsapp-button">
            🔄 Atualizar QR Code
          </button>
        </div>

        <script>
          // Atualiza status a cada 5 segundos
          setInterval(() => {
            fetch('/whatsapp/status')
              .then(res => res.json())
              .then(data => {
                const status = document.getElementById('status');
                status.textContent = data.message || 'Aguardando...';
              });
          }, 5000);
        </script>
      </body>
    </html>
  `);
});

// Rota para obter o QR code atual
whatsappRouter.get("/qr", (req, res) => {
  if (currentQR) {
    res.json({ qr: currentQR });
  } else if (clientReady) {
    res.json({ connected: true });
  } else {
    res.json({ error: "QR Code não disponível" });
  }
});

// Número do WhatsApp do bot (com código do país)
const BOT_NUMBER = "5511965905750";

// Rota para usuários iniciarem conversa
whatsappRouter.get("/conversar", (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Conversar com FinBot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { 
            font-family: Arial; 
            text-align: center; 
            padding: 20px;
            background: #f5f5f5;
          }
          .container {
            max-width: 600px;
            margin: 0 auto;
          }
          .whatsapp-button {
            background: #25D366;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 18px;
            display: inline-block;
            margin-top: 20px;
          }
          .qr-code {
            margin: 20px auto;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 300px;
          }
          .qr-code img {
            max-width: 100%;
            height: auto;
          }
          .or-divider {
            margin: 20px 0;
            font-size: 18px;
            color: #666;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>💬 Conversar com FinBot</h1>
          
          <div class="qr-code">
            <h2>Opção 1: Escaneie o QR Code</h2>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://wa.me/${BOT_NUMBER}" alt="QR Code WhatsApp"/>
          </div>

          <div class="or-divider">- OU -</div>

          <div>
            <h2>Opção 2: Clique no botão</h2>
            <p>Para iniciar uma conversa com o FinBot no WhatsApp</p>
            <a href="https://wa.me/${BOT_NUMBER}" class="whatsapp-button" target="_blank">
              Iniciar Conversa
            </a>
          </div>
        </div>
      </body>
    </html>
  `);
});

// Registra o router com prefixo
app.use("/whatsapp", whatsappRouter);

// Rota de status
app.get("/status", (req, res) => {
  res.json({
    status: clientReady ? "connected" : "disconnected",
    qrAvailable: currentQR !== null,
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor WhatsApp rodando na porta ${PORT}`);
  console.log("⏳ Iniciando cliente WhatsApp...");
  initializeWhatsApp();
});

// Tratamento de erros
process.on("unhandledRejection", (error) => {
  console.error("🔥 Erro não tratado:", error);
});

process.on("uncaughtException", (error) => {
  console.error("🔥 Exceção não capturada:", error);
});
