import logging
from ..db.database import SessionLocal
from ..repositorios import logs_repositorio, tarefas_repositorio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def executar_limpeza_periodica():
    """
    Executa a limpeza periódica de logs e tarefas antigas no banco de dados.
    Esta função é projetada para ser chamada por um agendador (scheduler).
    """
    logging.info("Iniciando tarefa de limpeza periódica de dados antigos...")
    db = SessionLocal()
    try:
        # Limpeza de logs com mais de 30 dias
        logs_deletados = logs_repositorio.deleta_logs_antigos(db, dias=30)
        if logs_deletados > 0:
            logging.info(f"Limpeza de logs concluída. {logs_deletados} registros antigos foram removidos.")

        # Limpeza de tarefas com mais de 30 dias
        tarefas_deletadas = tarefas_repositorio.deleta_tarefas_antigas(db, dias=30)
        if tarefas_deletadas > 0:
            logging.info(f"Limpeza de tarefas concluída. {tarefas_deletadas} tarefas antigas foram removidas.")

    except Exception as e:
        logging.error(f"Erro durante a execução da limpeza periódica: {e}", exc_info=True)
    finally:
        db.close()
        logging.info("Tarefa de limpeza periódica finalizada.")