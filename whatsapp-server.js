const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const express = require("express");
const qrcode = require("qrcode");
const fetch = require("node-fetch");
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

async function connectToWhatsApp() {
  try {
    console.log("Iniciando conexão...");
    const { state, saveCreds } = await useMultiFileAuthState("auth_info");

    sock = makeWASocket({
      auth: state,
      printQRInTerminal: true,
      defaultQueryTimeoutMs: 60000, // 60 segundos
      connectTimeoutMs: 60000,
      keepAliveIntervalMs: 25000,
      retryRequestDelayMs: 2000,
      browser: ["Chrome (Linux)", "Chrome", "104"],
      version: [2, 2323, 4],
      fireAndForget: true,
    });

    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;
      console.log("Status da conexão:", connection);

      if (qr) {
        currentQR = await qrcode.toDataURL(qr);
        connectionStatus = "awaiting_scan";
        console.log("🔄 Novo QR code gerado - Aguardando scan...");
        reconnectAttempts = 0; // Reset contador ao gerar novo QR
      }

      if (connection === "close") {
        connectionStatus = "disconnected";
        console.log("❌ Conexão fechada");

        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        if (shouldReconnect && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts++;
          console.log(
            `🔄 Tentativa de reconexão ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`
          );
          setTimeout(connectToWhatsApp, 5000 * reconnectAttempts);
        } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          console.log("❌ Máximo de tentativas de reconexão atingido");
          process.exit(1); // Força restart do serviço
        }
      } else if (connection === "open") {
        connectionStatus = "connected";
        console.log("🟢 Conectado com sucesso ao WhatsApp!");
        currentQR = "";
        reconnectAttempts = 0;
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

          console.log(`📩 Mensagem recebida de ${from}: ${text}`);

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

              console.log("✅ Mensagem processada pelo FastAPI");
            } catch (error) {
              console.error("❌ Erro ao enviar para FastAPI:", error);
            }
          }
        }
      } catch (error) {
        console.error("❌ Erro ao processar mensagem:", error);
      }
    });
  } catch (err) {
    console.error("Erro ao conectar:", err);
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++;
      setTimeout(connectToWhatsApp, 5000 * reconnectAttempts);
    }
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
    console.log(`📤 Enviando mensagem para ${to}: ${message}`);

    // Adiciona timeout na requisição
    const timeout = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Timeout")), 30000)
    );

    const sendMessage = sock.sendMessage(to + "@s.whatsapp.net", {
      text: message,
    });

    await Promise.race([sendMessage, timeout]);
    console.log(`✅ Mensagem enviada para ${to}`);

    res.json({ status: "success", message: "Mensagem enviada" });
  } catch (error) {
    console.error("❌ Erro ao enviar mensagem:", error);
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

// Rota para o QR code
app.get("/qr", (req, res) => {
  if (connectionStatus === "connected") {
    return res.redirect("/");
  }

  if (!currentQR) {
    return res.send(
      "QR Code ainda não disponível. Aguarde alguns segundos e tente novamente."
    );
  }

  res.send(`
    <html>
      <head>
        <title>WhatsApp QR Code</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="30">
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
          }
          img {
            max-width: 300px;
            margin: 20px 0;
          }
          .container {
            margin-top: 50px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>WhatsApp QR Code</h1>
          <p>Escaneie o QR Code abaixo no seu WhatsApp:</p>
          <img src="${currentQR}" alt="WhatsApp QR Code"/>
          <p>
            <small>Esta página atualiza automaticamente a cada 30 segundos.<br>
            Se o QR code não aparecer, <a href="/qr">clique aqui</a> para atualizar.</small>
          </p>
        </div>
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
