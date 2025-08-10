from sqlalchemy.orm import Session
from ..modelos.registro_modelo import RegistroModelo

def registrar_modelo(db: Session, nome_modelo: str, versao: str, caminhos: dict, metricas: dict):
    """Salva os metadados de um modelo treinado no banco de dados."""
    registro = RegistroModelo(
        nome_modelo=nome_modelo,
        versao=versao,
        caminho_arquivo_modelo=caminhos["modelo"],
        caminho_arquivo_encoder=caminhos["encoder"],
        caminho_arquivo_tfidf=caminhos["tfidf"],
        metricas=metricas
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro

def listar_todos_modelos(db: Session):
    """Retorna uma lista de todos os modelos marcados como 'em_producao'."""
    return db.query(RegistroModelo).all()

def listar_modelos_em_producao(db: Session):
    """Retorna uma lista de todos os modelos marcados como 'em_producao'."""
    return db.query(RegistroModelo).filter(RegistroModelo.em_producao == True).all()

def promover_modelo_para_producao(db: Session, nome_modelo: str, versao: str):
    """Define um modelo específico como a versão de produção."""
    # Primeiro, desativa qualquer outro modelo com o mesmo nome
    db.query(RegistroModelo).filter(RegistroModelo.nome_modelo == nome_modelo).update({"em_producao": False})
    
    # Ativa a versão especificada
    modelo = db.query(RegistroModelo).filter(
        RegistroModelo.nome_modelo == nome_modelo,
        RegistroModelo.versao == versao
    ).first()

    if not modelo:
        return None
        
    modelo.em_producao = True
    db.commit()
    return modelo