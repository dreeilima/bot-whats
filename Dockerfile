# Use uma imagem oficial do Python como imagem mãe
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o necessário
COPY requirements.txt .
COPY app/ ./app/
COPY setup.py .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta
EXPOSE 10000

# Define variáveis de ambiente
ENV PORT=10000
ENV IP=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Comando para iniciar
CMD ["python", "setup.py"]

FROM node:20-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    chromium \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define variáveis de ambiente
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Cria diretório da aplicação
WORKDIR /app

# Copia arquivos de dependências
COPY package*.json ./

# Instala dependências
RUN npm install --omit=dev

# Copia código fonte
COPY . .

# Expõe porta
EXPOSE 3001

# Inicia aplicação
CMD ["node", "whatsapp-server.js"]
