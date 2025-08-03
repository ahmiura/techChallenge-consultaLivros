from sqlalchemy.orm import Session
from ..modelos.livros import Livro

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


def busca_todos_livros(db: Session):
    """Busca todos os livros no banco de dados."""
    return db.query(Livro).all()