from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from ..raspagem.chrome_scraper import rodar_scraper_completo
from ..repositorios.tarefas_repositorio import cria_tarefa, busca_tarefa_por_id, busca_tarefa_por_estados
from ..db.database import get_db

# Importe as funções e modelos do seu arquivo seguranca.py
from ..autenticacao.seguranca import (
    get_current_user,
    TokenData
)

router = APIRouter(
    prefix="/api/v1",
    tags=["raspagem"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

@router.post("/raspagem/trigger", status_code=status.HTTP_202_ACCEPTED)
async def executar_scraper(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Executa o scraper de livros em segundo plano.
    """
    # VERIFICAÇÃO: Impede a execução de múltiplas tarefas de raspagem
    tarefa_em_andamento = busca_tarefa_por_estados(db, estados=["PENDENTE", "EXECUTANDO"])
    if tarefa_em_andamento:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma tarefa de raspagem em andamento (ID: {tarefa_em_andamento.id}, Estado: {tarefa_em_andamento.estado})."
        )

    # Cria uma nova tarefa no banco de dados usando a sessão injetada
    tarefa = cria_tarefa(db, estado="PENDENTE", resultado=None)
    print(f"Tarefa {tarefa.id} criada com sucesso.")

    # A tarefa em background é responsável por gerenciar sua própria sessão de DB
    background_tasks.add_task(rodar_scraper_completo, id_tarefa=tarefa.id)
    return {"id_tarefa": tarefa.id, "message": "Processo de raspagem iniciado em segundo plano."}


@router.get("/raspagem/status/{id_tarefa}", status_code=status.HTTP_200_OK)
async def verificar_status_tarefa(
    id_tarefa: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Verifica o status de uma tarefa de raspagem.
    """
    tarefa = busca_tarefa_por_id(db, id_tarefa)
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada."
        )

    return {"id_tarefa": tarefa.id, "estado": tarefa.estado, "resultado": tarefa.resultado}