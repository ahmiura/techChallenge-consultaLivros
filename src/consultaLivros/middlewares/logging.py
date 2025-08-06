import time
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

# Configura o logger 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Processa a requisição
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000  # em milissegundos

        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_host": request.client.host,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time, 2),
        }

        # Converte o dicionário para uma string JSON e loga
        logging.info(json.dumps(log_dict))
        
        return response