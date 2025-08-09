from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositorios.usuarios_repositorio import cria_usuario, busca_usuario
from ..autenticacao.seguranca import get_password_hash, get_current_user
from ..schemas import usuario as schemas_usuario


router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["usuarios"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas_usuario.UsuarioResponse)
async def create_user(dados_usuario: schemas_usuario.Usuario, db: Session = Depends(get_db)):
    """
    Cria um novo usuário no banco de dados.
    O nome de usuário deve ser único.
    """

    # Verifica se o usuario existe
    usuario_existente = busca_usuario(db=db, username=dados_usuario.username)
    if usuario_existente:
        # Retorna 409 Conflict, que é mais semântico para recursos duplicados.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nome de usuário já cadastrado."
        )

    hashed_password = get_password_hash(dados_usuario.password)
    usuario = cria_usuario(db=db, username=dados_usuario.username, hashed_password=hashed_password)

    return usuario


@router.get("/me", response_model=schemas_usuario.UsuarioResponse)
async def read_users_me(current_user: schemas_usuario.UsuarioResponse = Depends(get_current_user)):
    """Retorna os dados do usuário atualmente autenticado."""
    return current_user
