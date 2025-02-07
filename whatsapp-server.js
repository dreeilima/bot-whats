const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const express = require("express");
const qrcode = require("qrcode");
const app = express();
app.use(express.json());

// Porta para a API
const PORT = process.env.PORT || 3001;

// Status da conexão
let connectionStatus = "disconnected";
let currentQR = "";
let sock = null; // Guarda a conexão

async function connectToWhatsApp() {
  try {
    const { state, saveCreds } = await useMultiFileAuthState("auth_info");
    sock = makeWASocket({
      auth: state,
      printQRInTerminal: true,
      defaultQueryTimeoutMs: 30000, // 30 segundos timeout
      connectTimeoutMs: 30000,
      keepAliveIntervalMs: 15000,
      retryRequestDelayMs: 5000,
    });

    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        currentQR = await qrcode.toDataURL(qr);
        connectionStatus = "awaiting_scan";
        console.log("🔄 Novo QR code gerado - Aguardando scan...");
      }

      if (connection === "close") {
        connectionStatus = "disconnected";
        console.log("❌ Conexão fechada");

        const shouldReconnect =
          (lastDisconnect?.error instanceof Boom)?.output?.statusCode !==
          DisconnectReason.loggedOut;

        if (shouldReconnect) {
          console.log("🔄 Reconectando...");
          setTimeout(connectToWhatsApp, 5000); // Tenta reconectar após 5s
        }
      } else if (connection === "open") {
        connectionStatus = "connected";
        console.log("🟢 Conectado com sucesso ao WhatsApp!");
        currentQR = "";
      }
    });

    sock.ev.on("creds.update", saveCreds);
  } catch (err) {
    console.error("Erro ao conectar:", err);
    setTimeout(connectToWhatsApp, 5000); // Tenta reconectar após 5s
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

// Rota inicial com status
app.get("/", (req, res) => {
  res.send(`
    <html>
      <head>
        <title>WhatsApp Bot</title>
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
          <h1>WhatsApp Bot</h1>
          
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
