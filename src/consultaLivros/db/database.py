from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = "sqlite:///./banco_de_dados/app.db" 

# Cria o diretório se ele não existir
os.makedirs(os.path.dirname(DATABASE_URL.split("///")[1]), exist_ok=True)

# Cria o engine para o banco de dados SQLite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # connect_args={"check_same_thread": False} é necessário para permitir o uso de múltiplas threads com SQLite
)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa que será usada por todos os modelos
Base = declarative_base()


# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
