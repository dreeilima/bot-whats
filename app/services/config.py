from decouple import config
import termcolor
import os


# Caminho do arquivo .env
ENV_PATH = ".env"

# Verifica se o arquivo .env existe
if not os.path.exists(ENV_PATH):
    with open(ENV_PATH, "w") as env_file:
        # Escreve as variáveis padrões no arquivo
        env_file.write("IP=127.0.0.1\n")
        env_file.write("PORT=8000\n")
        env_file.write("DATABASE_URL=sqlite:///./test.db\n")
        env_file.write("JWT_SECRET_KEY=sua_chave_secreta_aqui\n")
        env_file.write("ACCESS_TOKEN_EXPIRE_MINUTES=30\n")
        env_file.write("WHATSAPP_NUMBER=5511953238980\n")
        env_file.write("FORCE_DB_INIT=false\n")
    print(termcolor.colored(
        ".env criado com valores padrão. Por favor, revise e ajuste conforme necessário.",
        color="red",
        attrs=["bold"]
        )
    )

# Carrega as variáveis com valores padrão caso não existam
IP = config("IP", default="127.0.0.1")
PORT = int(config("PORT", default="8000"))
DATABASE_URL = config("DATABASE_URL", default="sqlite:///./test.db")
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default="sua_chave_secreta_aqui")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default="30"))
WHATSAPP_NUMBER = config("WHATSAPP_NUMBER", default="5511953238980")
FORCE_DB_INIT = config("FORCE_DB_INIT", default=False, cast=bool)
