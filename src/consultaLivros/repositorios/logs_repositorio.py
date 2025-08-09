from sqlalchemy.orm import Session
from ..modelos.logs import LogRequest
import pandas as pd
from datetime import datetime, timedelta, timezone

def cria_log_request(db: Session, method: str, path: str, status_code: int, process_time_ms: float):
    log_entry = LogRequest(
        method=method,
        path=path,
        status_code=status_code,
        process_time_ms=process_time_ms
    )
    db.add(log_entry)
    db.commit()
    return log_entry

def busca_logs_para_dataframe(db: Session) -> pd.DataFrame:
    query = db.query(LogRequest).statement
    df = pd.read_sql_query(query, db.bind)
    return df

def deleta_logs_antigos(db: Session, dias: int) -> int:
    """Deleta registros de log mais antigos que um número específico de dias."""
    data_limite = datetime.now(timezone.utc) - timedelta(days=dias)
    query = db.query(LogRequest).filter(LogRequest.timestamp < data_limite)
    num_deletados = query.delete(synchronize_session=False)
    db.commit()
    return num_deletados