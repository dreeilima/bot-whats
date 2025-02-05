# Use uma imagem oficial do Python como imagem mãe
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema incluindo SSL
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
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
