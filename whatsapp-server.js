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

// Rota admin para conectar o bot
app.get("/", (req, res) => {
  res.send(`
    <html>
      <head>
        <title>FinBot Admin</title>
        <style>
          body { font-family: Arial; text-align: center; padding: 20px; }
          .status { padding: 10px; margin: 20px 0; border-radius: 5px; }
          .connected { background: #d4edda; color: #155724; }
          .disconnected { background: #f8d7da; color: #721c24; }
        </style>
      </head>
      <body>
        <h1>🔧 FinBot Admin</h1>
        
        <div class="status ${clientReady ? "connected" : "disconnected"}">
          Status: ${clientReady ? "CONECTADO" : "DESCONECTADO"}
        </div>

        ${
          clientReady
            ? `<p>✅ Bot está online!</p>
               <p>Compartilhe o link: <br>
               <code>https://bot-whats-9onh.onrender.com/whatsapp/qr</code></p>`
            : `<p>Escaneie o QR Code para conectar:</p>
               <img src="${currentQR}" alt="QR Code" style="max-width: 300px"/>`
        }
      </body>
    </html>
  `);
});

// Rota para usuários
app.get("/whatsapp/qr", (req, res) => {
  if (!clientReady) {
    return res.send(`
      <html>
        <head>
          <title>FinBot Indisponível</title>
          <meta http-equiv="refresh" content="30">
          <style>
            body { font-family: Arial; text-align: center; padding: 20px; }
          </style>
        </head>
        <body>
          <h2>⚠️ Bot Offline</h2>
          <p>O FinBot está temporariamente indisponível.<br>
          Tente novamente em alguns minutos.</p>
        </body>
      </html>
    `);
  }

  // Gera QR code para o número do WhatsApp
  const phoneNumber = "5511965905750"; // Seu número
  const whatsappUrl = `https://wa.me/${phoneNumber}?text=oi`;

  qrcode.toDataURL(whatsappUrl, (err, qrImage) => {
    if (err) {
      return res.status(500).send("Erro ao gerar QR code");
    }

    res.send(`
      <html>
        <head>
          <title>FinBot - Seu Assistente Financeiro</title>
          <style>
            body { font-family: Arial; text-align: center; padding: 20px; }
            .qr-container { margin: 30px 0; }
            .qr-code { max-width: 300px; }
            .commands { text-align: left; max-width: 500px; margin: 30px auto; }
          </style>
        </head>
        <body>
          <h1>🤖 FinBot - Seu Assistente Financeiro</h1>
          
          <div class="qr-container">
            <h2>📱 Conecte-se ao FinBot</h2>
            <p>Escaneie o QR code ou clique nele para abrir o WhatsApp:</p>
            <a href="${whatsappUrl}" target="_blank">
              <img src="${qrImage}" alt="WhatsApp QR Code" class="qr-code"/>
            </a>
          </div>

          <div class="commands">
            <h3>📝 Comandos disponíveis:</h3>
            <ul>
              <li><code>/saldo</code> - Ver saldo atual</li>
              <li><code>/receita 1000 Salário #salario</code></li>
              <li><code>/despesa 50 Almoço #alimentacao</code></li>
              <li><code>/extrato</code> - Ver últimas transações</li>
            </ul>
          </div>
        </body>
      </html>
    `);
  });
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
