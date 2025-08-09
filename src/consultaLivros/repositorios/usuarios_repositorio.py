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

def deleta_usuario_por_id(db: Session, usuario_id: int):
    """Deleta um usuário pelo ID."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return None
    db.delete(usuario)
    db.commit()
    return usuario 

def deleta_todos_usuarios(db: Session):
    """Deleta todos os usuários no banco de dados."""
    resultado_query = db.query(Usuario).delete()
    db.commit()
    return resultado_query