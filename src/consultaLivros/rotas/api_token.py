from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from ..schemas import token as schemas_token
from ..repositorios.usuarios_repositorio import busca_usuario
from ..db.database import get_db
from sqlalchemy.orm import Session

# Importe as funções e modelos do seu arquivo seguranca.py
from ..autenticacao.seguranca import (
    create_access_token,
    create_refresh_token,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    REFRESH_SECRET_KEY,
    ALGORITHM
)


router = APIRouter(
    prefix="/api/v1",
    tags=["autenticação"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

# Exceções para cenários de autenticação
login_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Nome de usuário ou senha incorretos",
    headers={"WWW-Authenticate": "Bearer"},
)

refresh_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Refresh token inválido ou expirado",
    headers={"WWW-Authenticate": "Bearer"},
)

@router.post("/auth/login", response_model=schemas_token.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    """Autentica um usuário e retorna um par de tokens de acesso e de atualização."""
    user = busca_usuario(db=db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise login_exception

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/auth/refresh", response_model=schemas_token.Token)
async def refresh_access_token(
    request: schemas_token.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Gera um novo par de tokens (acesso e atualização) a partir de um refresh token válido.
    Isso implementa a rotação de tokens: o refresh token antigo é invalidado (implicitamente,
    pois um novo é emitido) a cada uso.
    """
    refresh_token = request.refresh_token
    try:
        # Decodifica o token para obter o payload
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise refresh_exception

        # VERIFICAÇÃO DE SEGURANÇA: Garante que o usuário do token ainda existe no banco.
        user = busca_usuario(db, username=username)
        if not user:
            raise refresh_exception

    except JWTError:
        raise refresh_exception

    # Cria novos tokens apenas se o usuário for válido
    access_token = create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(
        data={"sub": username}, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
