📚 Consulta Livros - API e Pipeline de ML

1. Descrição do Projeto
O projeto **Consulta Livros** é uma aplicação que demonstra o ciclo de vida de um projeto de dados, desde a coleta (web scraping) até a disponibilização de um modelo de Machine Learning via API. A aplicação realiza a raspagem de dados do site `books.toscrape.com`, armazena as informações em um banco de dados PostgreSQL e as expõe através de uma API RESTful construída com FastAPI.

Além disso, o projeto inclui um pipeline de Machine Learning com `scikit-learn` para prever a avaliação de livros (classificando-os como "bons" ou "ruins"). O sistema é complementado por monitoramento, que inclui logs estruturados em JSON e um dashboard analítico interativo construído com Streamlit para visualização de métricas da API.
2. Arquitetura
O projeto utiliza uma arquitetura desacoplada e organizada, seguindo as melhores práticas de Clean Code para projetos Python.

API (`FastAPI`): O núcleo da aplicação, responsável por servir os endpoints, autenticação e validação de dados.

Banco de Dados (`SQLAlchemy` + `PostgreSQL`): Camada de persistência para armazenar os dados dos livros e usuários. A configuração é centralizada e os modelos são desacoplados.

Padrão de Repositório: A lógica de acesso ao banco de dados é abstraída na camada de repositorios, separando a lógica de negócio das operações de banco.

Raspagem de Dados (`Selenium`): Um módulo dedicado para a coleta de dados de forma automatizada do site `books.toscrape.com`.

Machine Learning (`Scikit-learn` + `Pandas`): Um pipeline para pré-processamento de dados, treinamento de um modelo de classificação (`RandomForestClassifier`) e exposição de um endpoint de predição.

Tarefas em Segundo Plano (`BackgroundTasks`): Processos demorados, como a raspagem e o treinamento do modelo, são disparados via API e executados em segundo plano para não bloquear as requisições.

Monitoramento (`Logging` + `Streamlit`): Todas as requisições geram logs estruturados em JSON, que são consumidos por um dashboard em `Streamlit` para visualização e análise de uso da API.

3. Configuração do Ambiente Local
Siga os passos abaixo para configurar o ambiente de desenvolvimento local.

Pré-requisitos
Python 3.10 ou superior

Docker e Docker Compose (Recomendado para rodar o PostgreSQL)

Git

Passos
Clonar o Repositório:

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd consultaLivros
```
Criar e Ativar o Ambiente Virtual:

```bash

# Criar o ambiente
python -m venv venv

# Ativar no macOS/Linux
source venv/bin/activate

# Ativar no Windows
.\venv\Scripts\activate
```
Instalar as Dependências:
Com o ambiente virtual ativado, instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

Configurar Variáveis de Ambiente:
Crie um arquivo `.env` na raiz do projeto (no mesmo nível que `dashboard.py`) e adicione a URL de conexão do seu banco de dados PostgreSQL.

```dotenv
DATABASE_URL="postgresql://user:password@localhost:5432/database_name"
```
Substitua `user`, `password`, `localhost`, `5432` e `database_name` com as credenciais do seu banco.

4. Instruções para Execução
Deployment (Render) +A aplicação está configurada para deploy contínuo (CI/CD) através do Render. Qualquer push para a branch main no repositório do GitHub dispara automaticamente um novo build e deploy da API. + +URL Base da API: https://techchallenge-consultalivros.onrender.com/ + +A documentação interativa (Swagger UI) para a aplicação em produção está disponível em: +https://techchallenge-consultalivros.onrender.com/docs + + +5. Instruções para Execução Local A aplicação é composta por dois serviços principais que devem ser executados em terminais separados.

a) Executar a API (FastAPI)
Com o ambiente virtual ativado, execute o seguinte comando a partir da raiz do projeto (consultalivros/):

Bash

uvicorn src.consultaLivros.main:app --reload
src.consultaLivros.main:app: Aponta para o objeto app do FastAPI dentro do arquivo src/consultaLivros/main.py.

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

python -m src.consultaLivros.raspagem.chrome_scraper
Executar o Treinamento do Modelo:

Bash

python -m src.consultaLivros.ml.treinamento_modelo

5. Documentação da API
A seguir, a lista de endpoints disponíveis:

### Autenticação
| Método | Endpoint             | Descrição                                                          | Autenticação       |
| :----- | :------------------- | :----------------------------------------------------------------- | :----------------- |
| POST   | `/api/v1/auth/login` | Autentica um usuário e retorna tokens de acesso e renovação.         | Nenhuma            |

### Usuários
| Método | Endpoint             | Descrição                                     | Autenticação       |
| :----- | :------------------- | :-------------------------------------------- | :----------------- |
| POST   | `/api/v1/usuarios/`  | Cria um novo usuário.                         | Nenhuma            |

### Livros e Estatísticas
| Método | Endpoint                      | Descrição                                                          | Autenticação       |
| :----- | :---------------------------- | :----------------------------------------------------------------- | :----------------- |
| GET    | `/api/v1/health`              | Endpoint de verificação de saúde da API.                           | Nenhuma            |
| GET    | `/api/v1/books`               | Lista todos os livros disponíveis na base de dados com paginação.  | Nenhuma            |
| GET    | `/api/v1/books/{book_id}`     | Obtém detalhes de um livro específico pelo ID.                     | Nenhuma            |
| GET    | `/api/v1/books/search`        | Busca livros por título e/ou categoria.                            | Nenhuma            |
| GET    | `/api/v1/books/top-rated`     | Obtém os 10 livros mais bem avaliados.                             | Nenhuma            |
| GET    | `/api/v1/books/price-range`   | Obtém livros dentro de um intervalo de preços.                     | Nenhuma            |
| GET    | `/api/v1/categories`          | Lista todas as categorias de livros disponíveis.                   | Nenhuma            |
| GET    | `/api/v1/stats/overview`      | Obtém estatísticas gerais (total de livros, preço médio, etc.).    | Nenhuma            |
| GET    | `/api/v1/stats/categories`    | Obtém estatísticas detalhadas por categoria.                       | Nenhuma            |

### Raspagem de Dados
| Método | Endpoint                          | Descrição                                                 | Autenticação       |
| :----- | :-------------------------------- | :-------------------------------------------------------- | :----------------- |
| POST   | `/api/v1/raspagem/trigger`        | Dispara o processo de raspagem em segundo plano.          | Sim (Bearer Token) |
| GET    | `/api/v1/raspagem/status/{id_tarefa}` | Verifica o status de uma tarefa de raspagem.              | Sim (Bearer Token) |

### Administração
| Método | Endpoint                          | Descrição                                                 | Autenticação       |
| :----- | :-------------------------------- | :-------------------------------------------------------- | :----------------- |
| DELETE | `/api/v1/admin/limpa-tabela-livros` | Deleta todos os registros da tabela de livros.            | Sim (Bearer Token) |
| DELETE | `/api/v1/admin/limpa-tabela-usuarios` | Deleta todos os registros da tabela de usuários.          | Sim (Bearer Token) |
| DELETE | `/api/v1/admin/limpa-tabela-tarefas`  | Deleta todos os registros da tabela de tarefas.           | Sim (Bearer Token) |
| DELETE | `/api/v1/admin/limpa-usuario/{id}`    | Deleta um usuário específico pelo ID.                     | Sim (Bearer Token) |

### Machine Learning
| Método | Endpoint                  | Descrição                                                          | Autenticação       |
| :----- | :------------------------ | :----------------------------------------------------------------- | :----------------- |
| GET    | `/api/v1/ml/features`     | Retorna os dados formatados como features (sem o alvo).            | Nenhuma            |
| GET    | `/api/v1/ml/training-data`| Retorna o dataset completo para treinamento (features + alvo).     | Nenhuma            |
| POST   | `/api/v1/ml/train`        | Dispara o treinamento do modelo em segundo plano.                  | Nenhuma            |
| POST   | `/api/v1/ml/predictions`  | Recebe dados de um livro e retorna uma predição de rating.         | Nenhuma            |

6. Exemplos de Uso (API em Produção)
Os exemplos a seguir utilizam `cURL` para interagir com a API em produção, hospedada no Render. O fluxo demonstra desde a criação de um usuário até a utilização de rotas públicas e protegidas.

1. Criar um novo usuário:

```bash
curl -X 'POST' \
  'https://techchallenge-consultalivros.onrender.com/api/v1/usuarios/' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "meu_usuario",
    "password": "minha_senha_segura"
  }'
```
2. Obter um token de acesso (Login):

```bash
curl -X 'POST' \
  'https://techchallenge-consultalivros.onrender.com/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=meu_usuario&password=minha_senha_segura'
```
Resposta:

```json
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
}
```
3. Disparar a Raspagem (Rota Protegida):
Substitua `SEU_ACCESS_TOKEN` pelo token obtido no passo anterior.

```bash
curl -X 'POST' \
  'https://techchallenge-consultalivros.onrender.com/api/v1/raspagem/trigger' \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN' \
  -d ''
```
Resposta:

```json
{
    "id_tarefa": "e8a1b3f2-1c4d-4a3b-9d2c-8a1b3f2c4d5e",
    "message": "Processo de raspagem iniciado em segundo plano."
}
```
4. Fazer uma Predição de Rating (Rota Pública):

```bash
curl -X 'POST' \
  'https://techchallenge-consultalivros.onrender.com/api/v1/ml/predictions' \
  -H 'Content-Type: application/json' \
  -d '{
    "titulo": "A New Book About Python",
    "preco": 25.50,
    "rating": 4,
    "disponibilidade": true,
    "categoria": "Programming",
    "imagem": "http://example.com/image.jpg"
  }'
```
Resposta:

```json
{
    "livro": "A New Book About Python",
    "rating_predito": 1
}
```
