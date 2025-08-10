from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from ..db.database import Base
import uuid

class LogPredicao(Base):
    __tablename__ = "log_predicoes"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Armazena os inputs que o modelo recebeu
    input_features = Column(JSON)
    
    # Armazena a predição (output) do modelo
    output_predicao = Column(Integer)