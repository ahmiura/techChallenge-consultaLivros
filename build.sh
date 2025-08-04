#!/usr/bin/env bash
# Script para configurar o ambiente de build no Render (versão sem sudo).

# Faz com que o script pare imediatamente se algum comando falhar
set -o errexit

echo "Iniciando o processo de build..."

# 1. Instalar as dependências do Python
echo "Instalando dependências do Python do requirements.txt..."
pip install -r requirements.txt

# 2. Instalar as dependências de sistema (Google Chrome para o Selenium)
echo "Instalando dependências de sistema (Google Chrome)..."

# Atualiza a lista de pacotes e instala utilitários básicos
apt-get update
apt-get install -y wget gnupg

# Adiciona a chave de assinatura do Google (método moderno)
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg

# Adiciona o repositório oficial do Google Chrome à lista de fontes do sistema
sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Atualiza a lista de pacotes novamente para incluir o novo repositório
apt-get update

# Instala a versão estável do Google Chrome sem pedir confirmação (-y)
apt-get install -y google-chrome-stable

echo "Build finalizado com sucesso."