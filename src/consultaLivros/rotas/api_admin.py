from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositorios import livros_repositorio, usuarios_repositorio, tarefas_repositorio
from ..autenticacao.seguranca import get_password_hash, get_current_user
from ..schemas import usuario as schemas_usuario


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["administração"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

@router.delete("/limpa-tabela-livros", status_code=status.HTTP_200_OK)
async def limpa_tabela_livros(db: Session = Depends(get_db), current_user: schemas_usuario.Usuario = Depends(get_current_user)):
    """
    Deleta todos os registros da tabela livros. Requer autenticação.
    """
    livros_deletados = livros_repositorio.deleta_todos_livros(db)
    return {"message": f"{livros_deletados} livros foram deletados com sucesso."}


@router.delete("/limpa-tabela-usuarios", status_code=status.HTTP_200_OK)
async def limpa_tabela_usuarios(db: Session = Depends(get_db), current_user: schemas_usuario.Usuario = Depends(get_current_user)):
    """
    Deleta todos os registros da tabela usuarios. Requer autenticação.
    """
    usuarios_deletados = usuarios_repositorio.deleta_todos_usuarios(db)
    return {"message": f"{usuarios_deletados} usuários foram deletados com sucesso."}


@router.delete("/limpa-usuario/{usuario_id}", status_code=status.HTTP_200_OK)
async def limpa_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: schemas_usuario.Usuario = Depends(get_current_user)):
    """
    Deleta um usuário específico pelo ID. Requer autenticação.
    """
    usuario_deletado = usuarios_repositorio.deleta_usuario_por_id(db, usuario_id)    
    return {"message": f"Usuário {usuario_deletado.username} foi deletado com sucesso."}


@router.delete("/limpa-tabela-tarefas", status_code=status.HTTP_200_OK)
async def limpa_tabela_tarefas(db: Session = Depends(get_db), current_user: schemas_usuario.Usuario = Depends(get_current_user)):
    """
    Deleta todos os registros da tabela tarefas. Requer autenticação.
    """
    tarefas_deletadas = tarefas_repositorio.deleta_todos_tarefas(db)
    return {"message": f"{tarefas_deletadas} tarefas foram deletadas com sucesso."} 