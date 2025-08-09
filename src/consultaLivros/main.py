from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from .rotas import api_livros, api_ml, api_token, api_usuarios, api_raspagem, api_admin
from .db.database import cria_banco
from .db.database import SessionLocal
from .repositorios import logs_repositorio
import time
# Importe o novo modelo para que o Alembic/SQLAlchemy o reconheça
from .modelos import logs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .jobs.limpeza_periodica import executar_limpeza_periodica

# Cria uma instância do agendador
scheduler = AsyncIOScheduler(timezone="UTC")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de vida da aplicação para carregar recursos na inicialização
    e liberá-los no encerramento.
    """
    print("--- Iniciando a aplicação ---")
    cria_banco()
    print("Carregando modelos de Machine Learning...")
    api_ml.carregar_modelo_e_encoder()
    
    # Adiciona a tarefa de limpeza para rodar uma vez por dia
    scheduler.add_job(executar_limpeza_periodica, 'interval', days=1, id="limpeza_diaria")
    scheduler.start()
    print("Agendador de tarefas periódicas iniciado.")

    yield
    print("--- Encerrando a aplicação ---")
    scheduler.shutdown()
    print("Agendador de tarefas periódicas encerrado.")

app = FastAPI(
    title="Consulta Livros API",
    description="API para consulta de livros, raspagem de dados e predições de ML.",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def log_requests_to_db(request: Request, call_next):
    """
    Middleware para logar cada requisição HTTP no banco de dados.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # em ms

    # Não logar requisições para a documentação ou para o próprio health check
    if request.url.path.startswith(("/docs", "/openapi.json", "/health")):
        return response

    db = SessionLocal()
    try:
        logs_repositorio.cria_log_request(
            db=db,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=process_time
        )
    finally:
        db.close()

    return response

# Incluindo os roteadores
app.include_router(api_livros.router)
app.include_router(api_ml.router)
app.include_router(api_token.router)
app.include_router(api_usuarios.router)
app.include_router(api_raspagem.router)
app.include_router(api_admin.router)