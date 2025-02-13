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
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configura Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Instala dependências
COPY package*.json ./
RUN npm install --production --force

# Copia código
COPY . .

EXPOSE 3001

CMD ["npm", "start"]
