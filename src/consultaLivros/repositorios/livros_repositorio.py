from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from ..modelos.livros import Livro
from typing import List, Optional
import pandas as pd
import logging

def salva_dados_livros(db: Session, dados_todos_livros: list):
    """Salva uma lista de livros no banco de dados."""
    if not dados_todos_livros:
        print("Nenhum dado de livro para salvar.")
        return
    
    print(f"Salvando {len(dados_todos_livros)} livros no banco de dados...")

    livros_obj = [
        Livro(
            titulo=data['titulo'],
            preco=data['preco'],
            rating=data['rating'],
            disponibilidade=data['disponibilidade'],
            categoria=data['categoria'],
            imagem=data['imagem']
        )
        for data in dados_todos_livros
    ]

    db.add_all(livros_obj)  # Adiciona todos os livros à sessão
    db.commit()
    print(f"{len(livros_obj)} livros salvos com sucesso.")


def busca_todos_livros(db: Session, skip: int = 0, limit: int = 100) -> List[Livro]:
    """Busca todos os livros no banco de dados."""
    return db.query(Livro).offset(skip).limit(limit).all()


def busca_livro_por_id(db: Session, livro_id: int) -> Optional[Livro]:
    """Busca um livro específico pelo seu ID."""
    return db.query(Livro).filter(Livro.id == livro_id).first()


def busca_livros_por_filtro(db: Session, titulo: Optional[str], categoria: Optional[str]) -> List[Livro]:
    """Busca livros por título e/ou categoria."""
    query = db.query(Livro)
    if titulo:
        query = query.filter(Livro.titulo.ilike(f"%{titulo}%"))
    if categoria:
        query = query.filter(Livro.categoria.ilike(f"%{categoria}%"))
    return query.all()


def busca_livros_top_rated(db: Session) -> List[Livro]:
    """Busca os 10 livros com maior rating."""
    return db.query(Livro).order_by(Livro.rating.desc()).limit(10).all()


def busca_livros_por_preco(db: Session, min_preco: float, max_preco: float) -> List[Livro]:
    """Busca livros dentro de um intervalo de preços."""
    return db.query(Livro).filter(Livro.preco.between(min_preco, max_preco)).all()


def busca_todas_categorias(db: Session) -> List[str]:
    """Busca todas as categorias distintas de livros."""
    categorias_tuplas = db.query(Livro.categoria).distinct().all()
    return [categoria[0] for categoria in categorias_tuplas]


def deleta_todos_livros(db: Session) -> int:
    """Deleta todos os livros no banco de dados."""
    resultado_query = db.query(Livro).delete()
    db.commit()
    return resultado_query


def obter_estatisticas_gerais(db: Session) -> dict:
    """Busca estatísticas gerais (total, preço médio, distribuição de ratings)."""
    geral_stats = db.query(
        func.count(Livro.id),
        func.avg(Livro.preco)
    ).one()
    total_livros, preco_medio = geral_stats

    rating_query = db.query(
        Livro.rating,
        func.count(Livro.id)
    ).group_by(Livro.rating).all()
    distrib_ratings = {rating: count for rating, count in rating_query}

    return {
        "total_livros": total_livros,
        "preco_medio": preco_medio or 0.0,
        "distribuicao_ratings": distrib_ratings
    }


def obter_estatisticas_por_categoria(db: Session) -> dict:
    """Busca estatísticas detalhadas por categoria."""
    stats_query = db.query(
        Livro.categoria,
        func.count(Livro.id),
        func.avg(Livro.preco)
    ).group_by(Livro.categoria).all()

    stats_por_categoria = {
        cat: {"total_livros": count, "preco_medio": avg_price or 0.0, "distribuicao_ratings": {}}
        for cat, count, avg_price in stats_query
    }

    rating_dist_query = db.query(Livro.categoria, Livro.rating, func.count(Livro.id)).group_by(Livro.categoria, Livro.rating).all()
    for categoria, rating, count in rating_dist_query:
        if categoria in stats_por_categoria:
            stats_por_categoria[categoria]["distribuicao_ratings"][rating] = count

    return stats_por_categoria


def verificar_conexao_db(db: Session) -> bool:
    """
    Executa uma query simples para verificar se a conexão com o banco de dados está ativa.
    Retorna True se a conexão for bem-sucedida, False caso contrário.
    """
    try:
        db.execute(text('SELECT 1'))
        return True
    except SQLAlchemyError as e:
        logging.error(f"Falha na verificação de conexão com o banco de dados: {e}", exc_info=True)
        return False


def busca_todos_livros_para_dataframe(db: Session) -> pd.DataFrame:
    """
    Busca todos os livros no banco de dados e os retorna como um DataFrame do Pandas.
    Este método é otimizado para pipelines de ML.
    """
    try:
        query = db.query(Livro).statement
        df = pd.read_sql_query(query, db.bind)
        return df
    except SQLAlchemyError as e:
        logging.error(f"Erro de banco de dados ao buscar livros para DataFrame: {e}", exc_info=True)
        return pd.DataFrame()
