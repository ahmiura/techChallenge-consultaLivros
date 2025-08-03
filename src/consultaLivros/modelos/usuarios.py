from sqlalchemy import Column, Integer, String
from ..db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def __repr__(self):
        return f"<Usuarios(username='{self.username}')>"