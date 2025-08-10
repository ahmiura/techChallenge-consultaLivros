import uuid
from sqlalchemy import Column, String, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from ..db.database import Base

class RegistroModelo(Base):
    __tablename__ = "registro_modelos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome_modelo = Column(String, index=True) # Ex: "random_forest", "logistic_regression"
    versao = Column(String, default=lambda: datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    caminho_arquivo_modelo = Column(String)
    caminho_arquivo_encoder = Column(String)
    caminho_arquivo_tfidf = Column(String)
    metricas = Column(JSON) # Armazena a acurácia, F1-score, etc.
    em_producao = Column(Boolean, default=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())