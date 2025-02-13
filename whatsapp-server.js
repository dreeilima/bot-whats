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
    ? "https://bot-whats-9onh.onrender.com/webhook" // URL do serviço atual
    : "http://localhost:8000/webhook"; // URL local para desenvolvimento

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

        // Processa a mensagem
        const response = processMessage(message.body, message.from);

        // Envia resposta
        await client.sendText(message.from, response);
        console.log("✅ Resposta enviada:", response);
      } catch (error) {
        console.error("❌ Erro ao processar mensagem:", error);
        await client.sendText(
          message.from,
          "Desculpe, ocorreu um erro ao processar sua mensagem."
        );
      }
    });
  } catch (error) {
    console.error("❌ Erro ao iniciar cliente:", error);
    setTimeout(initializeWhatsApp, 5000);
  }
}

// Função para processar mensagem e retornar resposta
function processMessage(text, from) {
  // Converte para minúsculo para comparação
  const command = text.toLowerCase().trim();

  // Comandos básicos
  if (command === "oi" || command === "olá" || command === "ola") {
    return (
      "Olá! Eu sou o FinBot 🤖\nPosso te ajudar com:\n\n" +
      "📝 /receita [valor] [descrição] #categoria\n" +
      "💰 /despesa [valor] [descrição] #categoria\n" +
      "📊 /relatorio [diario|semanal|mensal]\n" +
      "❓ /ajuda - para ver todos os comandos"
    );
  }

  if (command === "/ajuda") {
    return (
      "Comandos disponíveis:\n\n" +
      "📝 Registrar receita:\n" +
      "/receita 100 Salário #trabalho\n\n" +
      "💰 Registrar despesa:\n" +
      "/despesa 50 Mercado #alimentacao\n\n" +
      "📊 Ver relatórios:\n" +
      "/relatorio diario\n" +
      "/relatorio semanal\n" +
      "/relatorio mensal"
    );
  }

  // Comandos de finanças
  if (command.startsWith("/receita")) {
    // TODO: Implementar lógica de receita
    return "🎉 Receita registrada com sucesso!";
  }

  if (command.startsWith("/despesa")) {
    // TODO: Implementar lógica de despesa
    return "📝 Despesa registrada com sucesso!";
  }

  if (command.startsWith("/relatorio")) {
    // TODO: Implementar lógica de relatório
    return "📊 Aqui está seu relatório...";
  }

  // Se não reconhecer o comando
  return "Desculpe, não entendi este comando. Digite /ajuda para ver as opções disponíveis.";
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

// Rota de documentação
app.get("/docs", (req, res) => {
  res.send(`
    <html>
      <head>
        <title>FinBot API Documentation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { 
            font-family: Arial; 
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
          }
          .endpoint {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
          }
          .method {
            font-weight: bold;
            color: #0066cc;
          }
          .url {
            color: #666;
            font-family: monospace;
          }
          h2 {
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
          }
        </style>
      </head>
      <body>
        <h1>🤖 FinBot API Documentation</h1>
        
        <h2>Endpoints Disponíveis</h2>

        <div class="endpoint">
          <p><span class="method">GET</span> <span class="url">/whatsapp</span></p>
          <p>Página de administração do bot. Mostra QR Code para conexão e status.</p>
          <p>Uso: Apenas para administradores</p>
        </div>

        <div class="endpoint">
          <p><span class="method">GET</span> <span class="url">/whatsapp/conversar</span></p>
          <p>Página para usuários iniciarem conversa com o bot.</p>
          <p>Contém QR Code e botão para WhatsApp.</p>
        </div>

        <div class="endpoint">
          <p><span class="method">GET</span> <span class="url">/whatsapp/qr</span></p>
          <p>Retorna o QR Code atual em JSON.</p>
          <p>Resposta: { qr: "string" } ou { connected: true }</p>
        </div>

        <div class="endpoint">
          <p><span class="method">GET</span> <span class="url">/status</span></p>
          <p>Retorna status atual do bot.</p>
          <p>Resposta: { status: "connected"|"disconnected", qrAvailable: boolean }</p>
        </div>

        <h2>Informações Adicionais</h2>
        <ul>
          <li>Número do Bot: ${BOT_NUMBER}</li>
          <li>Ambiente: ${process.env.NODE_ENV || "development"}</li>
          <li>Versão: ${require("./package.json").version}</li>
        </ul>
      </body>
    </html>
  `);
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
