# Use uma imagem oficial do Python como imagem mãe
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos do projeto
COPY requirements.txt .
COPY app/ ./app/
COPY setup.py .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta na qual o aplicativo é executado
EXPOSE 8000

# Define a variável de ambiente
ENV NAME PixzinhoBot

# Executa app.py quando o container é iniciado
CMD ["python", "setup.py"]
