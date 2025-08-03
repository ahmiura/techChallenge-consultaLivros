📚 Consulta Livros - API e Pipeline de ML
1. Descrição do Projeto
Consulta Livros é uma aplicação completa que demonstra um ciclo de vida de um projeto de dados, desde a coleta até a predição com Machine Learning. A aplicação realiza a raspagem de dados do site books.toscrape.com, armazena as informações em um banco de dados e as expõe através de uma API RESTful robusta construída com FastAPI.!!

Além disso, o projeto inclui um pipeline de Machine Learning para prever a avaliação de livros e um sistema de monitoramento com logs estruturados, métricas de performance e um dashboard analítico em Streamlit.

2. Arquitetura
O projeto utiliza uma arquitetura de microsserviços desacoplada e organizada, seguindo as melhores práticas de Clean Code para projetos Python.

API (FastAPI): O núcleo da aplicação, responsável por servir os endpoints, autenticação e validação de dados.

Banco de Dados (SQLAlchemy + SQLite): Camada de persistência para armazenar os dados dos livros e usuários. A configuração é centralizada e os modelos são desacoplados.

Padrão de Repositório: A lógica de acesso ao banco de dados é abstraída na camada de repositorios, separando a lógica de negócio das operações de banco.

Raspagem de Dados (Selenium): Um módulo dedicado para a coleta de dados de forma automatizada.

Machine Learning (Scikit-learn + Pandas): Um pipeline para pré-processamento de dados, treinamento de um modelo de classificação (RandomForestClassifier) e exposição de um endpoint de predição.

Tarefas em Segundo Plano (BackgroundTasks): Processos demorados, como a raspagem e o treinamento do modelo, são disparados via API e executados em segundo plano para não bloquear as requisições.

Monitoramento (Logging + Streamlit): Todas as requisições geram logs estruturados em JSON, que são consumidos por um dashboard em Streamlit para visualização e análise de uso da API.

3. Instalação e Configuração
Siga os passos abaixo para configurar o ambiente de desenvolvimento local.

Pré-requisitos
Python 3.10 ou superior

Git

Passos
Clonar o Repositório:

Bash

git clone <url-do-seu-repositorio>
cd consultalivros
Criar e Ativar o Ambiente Virtual:

Bash

# Criar o ambiente
python -m venv venv

# Ativar no macOS/Linux
source venv/bin/activate

# Ativar no Windows
.\venv\Scripts\activate
Instalar as Dependências:
Primeiro, gere o arquivo requirements.txt se ele não existir, com o ambiente ativado:

Bash

pip freeze > requirements.txt
Em seguida, instale as dependências:

Bash

pip install -r requirements.txt
Configurar Variáveis de Ambiente (Opcional):
Se você moveu os segredos para um arquivo .env, crie-o na raiz do projeto. Caso contrário, certifique-se de que as variáveis de segurança em src/autenticacao/seguranca.py estão definidas.

4. Instruções para Execução
A aplicação é composta por dois serviços principais que devem ser executados em terminais separados.

a) Executar a API (FastAPI)
Com o ambiente virtual ativado, execute o seguinte comando a partir da raiz do projeto (consultalivros/):

Bash

uvicorn src.main:app --reload
src.main:app: Aponta para o objeto app do FastAPI dentro do arquivo src/main.py.

--reload: Reinicia o servidor automaticamente sempre que um arquivo de código é alterado.

A API estará disponível em http://127.0.0.1:8000. A documentação interativa (Swagger UI) pode ser acessada em http://127.0.0.1:8000/docs.

b) Executar o Dashboard (Streamlit)
Em um novo terminal, com o ambiente virtual ativado, execute:

Bash

streamlit run dashboard.py
O dashboard será aberto no seu navegador, geralmente em http://localhost:8501.

c) Executar Tarefas Manuais (Opcional)
Para popular o banco de dados pela primeira vez ou treinar o modelo manualmente:

Executar a Raspagem:

Bash

python -m src.raspagem.chrome_scraper
Executar o Treinamento do Modelo:

Bash

python -m src.ia.treinamento
5. Documentação das Rotas da API
A seguir, a lista de endpoints disponíveis, agrupados por funcionalidade.

Autenticação
Método	Endpoint	Descrição	Autenticação
POST	/api/v1/auth/login	Autentica um usuário e retorna tokens de acesso e renovação.	Nenhuma
POST	/api/v1/auth/refresh	Gera um novo token de acesso usando um token de renovação.	Nenhuma

Exportar para as Planilhas
Usuários
Método	Endpoint	Descrição	Autenticação
POST	/api/v1/usuarios/	Cria um novo usuário.	Nenhuma
GET	/api/v1/users/me	Retorna os dados do usuário autenticado.	Sim (Bearer Token)

Exportar para as Planilhas
Livros
Método	Endpoint	Descrição	Autenticação
GET	/api/v1/livros	Lista todos os livros da base.	Sim (Bearer Token)
GET	/api/v1/livros/{id_livro}	Retorna um livro específico pelo ID.	Sim (Bearer Token)
GET	/api/v1/livros/search	Busca livros por título e/ou categoria.	Sim (Bearer Token)

Exportar para as Planilhas
Raspagem de Dados
Método	Endpoint	Descrição	Autenticação
POST	/api/v1/scraping/trigger	Dispara o processo de raspagem em segundo plano.	Sim (Bearer Token)
GET	/api/v1/scraping/status/{id_tarefa}	Verifica o status de uma tarefa de raspagem.	Sim (Bearer Token)

Exportar para as Planilhas
Machine Learning
Método	Endpoint	Descrição	Autenticação
GET	/api/v1/ml/features	Retorna os dados formatados como features (sem o alvo).	Nenhuma
GET	/api/v1/ml/training-data	Retorna o dataset completo para treinamento (features + alvo).	Nenhuma
POST	/api/v1/ml/train	Dispara o treinamento do modelo em segundo plano.	Sim (Bearer Token)
POST	/api/v1/ml/predictions	Recebe dados de um livro e retorna uma predição de rating.	Sim (Bearer Token)

Exportar para as Planilhas
6. Exemplos de Chamadas (cURL)
1. Criar um novo usuário:

Bash

curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/usuarios/' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "meu_usuario",
    "password": "minha_senha_segura"
  }'
2. Obter um token de acesso (Login):

Bash

curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=meu_usuario&password=minha_senha_segura'
Resposta:

JSON

{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
}
3. Disparar a Raspagem (Rota Protegida):
Substitua SEU_ACCESS_TOKEN pelo token obtido no passo anterior.

Bash

curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/scraping/trigger' \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN'
Resposta:

JSON

{
    "id_tarefa": "e8a1b3f2-1c4d-4a3b-9d2c-8a1b3f2c4d5e",
    "message": "Processo de raspagem iniciado em segundo plano."
}
4. Fazer uma Predição de Rating (Rota Protegida):

Bash

curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/ml/predictions' \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "titulo": "A New Book About Python",
    "preco": 25.50,
    "rating": 4,
    "disponibilidade": true,
    "categoria": "Programming",
    "imagem": "http://example.com/image.jpg"
  }'
Resposta:

JSON

{
    "livro": "A New Book About Python",
    "rating_predito": 1
}
