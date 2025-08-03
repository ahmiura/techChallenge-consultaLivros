from sqlalchemy.orm import Session
from ..modelos.tarefas import Tarefa

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
