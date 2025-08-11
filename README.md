📚 Consulta Livros - API e Pipeline de ML (Versão de Produção)


## **1. Descrição do Projeto**

O projeto Consulta Livros é uma aplicação que demonstra um ciclo de vida completo de um projeto de dados, desde a coleta (web scraping) até a implantação e monitoramento de um pipeline de Machine Learning.

A aplicação realiza a raspagem de dados do site books.toscrape.com, armazena as informações em um banco de dados PostgreSQL e as expõe através de uma API RESTful construída com FastAPI. O sistema inclui autenticação de usuários baseada em tokens JWT, com um ciclo de vida completo de acesso e renovação (token rotation).

O núcleo de ML do projeto implementa um pipeline de MLOps que permite treinar múltiplos modelos de classificação (random forest / regressão logística / svm) e os carrega diretamente em um cache em memória na API. Uma rota de treinamento dedicada permite o recarregamento dos modelos em tempo real ("hot-swap"), sem a necessidade de um novo deploy.

O sistema é complementado por um sistema de monitoramento, que loga todas as requisições no banco de dados e que registra as métricas dos modelos em cache, e um dashboard analítico interativo construído com Streamlit para visualização de métricas da API e do desempenho dos modelos.


## **2. Arquitetura**

O projeto utiliza uma arquitetura desacoplada e containerizada, pronta para um ambiente de produção, seguindo as melhores práticas de Clean Code.

API (FastAPI): O core da aplicação, responsável por servir os endpoints, autenticação e validação de dados via schemas Pydantic.

Banco de Dados (SQLAlchemy + PostgreSQL): Camada de persistência para armazenar dados de livros, usuários, tarefas e logs.

Padrão de Repositório: A lógica de acesso ao banco de dados é abstraída na camada de repositorios, separando a lógica de negócio das operações de banco.

Containerização (Docker): Tanto a API principal quanto o dashboard são containerizados usando Dockerfiles de múltiplos estágios para otimização e segurança, garantindo um ambiente de deploy consistente.

Tarefas em Segundo Plano (BackgroundTasks): Processos demorados, como a raspagem e o treinamento do modelo, são disparados via API e executados em segundo plano, com seu status rastreado no banco de dados.

Pipeline de MLOps (Em Memória):

Treinamento de Múltiplos Modelos: O pipeline treina diversos modelos (Random Forest, Regressão Logística e SVM) em paralelo com joblib.

Deploy "Hot-Swap": Uma rota de treinamento (/ml/train) dispara o processo que, ao final, atualiza um cache thread-safe em memória com as novas instâncias de modelos, permitindo o recarregamento em tempo real sem a necessidade de um novo deploy.

Persistência Opcional: Os artefatos (.pkl) são salvos em disco no contêiner para que possam ser recarregados caso a aplicação reinicie.

Monitoramento e Manutenção:

Dashboard (Streamlit): Um dashboard interativo consome uma rota /ml/cache-status para exibir as métricas dos modelos atualmente em memória, além de visualizar os logs de requisição e predição do banco de dados.

Tarefas Agendadas (APScheduler): Uma tarefa diária é executada para limpar registros antigos de logs e tarefas, mantendo a base de dados otimizada.


## **3. Configuração do Ambiente Local**

Pré-requisitos
Python 3.10 ou superior

Docker

Git

Passos

1.Clonar o Repositório:

``` bash
git clone https://github.com/ahmiura/techChallenge-consultaLivros.git
cd techChallenge-consultaLivros
```

2.Criar e Ativar o Ambiente Virtual:

``` bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual macOS/Linux
source venv/bin/activate

# Ativar no Windows
.\venv\Scripts\activate
```

3.Instalar as Dependências:

``` bash
pip install -r requirements.txt
```

4.Configurar Variáveis de Ambiente:

Crie um arquivo `.env` na raiz do projeto (no mesmo nível que `dashboard.py`) e adicione a URL de conexão do seu banco de dados PostgreSQL.

```dotenv
# Exemplo de .env
DATABASE_URL="postgresql://user:password@localhost:5432/db_livros"
API_URL="http://12cot 0.0.1:8000"

SECRET_KEY="<gere_uma_chave_segura_com_openssl_rand_hex_32>"
REFRESH_SECRET_KEY="<gere_outra_chave_segura_diferente>"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

Substitua `user`, `password`, `localhost`, `5432` e `database_name` com as credenciais do seu banco.

## **4. Execução**

### Deployment (Render)
A aplicação está configurada para deploy contínuo (CI/CD) através do Render. Qualquer push para a branch `main` no repositório do GitHub dispara automaticamente um novo build e deploy.

O projeto é composto por **dois Web Services** no Render, cada um rodando em seu próprio contêiner Docker:

1.  **API (FastAPI)**: Executa a aplicação principal.
    -   **URL Base:** `https://techchallenge-consultalivros.onrender.com/`
    -   **Documentação (Swagger):** `https://techchallenge-consultalivros.onrender.com/docs`
2.  **Dashboard (Streamlit)**: Executa o dashboard de monitoramento.
    -   **URL:** `https://techchallenge-consultalivros-dashboard.onrender.com/`


### Execução Local
A aplicação é composta por dois serviços principais que devem ser executados em terminais separados.

a) Executar a API (FastAPI)
Com o ambiente virtual ativado, execute o seguinte comando a partir da raiz do projeto (consultalivros/):

```bash
uvicorn src.consultaLivros.main:app --reload
```
`src.consultaLivros.main:app`: Aponta para o objeto app do FastAPI dentro do arquivo `src/consultaLivros/main.py`.
`--reload`: Reinicia o servidor automaticamente sempre que um arquivo de código é alterado.

A API estará disponível em http://127.0.0.1:8000. 
A documentação interativa (Swagger UI) pode ser acessada em http://127.0.0.1:8000/docs.

b) Executar o Dashboard (Streamlit)
Em um novo terminal, com o ambiente virtual ativado, execute:

```bash
streamlit run dashboard.py
```
O dashboard será aberto no seu navegador em http://localhost:8501.

c) Executar Tarefas Manuais (Opcional)
Para popular o banco de dados pela primeira vez ou treinar o modelo manualmente:

Executar a Raspagem:

```bash
python -m src.consultaLivros.raspagem.chrome_scraper
```

Executar o Treinamento do Modelo:

```bash
python -m src.consultaLivros.ml.treinamento_modelo
```

## **5. Documentação da API**

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
| GET   | `/api/v1/ml/cache-status`  | Retorna as métricas dos modelos em cache.         
| Nenhuma            |



## **6. Fluxo de Trabalho de MLOps**

O sistema permite um ciclo completo de MLOps diretamente pela API:

1. **Coletar Dados:** Dispare a raspagem para popular o banco:
`POST /api/v1/raspagem/trigger`

2. **Treinar e Carregar Modelos:** Dispare o pipeline de treinamento. Múltiplos modelos serão treinados e carregados diretamente no cache da API:
`POST /api/v1/ml/train`

3. **Analisar e Validar:** Use o Dashboard Streamlit para ver o "Leaderboard de Modelos em Cache". O dashboard consome a rota `/api/v1/ml/cache-status` para exibir as métricas de performance (Acurácia, F1-Score) dos modelos que estão atualmente na memória.

4. **Fazer Predições:** A API está pronta para servir predições com qualquer um dos modelos carregados:
`POST /api/v1/ml/predictions?nome_modelo=random_forest`

5. **Monitorar:** Acompanhe o desempenho das predições no dashboard. Se as métricas indicarem uma queda de performance (model drift), retorne ao passo 2 para retreinar e recarregar os modelos.


## **7. Exemplos de Uso (API em Produção)**

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
