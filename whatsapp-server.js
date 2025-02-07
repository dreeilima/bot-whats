const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const express = require("express");
const qrcode = require("qrcode-terminal");
const app = express();
app.use(express.json());

// Porta para a API
const PORT = process.env.PORT || 3001;

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
      // Gera QR code no terminal
      console.log("\n\nPOR FAVOR ESCANEIE O QR CODE ABAIXO NO SEU WHATSAPP:\n");
      qrcode.generate(qr, { small: true });
      console.log("\nAguardando scan...\n");
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

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`\n🚀 Servidor rodando na porta ${PORT}`);
  console.log("\nIniciando conexão com WhatsApp...\n");
  connectToWhatsApp();
});
