const express = require("express");
const venom = require("venom-bot");
const qrcode = require("qrcode");
const fetch = require("node-fetch");

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3001;
let currentQR = "";
let clientReady = false;

// Função para iniciar o cliente
function start(client) {
  clientReady = true;
  console.log("🟢 Bot conectado!");

  // Listener de mensagens
  client.onMessage(async (message) => {
    if (message.isGroupMsg) return;

    try {
      // Envia para o webhook local
      const response = await fetch(
        "https://bot-whats-9onh.onrender.com/webhook",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: {
              from: message.from.replace("@c.us", ""),
              text: message.body,
            },
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Webhook respondeu com status ${response.status}`);
      }

      // Se tiver resposta, envia de volta
      const data = await response.json();
      if (data.message) {
        await client.sendText(message.from, data.message);
      }

      console.log("✅ Mensagem processada");
    } catch (error) {
      console.error("❌ Erro ao processar mensagem:", error);
    }
  });

  // Endpoint para enviar mensagens
  app.post("/send-message", async (req, res) => {
    try {
      if (!clientReady) {
        return res.status(400).json({
          status: "error",
          message: "WhatsApp não está conectado",
        });
      }

      const { to, message } = req.body;
      await client.sendText(`${to}@c.us`, message);

      console.log(`✅ Mensagem enviada para ${to}`);
      res.json({ status: "success", message: "Mensagem enviada" });
    } catch (error) {
      console.error("❌ Erro ao enviar mensagem:", error);
      res.status(500).json({ status: "error", message: error.message });
    }
  });
}

// Inicia o venom-bot
venom
  .create({
    session: "finbot",
    multidevice: true,
    headless: true,
    debug: false,
    logQR: false,
    disableWelcome: true,
    catchQR: (qr) => {
      // Gera QR code para web
      qrcode.toDataURL(qr, (err, url) => {
        if (!err) {
          currentQR = url;
          console.log("🔄 Novo QR code gerado");
        }
      });
    },
  })
  .then((client) => start(client))
  .catch((error) => {
    console.error("❌ Erro ao iniciar:", error);
  });

// Rota para o QR code
app.get("/qr", (req, res) => {
  if (clientReady) {
    return res.send(`
      <html>
        <head>
          <title>WhatsApp Status</title>
          <style>
            body { font-family: Arial; text-align: center; padding: 20px; }
          </style>
        </head>
        <body>
          <h2>✅ WhatsApp Conectado!</h2>
        </body>
      </html>
    `);
  }

  if (!currentQR) {
    return res.send(`
      <html>
        <head>
          <title>Aguarde...</title>
          <meta http-equiv="refresh" content="5">
          <style>
            body { font-family: Arial; text-align: center; padding: 20px; }
          </style>
        </head>
        <body>
          <h2>Gerando QR Code...</h2>
          <p>Aguarde um momento...</p>
        </body>
      </html>
    `);
  }

  res.send(`
    <html>
      <head>
        <title>WhatsApp QR Code</title>
        <meta http-equiv="refresh" content="30">
        <style>
          body { font-family: Arial; text-align: center; padding: 20px; }
          img { max-width: 300px; }
        </style>
      </head>
      <body>
        <h2>Escaneie o QR Code</h2>
        <img src="${currentQR}" alt="QR Code"/>
        <p><small>Esta página atualiza automaticamente.</small></p>
      </body>
    </html>
  `);
});

// Rota do webhook
app.post("/webhook", async (req, res) => {
  try {
    const { message } = req.body;
    console.log("📩 Mensagem recebida:", message);

    // Aqui você pode processar a mensagem
    // Por exemplo, se for /saldo, retorna o saldo
    let response = "";

    if (message.text.startsWith("/")) {
      const command = message.text.toLowerCase();

      if (command === "/saldo") {
        response = "Seu saldo atual é R$ 1.000,00";
      } else if (command === "/ajuda") {
        response = `Comandos disponíveis:
/saldo - Ver saldo atual
/receita valor descrição #categoria
/despesa valor descrição #categoria
/extrato - Ver últimas transações`;
      }
    }

    // Retorna a resposta
    res.json({
      message: response,
      status: "success",
    });
  } catch (error) {
    console.error("❌ Erro no webhook:", error);
    res.status(500).json({
      status: "error",
      message: error.message,
    });
  }
});

// Status da API
app.get("/status", (req, res) => {
  res.json({
    status: clientReady ? "connected" : "disconnected",
    connected: clientReady,
  });
});

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`\n🚀 Servidor rodando na porta ${PORT}`);
});
