from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositorios import livros_repositorio, usuarios_repositorio, tarefas_repositorio, registro_modelos_repositorio
from ..autenticacao.seguranca import get_current_user
from ..schemas import token as schemas_token
from ..rotas.api_ml import carregar_modelos_em_producao


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["administração"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

@router.delete("/limpa-tabela-livros", status_code=status.HTTP_200_OK)
async def limpa_tabela_livros(db: Session = Depends(get_db), current_user: schemas_token.TokenData = Depends(get_current_user)):
    """
    Deleta todos os registros da tabela livros e reinicia a contagem do ID.
    Requer autenticação.
    """
    livros_repositorio.deleta_todos_livros(db)
    return {"message": "A tabela de livros foi limpa e a contagem de ID foi reiniciada com sucesso."}


@router.delete("/limpa-tabela-usuarios", status_code=status.HTTP_200_OK)
async def limpa_tabela_usuarios(db: Session = Depends(get_db), current_user: schemas_token.TokenData = Depends(get_current_user)):
    """
    Deleta todos os registros da tabela usuarios. Requer autenticação.
    """
    usuarios_deletados = usuarios_repositorio.deleta_todos_usuarios(db)
    return {"message": f"{usuarios_deletados} usuários foram deletados com sucesso."}


@router.delete("/limpa-usuario/{usuario_id}", status_code=status.HTTP_200_OK)
async def limpa_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: schemas_token.TokenData = Depends(get_current_user)):
    """
    Deleta um usuário específico pelo ID. Requer autenticação.
    """
    usuario_deletado = usuarios_repositorio.deleta_usuario_por_id(db, usuario_id)
    if not usuario_deletado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {usuario_id} não encontrado."
        )
    return {"message": f"Usuário '{usuario_deletado.username}' foi deletado com sucesso."}


@router.delete("/limpa-tabela-tarefas", status_code=status.HTTP_200_OK)
async def limpa_tabela_tarefas(db: Session = Depends(get_db), current_user: schemas_token.TokenData = Depends(get_current_user)):
    """
    Deleta todos os registros da tabela tarefas. Requer autenticação.
    """
    tarefas_deletadas = tarefas_repositorio.deleta_todos_tarefas(db)
    return {"message": f"{tarefas_deletadas} tarefas foram deletadas com sucesso."} 


@router.get("/listar-modelos", status_code=status.HTTP_200_OK)
async def listar_modelos(db: Session = Depends(get_db)):
    listar_modelos = registro_modelos_repositorio.listar_todos_modelos(db)
    return {"modelos": listar_modelos}
                        

@router.post("/promover-modelo/{nome_modelo}/{versao}", status_code=status.HTTP_200_OK)
async def promover_modelo(
    nome_modelo: str,
    versao: str,
    db: Session = Depends(get_db),
    current_user: schemas_token.TokenData = Depends(get_current_user)
):
    """
    Promove uma versão específica de um modelo para o ambiente de produção (no DB).
    Requer autenticação.
    """
    modelo_promovido = registro_modelos_repositorio.promover_modelo_para_producao(
        db=db, nome_modelo=nome_modelo, versao=versao
    )

    if not modelo_promovido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modelo '{nome_modelo}' na versão '{versao}' não encontrado no registro."
        )

    return {
        "message": f"Modelo '{modelo_promovido.nome_modelo}' (versão {modelo_promovido.versao}) foi marcado para produção. Faça um novo deploy para ativá-lo."
    }

