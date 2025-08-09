from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..modelos import livros as modelo_livros
from ..schemas import livros as schemas_livros
from ..db.database import get_db


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
    todos_livros = db.query(modelo_livros.Livro).offset(skip).limit(limit).all()
    return todos_livros


@router.get("/books/search", response_model=List[schemas_livros.Livro])
async def search_livros(
    db: Session = Depends(get_db),
    title: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Busca livros por título e/ou categoria. Pelo menos um dos dois deve ser fornecido.
    """
    if not title and not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça um título ou uma categoria para a busca."
        )

    query = db.query(modelo_livros.Livro)
    if title:
        query = query.filter(modelo_livros.Livro.titulo.ilike(f"%{title}%"))
    if category:
        query = query.filter(modelo_livros.Livro.categoria.ilike(f"%{category}%"))
    livros_encontrados = query.all()
    return livros_encontrados


@router.get("/books/top-rated", response_model=List[schemas_livros.Livro])
async def get_top_rated_books(db: Session = Depends(get_db)):
    """Obtém os livros mais bem avaliados (requer autenticação JWT)."""
    top_rated_books = db.query(modelo_livros.Livro).order_by(modelo_livros.Livro.rating.desc()).limit(10).all()
    return top_rated_books


@router.get("/books/price-range", response_model=List[schemas_livros.Livro])
async def get_books_by_price_range(min: float, max: float, db: Session = Depends(get_db)):
    """Obtém livros dentro de um intervalo de preços (requer autenticação JWT)."""
    if min < 0 or max < 0 or min > max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Intervalo de preços inválido")
    
    livros = db.query(modelo_livros.Livro).filter(modelo_livros.Livro.preco.between(min, max)).all()
    return livros


@router.get("/books/{book_id}", response_model=schemas_livros.Livro)
async def get_livro(book_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes de um livro específico pelo ID (requer autenticação JWT)."""
    livro = db.query(modelo_livros.Livro).filter(modelo_livros.Livro.id == book_id).first()
    if not livro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")
    return livro


@router.get("/categories", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    """Lista todas as categorias de livros disponíveis (requer autenticação JWT)."""
    categorias = db.query(modelo_livros.Livro.categoria).distinct().all()
    return [categoria[0] for categoria in categorias]


@router.get("/health", response_model=dict)
async def health_check():
    """Endpoint de verificação de saúde da API."""
    return {"status": "ok", "message": "API está funcionando corretamente."}



@router.get("/stats/overview", response_model=dict)
async def get_overview_stats(db: Session = Depends(get_db)):
    """Obtém estatísticas gerais da base de dados de forma otimizada."""
    # Query 1: Obter total de livros e preço médio em uma única consulta
    geral_stats = db.query(
        func.count(modelo_livros.Livro.id),
        func.avg(modelo_livros.Livro.preco)
    ).one()
    total_livros, preco_medio = geral_stats
    
    # Query 2: Obter a distribuição de ratings
    rating_query = db.query(
        modelo_livros.Livro.rating, 
        func.count(modelo_livros.Livro.id)
    ).group_by(modelo_livros.Livro.rating).all()
    distrib_ratings = {rating: count for rating, count in rating_query}
    
    return {
        "total_livros": total_livros,
        "preco_medio": preco_medio or 0.0,
        "distribuicao_ratings": distrib_ratings
    }


@router.get("/stats/categories", response_model=dict)
async def get_category_stats(db: Session = Depends(get_db)):
    """Obtém estatísticas por categoria de forma otimizada, evitando o problema N+1."""
    # Query 1: Obter contagem de livros e preço médio por categoria
    stats_query = db.query(
        modelo_livros.Livro.categoria,
        func.count(modelo_livros.Livro.id),
        func.avg(modelo_livros.Livro.preco)
    ).group_by(modelo_livros.Livro.categoria).all()
    
    stats_por_categoria = {
        cat: {"total_livros": count, "preco_medio": avg_price or 0.0, "distribuicao_ratings": {}}
        for cat, count, avg_price in stats_query
    }
    # Query 2: Obter distribuição de ratings por categoria
    rating_dist_query = db.query(modelo_livros.Livro.categoria, modelo_livros.Livro.rating, func.count(modelo_livros.Livro.id)).group_by(modelo_livros.Livro.categoria, modelo_livros.Livro.rating).all()
    for categoria, rating, count in rating_dist_query:
        if categoria in stats_por_categoria:
            stats_por_categoria[categoria]["distribuicao_ratings"][rating] = count
    
    return stats_por_categoria
