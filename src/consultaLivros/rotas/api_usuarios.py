from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositorios.usuarios_repositorio import cria_usuario
from ..autenticacao.seguranca import get_password_hash
from ..schemas import usuario as schemas_usuario 


router = APIRouter(
    prefix="/api/v1",
    tags=["usuarios"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

@router.post("/usuario/create", status_code=status.HTTP_201_CREATED, response_model=schemas_usuario.UsuarioResponse)
async def create_user(user_data: schemas_usuario.Usuario, db: Session = Depends(get_db)):
    """Cria um novo usuário no banco de dados."""

    if not user_data.username or not user_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username e password são obrigatórios")

    hashed_password = get_password_hash(user_data.password)
    usuario = cria_usuario(db=db, username=user_data.username, hashed_password=hashed_password)
    
    return usuario
