from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv() 

# Lê a URL do banco de dados da variável de ambiente 'DATABASE_URL'
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida.")

# Cria o engine para o banco de dados 
engine = create_engine(DATABASE_URL)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa que será usada por todos os modelos
Base = declarative_base()

def cria_banco():
    """
    Cria todas as tabelas no banco de dados definidas pelos modelos SQLAlchemy
    que herdam de Base. Esta função é chamada na inicialização da aplicação
    para garantir que o schema do banco de dados esteja pronto.
    """
    Base.metadata.create_all(bind=engine)


# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
