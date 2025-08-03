from sqlalchemy import Column, Integer, String, Float, Boolean
from ..db.database import Base


class Livro(Base):
    __tablename__ = "livros"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    preco = Column(Float)
    rating = Column(Integer)
    disponibilidade = Column(Boolean)
    categoria = Column(String)
    imagem = Column(String)

    def __repr__(self):
        return f"<Livro(titulo='{self.titulo}', preco={self.preco}, rating='{self.rating}')>"