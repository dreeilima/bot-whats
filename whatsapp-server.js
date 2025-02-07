const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const express = require("express");
const qrcode = require("qrcode");
const fetch = require("node-fetch");
const fs = require("fs");
const app = express();
app.use(express.json());

// Porta para a API
const PORT = process.env.PORT || 3001;

// Status da conexão
let connectionStatus = "disconnected";
let currentQR = "";
let sock = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000; // 3 segundos

// Configuração de logs
function log(message, type = "info") {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${type.toUpperCase()}: ${message}\n`;
  console.log(logMessage);
  fs.appendFileSync("whatsapp.log", logMessage);
}

// Adicione esta função
function generateSmallQR(qr) {
  return qrcode.toString(qr, {
    type: "terminal",
    small: true,
    margin: 1,
    scale: 1,
  });
}

async function connectToWhatsApp() {
  try {
    log("Iniciando conexão...");

    // Remove auth_info para forçar novo QR
    if (fs.existsSync("auth_info")) {
      fs.rmSync("auth_info", { recursive: true, force: true });
    }

    const { state, saveCreds } = await useMultiFileAuthState("auth_info");

    // Configuração mais simples
    sock = makeWASocket({
      auth: state,
      printQRInTerminal: false, // Desabilita QR padrão
      browser: ["Chrome", "Windows", "10"],
      defaultQueryTimeoutMs: undefined,
    });

    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;
      log(`Status da conexão: ${connection}`);

      if (qr) {
        // Gera QR code menor para o terminal
        const smallQR = await generateSmallQR(qr);
        console.log("\nEscaneie o QR Code abaixo:\n");
        console.log(smallQR);

        // Gera QR code para web
        currentQR = await qrcode.toDataURL(qr);
        connectionStatus = "awaiting_scan";
        log("🔄 Novo QR code gerado");
      }

      if (connection === "close") {
        connectionStatus = "disconnected";
        log("❌ Conexão fechada");
        connectToWhatsApp(); // Reconecta imediatamente
      } else if (connection === "open") {
        connectionStatus = "connected";
        log("🟢 Conectado com sucesso!");
        currentQR = "";
      }
    });

    sock.ev.on("creds.update", saveCreds);

    // Listener de mensagens
    sock.ev.on("messages.upsert", async ({ messages }) => {
      try {
        for (const message of messages) {
          if (message.key.fromMe) continue;

          const from = message.key.remoteJid?.replace("@s.whatsapp.net", "");
          const text =
            message.message?.conversation ||
            message.message?.extendedTextMessage?.text ||
            "";

          log(`📩 Mensagem recebida de ${from}: ${text}`);

          if (text && from) {
            try {
              const response = await fetch(
                "https://finbot-api.onrender.com/whatsapp/webhook",
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    message: { from, text },
                  }),
                  timeout: 30000,
                }
              );

              if (!response.ok) {
                throw new Error(
                  `FastAPI respondeu com status ${response.status}`
                );
              }

              log("✅ Mensagem processada pelo FastAPI");
            } catch (error) {
              log("❌ Erro ao enviar para FastAPI:", error, "error");
            }
          }
        }
      } catch (error) {
        log("❌ Erro ao processar mensagem:", error, "error");
      }
    });
  } catch (err) {
    log(`Erro ao conectar: ${err.message}`, "error");
    setTimeout(connectToWhatsApp, 3000);
  }
}

// Endpoint para enviar mensagens com timeout
app.post("/send-message", async (req, res) => {
  try {
    if (!sock || connectionStatus !== "connected") {
      return res.status(400).json({
        status: "error",
        message: "WhatsApp não está conectado",
      });
    }

    const { to, message } = req.body;
    log(`📤 Enviando mensagem para ${to}: ${message}`);

    // Adiciona timeout na requisição
    const timeout = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Timeout")), 30000)
    );

    const sendMessage = sock.sendMessage(to + "@s.whatsapp.net", {
      text: message,
    });

    await Promise.race([sendMessage, timeout]);
    log(`✅ Mensagem enviada para ${to}`);

    res.json({ status: "success", message: "Mensagem enviada" });
  } catch (error) {
    log("❌ Erro ao enviar mensagem:", error, "error");
    res.status(500).json({ status: "error", message: error.message });
  }
});

// Rota admin (página inicial)
app.get("/", (req, res) => {
  res.send(`
    <html>
      <head>
        <title>FinBot Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
          }
          .status {
            padding: 10px;
            margin: 20px 0;
            border-radius: 5px;
          }
          .connected { background: #d4edda; color: #155724; }
          .disconnected { background: #f8d7da; color: #721c24; }
          .awaiting_scan { background: #fff3cd; color: #856404; }
          .steps {
            text-align: left;
            max-width: 500px;
            margin: 30px auto;
          }
          button {
            padding: 10px 20px;
            margin: 10px;
            border-radius: 5px;
            border: none;
            background: #007bff;
            color: white;
            cursor: pointer;
          }
          button:hover {
            background: #0056b3;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🔧 FinBot Admin</h1>
          
          <div class="status ${connectionStatus}">
            Status: ${connectionStatus.toUpperCase()}
          </div>
          
          ${
            connectionStatus === "connected"
              ? "<p>✅ Bot conectado e pronto para usar!</p>"
              : '<p>Escaneie o QR Code para conectar:</p><a href="/qr"><button>Ver QR Code</button></a>'
          }
        </div>
      </body>
    </html>
  `);
});

// Rota para usuários
app.get("/whatsapp/qr", async (req, res) => {
  // Gera QR code para o número do WhatsApp
  const phoneNumber = "5511965905750"; // Substitua pelo número real
  const whatsappUrl = `https://wa.me/${phoneNumber}?text=oi`;

  // Gera o QR code
  const whatsappQR = await qrcode.toDataURL(whatsappUrl);

  res.send(`
    <html>
      <head>
        <title>FinBot - Seu Assistente Financeiro</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
          }
          .steps {
            text-align: left;
            max-width: 500px;
            margin: 30px auto;
          }
          .commands {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
          }
          .highlight {
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 5px;
            font-family: monospace;
          }
          .qr-container {
            margin: 30px 0;
            padding: 20px;
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          }
          .qr-code {
            max-width: 200px;
            margin: 20px auto;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🤖 FinBot - Seu Assistente Financeiro</h1>
          
          <div class="qr-container">
            <h2>📱 Conecte-se ao FinBot</h2>
            <p>Escaneie o QR code abaixo ou clique nele para abrir o WhatsApp:</p>
            <a href="${whatsappUrl}" target="_blank">
              <img src="${whatsappQR}" alt="WhatsApp QR Code" class="qr-code"/>
            </a>
          </div>

          <div class="steps">
            <h2>Como começar:</h2>
            <ol>
              <li>Escaneie o QR code acima ou salve o contato: <span class="highlight">+${phoneNumber}</span></li>
              <li>Envie uma mensagem com <span class="highlight">/ajuda</span></li>
            </ol>

            <div class="commands">
              <h3>📝 Comandos principais:</h3>
              <ul>
                <li><span class="highlight">/saldo</span> - Ver saldo atual</li>
                <li><span class="highlight">/receita 1000 Salário #salario</span> - Registrar receita</li>
                <li><span class="highlight">/despesa 50 Almoço #alimentacao</span> - Registrar despesa</li>
                <li><span class="highlight">/extrato</span> - Ver últimas transações</li>
                <li><span class="highlight">/categorias</span> - Ver resumo por categoria</li>
              </ul>
            </div>

            <h3>💡 Dicas:</h3>
            <ul>
              <li>Use # para categorizar suas transações</li>
              <li>Exemplo: /despesa 30 Uber #transporte</li>
              <li>A categoria é opcional</li>
            </ul>
          </div>
        </div>
      </body>
    </html>
  `);
});

// Rota para o QR code (mais simples)
app.get("/qr", (req, res) => {
  res.send(`
    <html>
      <head>
        <title>WhatsApp QR Code</title>
        <meta http-equiv="refresh" content="5">
        <style>
          body { font-family: Arial; text-align: center; padding: 20px; }
          img { max-width: 300px; }
        </style>
      </head>
      <body>
        <h2>WhatsApp QR Code</h2>
        ${
          currentQR
            ? `<img src="${currentQR}" alt="QR Code"/>`
            : "<p>Gerando QR code...</p>"
        }
        <p><small>Atualizando em 5 segundos...</small></p>
      </body>
    </html>
  `);
});

// Rota de status com timeout
app.get("/status", (req, res) => {
  res.json({
    status: connectionStatus,
    connected: connectionStatus === "connected",
    timestamp: new Date().toISOString(),
  });
});

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`\n🚀 Servidor Baileys rodando na porta ${PORT}`);
  console.log("\n📱 Iniciando conexão com WhatsApp...\n");
  connectToWhatsApp();
});
