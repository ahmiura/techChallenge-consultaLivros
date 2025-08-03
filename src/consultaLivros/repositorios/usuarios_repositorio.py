from sqlalchemy.orm import Session
from ..modelos.usuarios  import Usuario
from ..autenticacao.seguranca import get_password_hash 

def cria_usuario(db: Session, username: str, hashed_password: str):
    """Cria um novo usuário no banco de dados."""
    db_user = Usuario(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def busca_usuario(db: Session, username: str):
    """Obtém um usuário pelo nome de usuário."""
    return db.query(Usuario).filter(Usuario.username == username).first()
