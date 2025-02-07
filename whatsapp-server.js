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

// Armazena o QR code atual
let currentQR = "";

async function connectToWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState("auth_info");
  const sock = makeWASocket({
    auth: state,
    printQRInTerminal: true,
    defaultQueryTimeoutMs: undefined,
  });

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      // Gera QR code como imagem base64
      currentQR = await qrcode.toDataURL(qr);
      console.log("Novo QR code gerado");
    }

    if (connection === "close") {
      const shouldReconnect =
        (lastDisconnect.error instanceof Boom)?.output?.statusCode !==
        DisconnectReason.loggedOut;
      console.log(
        "Conexão fechada por",
        lastDisconnect.error,
        "Reconectando:",
        shouldReconnect
      );
      if (shouldReconnect) {
        connectToWhatsApp();
      }
    } else if (connection === "open") {
      console.log("\n🟢 Conectado com sucesso ao WhatsApp!\n");
    }
  });

  sock.ev.on("creds.update", saveCreds);

  // Endpoint para enviar mensagens
  app.post("/send-message", async (req, res) => {
    try {
      const { to, message } = req.body;
      console.log(`Enviando mensagem para ${to}: ${message}`);

      await sock.sendMessage(to + "@s.whatsapp.net", { text: message });

      res.json({ status: "success", message: "Mensagem enviada" });
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
      res.status(500).json({ status: "error", message: error.message });
    }
  });
}

// Rota inicial
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
          <h1>WhatsApp Bot</h1>
          <p>Escaneie o QR Code para conectar:</p>
          <a href="/qr"><button>Ver QR Code</button></a>
        </div>
      </body>
    </html>
  `);
});

// Rota para o QR code
app.get("/qr", (req, res) => {
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
            <small>Se o QR code não aparecer, <a href="/qr">clique aqui</a> para atualizar.</small>
          </p>
        </div>
      </body>
    </html>
  `);
});

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`\n🚀 Servidor rodando na porta ${PORT}`);
  console.log("\nIniciando conexão com WhatsApp...\n");
  connectToWhatsApp();
});
