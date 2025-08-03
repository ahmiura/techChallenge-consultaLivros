from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from .db.database import engine, Base
from .modelos import livros, usuarios, tarefas
from .rotas import api_livros, api_raspagem, api_token, api_ml, api_usuarios  # Importe os roteadores
from .middlewares.logging import StructuredLoggingMiddleware
from prometheus_fastapi_instrumentator import Instrumentator 

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)  

# Inicializando FastAPI
app = FastAPI(
    title = "Consulta de Livros",
    version = "1.0.0",
    description = "Sistema para consulta de dados de livros"
)

# Adiciona a middleware de logging. Ela será a primeira a processar a requisição.
app.add_middleware(StructuredLoggingMiddleware)

# Adiciona o instrumentador do Prometheus
Instrumentator().instrument(app).expose(app)

app.include_router(api_livros.router)  # Inclua o roteador de livros
app.include_router(api_token.router)  # Inclua o roteador de usuários
app.include_router(api_usuarios.router)  # Inclua o roteador de usuários
app.include_router(api_raspagem.router)  # Inclua o roteador de scraping
app.include_router(api_ml.router)  # Inclua o roteador de machine learning
