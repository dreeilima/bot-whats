# Bot WhatsApp - Gestão Financeira

Bot de WhatsApp para gestão financeira pessoal integrado com PIX.

## Funcionalidades

- 💰 Gestão de contas e transações
- 📊 Categorização de despesas
- 🎯 Metas financeiras
- ⏰ Lembretes de contas
- 📈 Relatórios financeiros
- 💸 Integração com PIX

## Tecnologias

- Python 3.11
- FastAPI
- SQLModel
- Docker
- Railway Deploy

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/dreeilima/bot-whats.git
cd bot-whats
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure o arquivo .env:

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Execute o bot:

```bash
python setup.py
```

## Comandos WhatsApp

📱 **Comandos Disponíveis:**

💰 **Gestão Financeira:**

- `/saldo` - Ver saldo de todas as contas
- `/conta [nome]` - Informações da conta
- `/extrato` - Ver extrato dos últimos 7 dias
- `/relatorio` - Relatório financeiro completo

💸 **Transações:**

- `/despesa valor descrição` - Registrar despesa
- `/receita valor descrição` - Registrar receita
- `/categoria listar` - Ver categorias

📋 **Contas e Metas:**

- `/contas` - Ver contas pendentes
- `/meta criar nome valor data` - Criar meta
- `/meta listar` - Ver metas

⏰ **Lembretes:**

- `/lembrete contas` - Lembrar contas
- `/lembrete meta nome` - Lembrar meta
- `/lembrete saldo` - Lembrar saldo

## Deploy

```bash
# Usando Docker
docker-compose up -d

# Usando Railway
railway up
```

## Licença

MIT
