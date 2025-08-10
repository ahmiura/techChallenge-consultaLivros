from sqlalchemy.orm import Session
from ..modelos.log_predicao import LogPredicao
from ..schemas.livros import LivroBase

def cria_log_predicao(db: Session, livro_input: LivroBase, predicao: int):
    """
    Cria um novo registro de log para uma predição no banco de dados.
    """
    log_entry = LogPredicao(
        input_features=livro_input.model_dump(),
        output_predicao=predicao
    )
    db.add(log_entry)
    db.commit()
    return log_entry