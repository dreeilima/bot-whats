FROM node:20-slim

# Instala dependências necessárias
RUN apt-get update && apt-get install -y \
    chromium \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configura Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Copia package.json e package-lock.json
COPY package*.json ./

# Instala todas as dependências (incluindo pg)
RUN npm install

# Copia o resto do código
COPY . .

EXPOSE 3001

CMD ["npm", "start"]
