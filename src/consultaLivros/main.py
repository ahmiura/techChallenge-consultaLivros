from contextlib import asynccontextmanager
from fastapi import FastAPI
from .rotas import api_livros, api_ml, api_token, api_usuarios, api_raspagem
from .db.database import cria_banco


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
    yield
    print("--- Encerrando a aplicação ---")


app = FastAPI(
    title="Consulta Livros API",
    description="API para consulta de livros, raspagem de dados e predições de ML.",
    version="1.0.0",
    lifespan=lifespan
)

# Incluindo os roteadores
app.include_router(api_livros.router)
app.include_router(api_ml.router)
app.include_router(api_token.router)
app.include_router(api_usuarios.router)
app.include_router(api_raspagem.router)