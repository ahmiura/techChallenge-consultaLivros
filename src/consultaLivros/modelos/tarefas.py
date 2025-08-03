from sqlalchemy import Column, String, JSON, DateTime
from ..db.database import Base
from uuid import uuid4
from sqlalchemy.sql import func

class Tarefa(Base):
    __tablename__ = "tarefas"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    estado = Column(String, index=True, default="pendente")
    resultado = Column(JSON, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    finalizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Tarefa(estado='{self.estado}', resultado={self.resultado})>"