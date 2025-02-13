const express = require("express");
const { create } = require("venom-bot");
const qrcode = require("qrcode");
const axios = require("axios");
const fs = require("fs");
const path = require("path");
const { Pool } = require("pg");
const cors = require("cors");

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 3001; // Usa a porta do ambiente ou 3001 como fallback
let currentQR = null;
let clientReady = false;
let client = null;

// Configurações de sessão mais robustas
const SESSION_DIR =
  process.env.NODE_ENV === "production"
    ? "/app/sessions" // Diretório persistente no Render
    : "./sessions"; // Local para desenvolvimento

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

// Ajuste na conexão com o banco
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false, // Permite certificados self-signed
  },
});

// No início do arquivo
const authenticatedUsers = new Set();

// Função para verificar autenticação
function isAuthenticated(userId) {
  return authenticatedUsers.has(userId);
}

// Função para autenticar usuário
function authenticateUser(userId) {
  authenticatedUsers.add(userId);
}

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
        const response = await processMessage(message.body, message.from);

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
async function processMessage(text, from) {
  const userId = from.replace("@c.us", "");

  try {
    // Verifica se usuário existe
    const userResult = await pool.query(
      "SELECT * FROM users WHERE phone = $1",
      [userId]
    );

    // Se não existir, cria
    if (userResult.rows.length === 0) {
      await pool.query(
        "INSERT INTO users (phone, created_at) VALUES ($1, NOW())",
        [userId]
      );
    }

    const command = text.toLowerCase().trim();

    // Comandos básicos
    if (command === "oi" || command === "olá" || command === "ola") {
      return formatMenuInicial();
    }

    if (command === "/ajuda") {
      return formatMenuInicial();
    }

    // Comando de saldo
    if (command === "/saldo") {
      const result = await pool.query(
        `SELECT COALESCE(SUM(CASE WHEN type = 'receita' THEN amount ELSE -amount END), 0) as saldo 
         FROM transactions WHERE user_id = $1`,
        [userId]
      );
      return formatSaldo(result.rows[0].saldo);
    }

    // Comando de extrato
    if (command === "/extrato") {
      const result = await pool.query(
        `SELECT type, amount, description, category, created_at as data
         FROM transactions 
         WHERE user_id = $1 
         ORDER BY created_at DESC 
         LIMIT 5`,
        [userId]
      );
      return formatExtrato(result.rows);
    }

    // Comando de receita
    if (command.startsWith("/receita")) {
      const match = command.match(/\/receita (\d+\.?\d*) ([^#]+)(#\w+)?/);
      if (!match) {
        return "❌ Formato inválido. Use: /receita [valor] [descrição] #categoria";
      }

      const valor = parseFloat(match[1]);
      const descricao = match[2].trim();
      const categoria = (match[3] || "#geral").substring(1);

      await pool.query(
        "INSERT INTO transactions (user_id, type, amount, description, category) VALUES ($1, $2, $3, $4, $5)",
        [userId, "receita", valor, descricao, categoria]
      );

      return `✅ Receita registrada!\n💰 Valor: ${formatMoney(
        valor
      )}\n📝 Descrição: ${descricao}\n🏷️ Categoria: ${categoria}`;
    }

    // Comando de despesa
    if (command.startsWith("/despesa")) {
      const match = command.match(/\/despesa (\d+\.?\d*) ([^#]+)(#\w+)?/);
      if (!match) {
        return "❌ Formato inválido. Use: /despesa [valor] [descrição] #categoria";
      }

      const valor = parseFloat(match[1]);
      const descricao = match[2].trim();
      const categoria = (match[3] || "#geral").substring(1);

      // Verifica orçamento
      const orcResult = await pool.query(
        "SELECT valor FROM orcamentos WHERE user_id = $1 AND categoria = $2",
        [userId, categoria]
      );

      if (orcResult.rows.length > 0) {
        const limite = orcResult.rows[0].valor;
        const gastosResult = await pool.query(
          `SELECT SUM(amount) as total 
           FROM transactions 
           WHERE user_id = $1 
           AND category = $2 
           AND type = 'despesa' 
           AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)`,
          [userId, categoria]
        );

        const gastosMes = (gastosResult.rows[0].total || 0) + valor;
        if (gastosMes > limite) {
          return `⚠️ Atenção! Esta despesa ultrapassará seu limite de ${formatMoney(
            limite
          )} para #${categoria} este mês.`;
        }
      }

      await pool.query(
        "INSERT INTO transactions (user_id, type, amount, description, category) VALUES ($1, $2, $3, $4, $5)",
        [userId, "despesa", valor, descricao, categoria]
      );

      return `✅ Despesa registrada!\n💸 Valor: ${formatMoney(
        valor
      )}\n📝 Descrição: ${descricao}\n🏷️ Categoria: ${categoria}`;
    }

    // Comando de categorias
    if (command === "/categorias") {
      const result = await pool.query(
        "SELECT DISTINCT category FROM transactions WHERE user_id = $1",
        [userId]
      );
      const categorias = new Set(result.rows.map((r) => r.category));
      return formatCategorias(categorias);
    }

    // Comando de relatório
    if (command.startsWith("/relatorio")) {
      const tipo = command.split(" ")[1] || "diario";
      const periodoQuery = {
        diario:
          "DATE_TRUNC('day', created_at) = DATE_TRUNC('day', CURRENT_DATE)",
        semanal:
          "DATE_TRUNC('week', created_at) = DATE_TRUNC('week', CURRENT_DATE)",
        mensal:
          "DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)",
      }[tipo];

      const result = await pool.query(
        `SELECT 
           COALESCE(SUM(CASE WHEN type = 'receita' THEN amount END), 0) as receitas,
           COALESCE(SUM(CASE WHEN type = 'despesa' THEN amount END), 0) as despesas,
           COALESCE(SUM(CASE WHEN type = 'receita' THEN amount ELSE -amount END), 0) as saldo
         FROM transactions 
         WHERE user_id = $1 AND ${periodoQuery}`,
        [userId]
      );

      return formatRelatorio(tipo, result.rows[0]);
    }

    // Se não reconhecer o comando
    return "❓ Comando não reconhecido. Digite /ajuda para ver as opções disponíveis.";
  } catch (error) {
    console.error("❌ Erro no banco:", error);
    return "Desculpe, ocorreu um erro ao processar sua solicitação.";
  }
}

// Função para formatar moeda
function formatMoney(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

// Função para formatar data
function formatDate(date) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

// Função para formatar extrato
function formatExtrato(transacoes) {
  if (transacoes.length === 0) {
    return "📊 *Extrato*\n\n❌ Nenhuma transação encontrada.";
  }

  const header =
    "📊 *Extrato das Últimas Transações*\n" + "━━━━━━━━━━━━━━━━━━━━━\n\n";

  const items = transacoes
    .map((t) => {
      const emoji = t.valor > 0 ? "📈" : "📉";
      const valor = formatMoney(Math.abs(t.valor));
      return (
        `${emoji} *${t.descricao}*\n` +
        ` Valor: ${valor}\n` +
        `🏷️ Categoria: #${t.categoria}\n` +
        `📅 Data: ${formatDate(t.data)}\n` +
        "━━━━━━━━━━━━━━━━━━━━━"
      );
    })
    .join("\n\n");

  return header + items;
}

// Função para formatar saldo
function formatSaldo(saldo) {
  const emoji = saldo >= 0 ? "📈" : "📉";
  return (
    `${emoji} *Saldo Atual*\n\n` +
    `💰 ${formatMoney(saldo)}\n\n` +
    `_Use /extrato para ver suas últimas transações_`
  );
}

// Função para formatar categorias
function formatCategorias(categorias) {
  if (categorias.size === 0) {
    return "📋 *Categorias*\n\n❌ Nenhuma categoria registrada.";
  }

  return (
    "📋 *Suas Categorias*\n" +
    "━━━━━━━━━━━━━━━━━━━━━\n\n" +
    Array.from(categorias)
      .map((c) => `🏷️ #${c}`)
      .join("\n") +
    "\n\n_Use uma categoria ao registrar transações_"
  );
}

// Função para formatar menu inicial
function formatMenuInicial() {
  return (
    `🤖 *FinBot - Seu Assistente Financeiro*\n\n` +
    `*Comandos Básicos:*\n` +
    `━━━━━━━━━━━━━━━━━━━━━\n` +
    `💰 */saldo* - Ver saldo atual\n` +
    `📝 */receita* [valor] [descrição] #categoria\n` +
    `💸 */despesa* [valor] [descrição] #categoria\n` +
    `📊 */extrato* - Ver últimas transações\n\n` +
    `*Gestão Financeira:*\n` +
    `━━━━━━━━━━━━━━━━━━━━━\n` +
    `🎯 */meta* [valor] [descrição] - Definir meta\n` +
    `⏰ */lembrete* [data] [descrição] - Criar lembrete\n` +
    `📅 */recorrente* [tipo] [valor] [descrição] - Pagamento recorrente\n` +
    `💹 */orcamento* [categoria] [valor] - Definir orçamento\n\n` +
    `*Análises:*\n` +
    `━━━━━━━━━━━━━━━━━━━━━\n` +
    `📈 */relatorio* [diario|semanal|mensal]\n` +
    `📊 */categorias* - Ver categorias\n` +
    `❓ */ajuda* - Ver todos os comandos`
  );
}

// Função para formatar relatório
function formatRelatorio(tipo, dados) {
  const hoje = new Date();
  const periodos = {
    diario: "Diário",
    semanal: "Semanal",
    mensal: "Mensal",
  };

  return (
    `📊 *Relatório ${periodos[tipo]}*\n` +
    `📅 ${formatDate(hoje)}\n` +
    `━━━━━━━━━━━━━━━━━━━━━\n\n` +
    `📈 Receitas: ${formatMoney(dados.receitas)}\n` +
    `📉 Despesas: ${formatMoney(dados.despesas)}\n` +
    `━━━━━━━━━━━━━━━━━━━━━\n` +
    `💰 Saldo: ${formatMoney(dados.saldo)}`
  );
}

// Configurações do Venom
const venomOptions = {
  session: "finbot-session",
  headless: true,
  useChrome: false,
  createPathFileToken: true,
  folderNameToken: SESSION_DIR,
  disableWelcome: true,
  autoClose: false,
  // Aumenta tempo de espera da sessão
  waitForLogin: true,
  sessionToken: {
    WABrowserId: process.env.WA_BROWSER_ID,
    WASecretBundle: process.env.WA_SECRET_BUNDLE,
    WAToken1: process.env.WA_TOKEN1,
    WAToken2: process.env.WA_TOKEN2,
  },
  catchQR: (base64Qr, asciiQR) => {
    console.log("\n\n==== QR CODE ====\n");
    console.log(asciiQR);
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

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`🚀 Servidor WhatsApp rodando na porta ${PORT}`);
  console.log("⏳ Iniciando cliente WhatsApp...");
  initializeWhatsApp();
});

// Adiciona rota de status
app.get("/status", (req, res) => {
  res.json({
    status: "online",
    whatsapp: clientReady ? "connected" : "disconnected",
  });
});

// Melhora rota do QR code
app.get(["/qr", "/whatsapp/qr"], (req, res) => {
  if (clientReady) {
    return res.json({
      status: "success",
      connected: true,
      message: "WhatsApp já está conectado",
    });
  }

  if (currentQR) {
    return res.json({
      status: "success",
      connected: false,
      qr: currentQR,
    });
  }

  return res.json({
    status: "error",
    message: "QR Code ainda não disponível",
  });
});

// Tratamento de erros
process.on("unhandledRejection", (error) => {
  console.error("🔥 Erro não tratado:", error);
});

process.on("uncaughtException", (error) => {
  console.error("🔥 Exceção não capturada:", error);
});
