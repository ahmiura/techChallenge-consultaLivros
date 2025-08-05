# Estágio 1: Builder - Instala dependências de sistema e Python
FROM python:3.11-slim-bookworm AS builder

# Diretório de trabalho
WORKDIR /app


# Instala o Google Chrome e outras dependências de sistema
# Todos esses comandos rodam em um ambiente com permissão de escrita
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências e instala os pacotes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 2: Runner - A imagem final e otimizada
FROM python:3.11-slim-bookworm

WORKDIR /app

# Cria o usuário 'appuser'
RUN useradd --create-home appuser

# Copia as dependências de sistema (Chrome) do estágio anterior
COPY --from=builder /opt/google/chrome /opt/google/chrome
COPY --from=builder /usr/share/keyrings/google-chrome-keyring.gpg /usr/share/keyrings/google-chrome-keyring.gpg

# Copia as dependências Python instaladas do estágio anterior
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copia o código da sua aplicação e define o 'appuser' como o dono
COPY --chown=appuser:appuser ./src ./src

# Define o PYTHONPATH para o diretório de trabalho atual (/app).
ENV PYTHONPATH=.

# Muda para o usuário 'appuser'
USER appuser

# Expõe a porta que a aplicação irá rodar
EXPOSE 10000

# Comando para iniciar a aplicação. O Render injeta a variável $PORT.
#CMD ["uvicorn", "src.consultaLivros.main:app", "--host", "0.0.0.0", "--port", "10000"]
CMD ["uvicorn", "src.consultaLivros.main:app", "--host", "0.0.0.0", "--port", "10000", "--log-level", "debug"]