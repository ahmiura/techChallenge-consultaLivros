from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositorios.usuarios_repositorio import cria_usuario, busca_usuario
from ..autenticacao.seguranca import get_password_hash
from ..schemas import usuario as schemas_usuario 


router = APIRouter(
    prefix="/api/v1/usuario",
    tags=["usuarios"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

@router.post("/cria", status_code=status.HTTP_201_CREATED, response_model=schemas_usuario.UsuarioResponse)
async def create_user(dados_usuario: schemas_usuario.Usuario, db: Session = Depends(get_db)):
    """Cria um novo usuário no banco de dados."""

    if not dados_usuario.username or not dados_usuario.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username e password são obrigatórios")

    # Verifica se o usuario existe
    usuario_existente = busca_usuario(db=db, username=dados_usuario.username)
    if usuario_existente:
        # Se o usuário for encontrado, lança um erro HTTP 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já cadastrado."
        )

    hashed_password = get_password_hash(dados_usuario.password)
    usuario = cria_usuario(db=db, username=dados_usuario.username, hashed_password=hashed_password)
    
    return usuario
