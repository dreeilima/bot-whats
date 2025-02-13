const express = require("express");
const { create } = require("venom-bot");
const qrcode = require("qrcode");
const axios = require("axios");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(express.json());

const PORT = 3001; // Força a porta 3001
let currentQR = null;
let clientReady = false;
let client = null;
const SESSION_DIR = "./sessions";

// Garante que o diretório de sessões existe
if (!fs.existsSync(SESSION_DIR)) {
  fs.mkdirSync(SESSION_DIR);
}

// Ajuste a URL do webhook baseado no ambiente
const webhookUrl =
  process.env.NODE_ENV === "production"
    ? "https://bot-whats-9onh.onrender.com/whatsapp/webhook"
    : "http://localhost:8000/whatsapp/webhook";

// No início do arquivo, após os requires
console.log("🚀 Iniciando servidor...");

// Configurações do Venom para produção
const venomOptions = {
  session: "finbot-session", // Nome da sessão
  multidevice: true, // Habilita suporte multidevice
  headless: true,
  useChrome: false,
  debug: false,
  logQR: true,
  disableWelcome: true,
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
  createPathFileToken: true, // Importante para criar o arquivo de sessão
  waitForLogin: false,
  folderNameToken: "tokens", // Pasta onde serão salvos os tokens
  mkdirFolderToken: true, // Cria a pasta se não existir
  catchQR: (base64Qr, asciiQR, attempts) => {
    console.log("Tentativa", attempts, "de gerar QR Code");
    currentQR = base64Qr;

    // Salva o QR code em um arquivo para debug
    if (base64Qr) {
      const qrPath = path.join(__dirname, "qr-code.txt");
      fs.writeFileSync(qrPath, base64Qr);
      console.log("QR Code salvo em:", qrPath);
    }
  },
  statusFind: (statusSession, session) => {
    console.log("Status da Sessão:", statusSession);
    if (
      statusSession === "qrReadSuccess" ||
      statusSession === "inChat" ||
      statusSession === "isLogged"
    ) {
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

    // Garante que as pastas existem
    if (!fs.existsSync("./tokens")) {
      fs.mkdirSync("./tokens", { recursive: true });
    }
    if (!fs.existsSync("./sessions")) {
      fs.mkdirSync("./sessions", { recursive: true });
    }

    // Limpa sessões antigas
    if (fs.existsSync("./tokens")) {
      fs.rmSync("./tokens", { recursive: true, force: true });
      fs.mkdirSync("./tokens");
      console.log("🧹 Sessões antigas removidas");
    }

    client = await create({
      session: "finbot-session",
      ...venomOptions,
    });

    // Configurar listener de mensagens
    client.onMessage(async (message) => {
      if (message.isGroupMsg) return;

      try {
        console.log("📩 Mensagem recebida:", message.body);

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
            return status >= 200 && status < 500;
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
        console.error("❌ Erro ao processar mensagem:", error.message);
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
  console.log(`🚀 Servidor WhatsApp rodando em http://localhost:${PORT}`);
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
