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

# Exceção para credenciais inválidas
credentials_exception = HTTPException( 
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalido refresh token",
    headers={"WWW-Authenticate": "Bearer"},
)

@router.post("/auth/login", response_model=schemas_token.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = busca_usuario(db=db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise credentials_exception

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
async def refresh_access_token(request: schemas_token.RefreshTokenRequest):
    refresh_token = request.refresh_token
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    new_access_token = create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(
        data={"sub": username}, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
