from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from ..modelos import livros as modelo_livros
from ..schemas import livros as schemas_livros
from ..repositorios import livros_repositorio
from ..db.database import get_db

import logging


router = APIRouter(
    prefix="/api/v1",
    tags=["livros"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)


@router.get("/books", response_model=List[schemas_livros.Livro])
async def get_livros(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Lista todos os livros disponíveis na base de dados com paginação.
    """
    todos_livros = livros_repositorio.busca_todos_livros(db, skip=skip, limit=limit)
    return todos_livros


@router.get("/books/search", response_model=List[schemas_livros.Livro])
async def search_livros(
    db: Session = Depends(get_db),
    titulo: Optional[str] = None,
    categoria: Optional[str] = None
):
    """
    Busca livros por título e/ou categoria. Pelo menos um dos dois deve ser fornecido.
    """
    if not titulo and not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça um título ou uma categoria para a busca."
        )

    livros_encontrados = livros_repositorio.busca_livros_por_filtro(db, titulo=titulo, categoria=categoria)
    return livros_encontrados


@router.get("/books/top-rated", response_model=List[schemas_livros.Livro])
async def get_top_rated_books(db: Session = Depends(get_db)):
    """Obtém os livros mais bem avaliados (requer autenticação JWT)."""
    top_rated_books = livros_repositorio.busca_livros_top_rated(db)
    return top_rated_books


@router.get("/books/price-range", response_model=List[schemas_livros.Livro])
async def get_books_by_price_range(min_preco: float, max_preco: float, db: Session = Depends(get_db)):
    """Obtém livros dentro de um intervalo de preços (requer autenticação JWT)."""
    if min_preco < 0 or max_preco < 0 or min_preco > max_preco:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Intervalo de preços inválido")
    
    livros = livros_repositorio.busca_livros_por_preco(db, min_preco=min_preco, max_preco=max_preco)
    return livros


@router.get("/books/{book_id}", response_model=schemas_livros.Livro)
async def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes de um livro específico pelo seu ID."""
    livro = livros_repositorio.busca_livro_por_id(db, livro_id=book_id)
    if not livro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")
    return livro


@router.get("/categories", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    """Lista todas as categorias de livros disponíveis (requer autenticação JWT)."""
    categorias = livros_repositorio.busca_todas_categorias(db)
    return categorias


@router.get("/health", response_model=dict)
async def health_check(db: Session = Depends(get_db)):
    """
    Endpoint de verificação de saúde da API.
    Verifica se a API está no ar e se a conexão com o banco de dados está ativa.
    """
    if livros_repositorio.verificar_conexao_db(db):
        return {"status": "ok", "message": "API e banco de dados estão funcionando corretamente."}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A API está no ar, mas não foi possível conectar ao banco de dados."
        )



@router.get("/stats/overview", response_model=dict)
async def get_overview_stats(db: Session = Depends(get_db)):
    """Obtém estatísticas gerais da base de dados de forma otimizada."""
    try:
        stats = livros_repositorio.obter_estatisticas_gerais(db)
        return stats
    except SQLAlchemyError as e:
        logging.error(f"Erro de banco de dados ao buscar estatísticas gerais: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao processar as estatísticas gerais."
        )


@router.get("/stats/categories", response_model=dict)
async def get_category_stats(db: Session = Depends(get_db)):
    """Obtém estatísticas por categoria de forma otimizada, evitando o problema N+1."""
    try:
        stats = livros_repositorio.obter_estatisticas_por_categoria(db)
        return stats
    except SQLAlchemyError as e:
        logging.error(f"Erro de banco de dados ao buscar estatísticas por categoria: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao processar as estatísticas por categoria."
        )
