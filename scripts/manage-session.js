const fs = require("fs");
const path = require("path");

const SESSION_DIR = path.join(__dirname, "..", "sessions");

// Garante que o diretório existe
if (!fs.existsSync(SESSION_DIR)) {
  fs.mkdirSync(SESSION_DIR, { recursive: true });
}

function backupSession() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const backupDir = path.join(SESSION_DIR, "backups", timestamp);

  if (fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(backupDir, { recursive: true });
    fs.readdirSync(SESSION_DIR).forEach((file) => {
      if (file !== "backups") {
        fs.copyFileSync(
          path.join(SESSION_DIR, file),
          path.join(backupDir, file)
        );
      }
    });
    console.log(`✅ Backup criado em: ${backupDir}`);
  }
}

function restoreSession(timestamp) {
  const backupDir = path.join(SESSION_DIR, "backups", timestamp);
  if (fs.existsSync(backupDir)) {
    fs.readdirSync(backupDir).forEach((file) => {
      fs.copyFileSync(path.join(backupDir, file), path.join(SESSION_DIR, file));
    });
    console.log("✅ Sessão restaurada com sucesso!");
  } else {
    console.error("❌ Backup não encontrado!");
  }
}

function listBackups() {
  const backupsDir = path.join(SESSION_DIR, "backups");
  if (fs.existsSync(backupsDir)) {
    const backups = fs.readdirSync(backupsDir);
    console.log("📂 Backups disponíveis:");
    backups.forEach((backup) => console.log(`- ${backup}`));
  } else {
    console.log("❌ Nenhum backup encontrado");
  }
}

// Processa argumentos da linha de comando
const [, , command, arg] = process.argv;

switch (command) {
  case "backup":
    backupSession();
    break;
  case "restore":
    if (!arg) {
      console.error("❌ Especifique o timestamp do backup!");
      process.exit(1);
    }
    restoreSession(arg);
    break;
  case "list":
    listBackups();
    break;
  default:
    console.log(`
📱 Gerenciador de Sessão do WhatsApp

Comandos:
- node manage-session.js backup   : Cria backup da sessão atual
- node manage-session.js restore [timestamp] : Restaura backup específico
- node manage-session.js list    : Lista backups disponíveis
        `);
}
