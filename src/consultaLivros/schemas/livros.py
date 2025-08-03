from pydantic import BaseModel
from typing import Dict

# Definindo o modelo de dados para Livro
class Livro(BaseModel):
    titulo: str
    preco: float
    rating: int
    disponibilidade: bool
    categoria: str
    imagem: str


# Definindo o modelo de dados para a visão geral das estatísticas
class EstatisticaGerais(BaseModel):
    total_livros: int
    preco_medio: float
    distribuicao_ratings: Dict[int, int]

    class Config:
        from_attributes = True


# Em schemas/livro.py
class LivroBase(BaseModel):
    titulo: str
    preco: float
    rating: int
    disponibilidade: bool
    categoria: str
    imagem: str
