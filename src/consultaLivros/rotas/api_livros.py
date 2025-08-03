from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..modelos import livros as modelo_livros
from ..schemas import livros as schemas_livros
from ..db.database import get_db


router = APIRouter(
    prefix="/api/v1",
    tags=["livros"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)


@router.get("/books", response_model=List[schemas_livros.Livro])
async def get_livros(db: Session = Depends(get_db)):
    """Lista todos os livros disponíveis na base de dados (requer autenticação JWT)."""
    todos_livros = db.query(modelo_livros.Livro).all()
    return todos_livros


@router.get("/books/search", response_model=List[schemas_livros.Livro])
async def search_livros(title: str, category: str, db: Session = Depends(get_db)):
    """Busca livros por título e categoria (requer autenticação JWT)."""
    query = db.query(modelo_livros.Livro)
    if title:
        query = query.filter(modelo_livros.Livro.titulo.ilike(f"%{title}%"))
    if category:
        query = query.filter(modelo_livros.Livro.categoria.ilike(f"%{category}%"))
    
    print(f"Query: {query}")
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
    """Obtém estatísticas gerais da base de dados (requer autenticação JWT)."""
    # Obtém o total de livros e categorias
    total_livros = db.query(modelo_livros.Livro).count()

    # Obtém o preço médio dos livros
    preco_medio = db.query(func.avg(modelo_livros.Livro.preco)).scalar() or 0.0

    # Obtém a distribuição de ratings
    rating_query = db.query(modelo_livros.Livro.rating, func.count(modelo_livros.Livro.rating)).group_by(modelo_livros.Livro.rating).all()
    distrib_ratings = {rating: count for rating, count in rating_query}
    
    stats = {
        "total_livros": total_livros,
        "preco_medio": preco_medio,
        "distribuicao_ratings": distrib_ratings
    }
    
    return stats


@router.get("/stats/categories", response_model=dict)
async def get_category_stats(db:Session = Depends(get_db)):
    """Obtém estatísticas por categoria (requer autenticação JWT)."""
    # Obtém todas as categorias
    categorias = db.query(modelo_livros.Livro.categoria).distinct().all()
    categorias = [categoria[0] for categoria in categorias]

    stats_por_categoria = {}
    
    for categoria in categorias:
        total_livros = db.query(modelo_livros.Livro).filter(modelo_livros.Livro.categoria == categoria).count()
        preco_medio = db.query(func.avg(modelo_livros.Livro.preco)).filter(modelo_livros.Livro.categoria == categoria).scalar() or 0.0
        rating_query = db.query(modelo_livros.Livro.rating, func.count(modelo_livros.Livro.rating)).filter(modelo_livros.Livro.categoria == categoria).group_by(modelo_livros.Livro.rating).all()
        distrib_ratings = {rating: count for rating, count in rating_query}
        
        stats_por_categoria[categoria] = {
            "total_livros": total_livros,
            "preco_medio": preco_medio,
            "distribuicao_ratings": distrib_ratings
        }
    
    return stats_por_categoria



