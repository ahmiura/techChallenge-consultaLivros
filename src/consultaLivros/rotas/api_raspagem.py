from fastapi import APIRouter, Depends, status, BackgroundTasks
from ..raspagem.chrome_scraper import rodar_scraper_completo
from ..repositorios.tarefas_repositorio import cria_tarefa, busca_tarefa_por_id
from ..db.database import SessionLocal

# Importe as funções e modelos do seu arquivo seguranca.py
from ..autenticacao.seguranca import (
    get_current_user,
    TokenData,
    oauth2_scheme # Importe oauth2_scheme aqui
)

router = APIRouter(
    prefix="/api/v1",
    tags=["scraper"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)

@router.post("/scraping/trigger", status_code=status.HTTP_202_ACCEPTED)
async def executar_scraper(background_tasks: BackgroundTasks, current_user: TokenData = Depends(get_current_user)):
    """
    Executa o scraper de livros em segundo plano.
    """
    # Cria uma nova tarefa no banco de dados
    with SessionLocal() as db:
        tarefa = cria_tarefa(db, estado="PENDENTE", resultado=None)
        print(f"Tarefa {tarefa.id} criada com sucesso.")

    background_tasks.add_task(rodar_scraper_completo, id_tarefa=tarefa.id)
    return {"id_tarefa": tarefa.id, "message": "Processo de raspagem iniciado em segundo plano."}


@router.get("/scraping/status/{id_tarefa}", status_code=status.HTTP_200_OK)
async def verificar_status_tarefa(id_tarefa: str):
    """
    Verifica o status de uma tarefa de raspagem.
    """
    with SessionLocal() as db:
        tarefa = busca_tarefa_por_id(db, id_tarefa)
        if not tarefa:
            return {"message": "Tarefa não encontrada."}
        
        return {
            "id_tarefa": tarefa.id,
            "estado": tarefa.estado,
            "resultado": tarefa.resultado
        }