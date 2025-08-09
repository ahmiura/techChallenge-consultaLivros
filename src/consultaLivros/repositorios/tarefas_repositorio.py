from sqlalchemy.orm import Session
from ..modelos.tarefas import Tarefa
from datetime import datetime, timedelta, timezone

def cria_tarefa(db: Session, estado: str = "pendente", resultado: dict = None):
    """Cria uma nova tarefa no banco de dados."""
    tarefa = Tarefa(estado=estado, resultado=resultado)
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return tarefa   

def busca_tarefa_por_id(db: Session, tarefa_id: str):
    """Busca uma tarefa pelo ID."""
    tarefa = db.query(Tarefa).filter(Tarefa.id == tarefa_id).first()
    if not tarefa:
        print("Tarefa não encontrada")
        return
    return tarefa   

def busca_tarefa_por_estados(db: Session, estados: list[str]):
    """Busca a primeira tarefa que corresponde a um dos estados fornecidos."""
    return db.query(Tarefa).filter(Tarefa.estado.in_(estados)).first()


def atualiza_tarefa(db: Session, tarefa_id: str, estado: str = None, resultado: dict = None):
    """Atualiza o estado ou resultado de uma tarefa."""
    tarefa = busca_tarefa_por_id(db, tarefa_id)
    if estado:
        tarefa.estado = estado
    if resultado is not None:
        tarefa.resultado = resultado
    db.commit()
    db.refresh(tarefa)
    return tarefa

def deleta_todos_tarefas(db: Session):
    """Deleta todas as tarefas no banco de dados."""
    resultado_query = db.query(Tarefa).delete()
    db.commit()
    return resultado_query

def deleta_tarefas_antigas(db: Session, dias: int) -> int:
    """
    Deleta tarefas em estado final (CONCLUIDA, ERRO) mais antigas
    que um número específico de dias, com base na data de finalização.
    """
    data_limite = datetime.now(timezone.utc) - timedelta(days=dias)
    estados_finais = ["CONCLUIDA", "ERRO"]
    
    query = db.query(Tarefa).filter(
        Tarefa.estado.in_(estados_finais),
        Tarefa.finalizado_em < data_limite
    )
    
    num_deletados = query.delete(synchronize_session=False)
    db.commit()
    return num_deletados
