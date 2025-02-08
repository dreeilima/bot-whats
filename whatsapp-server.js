const express = require("express");
const venom = require("venom-bot");
const qrcode = require("qrcode");
const fetch = require("node-fetch");

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3001;
let currentQR = null;
let clientReady = false;

// Ajuste a URL do webhook baseado no ambiente
const webhookUrl = process.env.NODE_ENV === 'production'
  ? 'https://finbot-api-9onh.onrender.com/webhook'  // URL de produção
  : 'http://localhost:8000/webhook';  // URL local

// Função para iniciar o cliente
function start(client) {
  clientReady = true;
  console.log("🟢 Bot conectado!");

  // Listener de mensagens
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

      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(payload),
      });

      console.log("📥 Status do webhook:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Detalhes do erro:', errorText);
        throw new Error(`Webhook respondeu com status ${response.status}`);
      }

      const data = await response.json();
      console.log("📥 Resposta do webhook:", data);

      if (data.message) {
        await client.sendText(message.from, data.message);
        console.log("✅ Resposta enviada:", data.message);
      }

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
    headless: "new",
    debug: false,
    logQR: true,
    disableWelcome: true,
    catchQR: (base64Qr, asciiQR, attempts) => {
      // Armazena o QR code diretamente em base64
      currentQR = base64Qr;
      console.log('QR Code gerado:', attempts, 'tentativa');
      // Opcional: mostra QR no terminal
      console.log(asciiQR);
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
        </style>
      </head>
      <body>
        <h1>🤖 FinBot Admin</h1>
        
        <div class="qr-container">
          ${
            clientReady
              ? `<h2>✅ Bot Conectado!</h2>`
              : currentQR
                ? `<h2>📱 Escaneie o QR Code</h2>
                   <img src="${currentQR}" alt="QR Code" />`
                : `<h2>⏳ Gerando QR Code...</h2>
                   <p>Aguarde um momento...</p>`
          }
        </div>
      </body>
    </html>
  `);
});

// Rota para usuários
app.get("/whatsapp/qr", (req, res) => {
  // Gera QR code para o número do WhatsApp
  const phoneNumber = "5511965905750"; // Adiciona o código do país
  const whatsappUrl = `https://wa.me/${phoneNumber}?text=oi`;

  qrcode.toDataURL(whatsappUrl, (err, qrImage) => {
    if (err) {
      return res.status(500).send("Erro ao gerar QR code");
    }

    res.send(`
      <html>
        <head>
          <title>FinBot - Seu Assistente Financeiro</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { 
              font-family: Arial, sans-serif; 
              text-align: center; 
              padding: 20px;
              background: #f5f5f5;
              line-height: 1.6;
            }
            .container {
              max-width: 600px;
              margin: 0 auto;
            }
            .qr-container {
              background: white;
              padding: 30px;
              border-radius: 15px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              margin: 20px 0;
            }
            .commands {
              background: white;
              padding: 30px;
              border-radius: 15px;
              text-align: left;
              margin: 20px 0;
            }
            img {
              max-width: 300px;
              height: auto;
              margin: 20px 0;
            }
            .button {
              display: inline-block;
              background: #25D366;
              color: white;
              padding: 12px 30px;
              border-radius: 25px;
              text-decoration: none;
              font-weight: bold;
              margin: 10px 0;
              transition: all 0.3s ease;
            }
            .button:hover {
              background: #128C7E;
              transform: translateY(-2px);
            }
            code {
              background: #f8f9fa;
              padding: 3px 6px;
              border-radius: 4px;
              font-size: 0.9em;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🤖 FinBot</h1>
            <p>Seu assistente financeiro pessoal</p>

            <div class="qr-container">
              <h2>📱 Conecte-se ao FinBot</h2>
              <p>Escaneie o QR code ou clique no botão abaixo:</p>
              
              <img src="${qrImage}" alt="QR Code para WhatsApp"/>
              
              <a href="${whatsappUrl}" class="button" target="_blank">
                Iniciar Conversa ↗
              </a>
            </div>

            <div class="commands">
              <h2>📝 Comandos Disponíveis</h2>
              <ul>
                <li><code>/ajuda</code> - Lista todos os comandos</li>
                <li><code>/saldo</code> - Ver saldo atual</li>
                <li><code>/despesa 50 Almoço #alimentacao</code></li>
                <li><code>/receita 1000 Salário #salario</code></li>
                <li><code>/extrato</code> - Ver últimas transações</li>
              </ul>
            </div>
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
  console.log(`🚀 Servidor rodando na porta ${PORT}`);
});
