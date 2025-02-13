FROM node:20-slim

# Instala dependências necessárias
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configura Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Instala dependências
COPY package*.json ./
RUN npm install --omit=dev

# Copia código
COPY . .

EXPOSE 3001

CMD ["npm", "start"]
