# Estágio 1: Builder - Instala dependências Python
FROM python:3.11-slim-bookworm AS builder

# Diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências e instala os pacotes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 2: Runner - A imagem final e otimizada
FROM python:3.11-slim-bookworm

WORKDIR /app

# Instala o Google Chrome e suas dependências de sistema
# Isso garante que todas as bibliotecas compartilhadas (.so) estejam presentes
RUN apt-get update && \
    apt-get install -y wget gnupg --no-install-recommends && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Cria o usuário 'appuser'
RUN useradd --create-home appuser

# Cria o diretório para os modelos de ML e define o 'appuser' como dono
RUN mkdir /app/modelos_ml && chown appuser:appuser /app/modelos_ml

# Copia as dependências Python instaladas do estágio anterior
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copia os execs (uvicorn)
COPY --from=builder /usr/local/bin /usr/local/bin

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