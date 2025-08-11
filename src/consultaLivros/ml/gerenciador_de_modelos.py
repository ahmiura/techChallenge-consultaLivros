import logging
import os
import pickle
from threading import Lock
from typing import Any, Dict


# Cache para armazenar o modelo e o encoder
modelo_cache: Dict[str, Any] = {
    "modelos": {},
    "metricas": {},
    "encoder_prod": None,
    "tfidf_prod": None,
    "lock": Lock()  # Adiciona um lock para garantir acesso thread-safe ao cache
}

def carregar_modelos_do_disco():
    """
    Carrega os modelos e artefatos salvos em disco para o cache em memória.
    Esta função é chamada na inicialização da aplicação (lifespan).
    """
    logging.info("Tentando carregar modelos e artefatos do disco...")
    modelo_dir = 'modelos_ml'
    
    try:
        with modelo_cache["lock"]:
            # Carrega os artefatos de pré-processamento
            with open(os.path.join(modelo_dir, 'encoder.pkl'), 'rb') as f:
                modelo_cache["encoder_prod"] = pickle.load(f)
            with open(os.path.join(modelo_dir, 'tfidf.pkl'), 'rb') as f:
                modelo_cache["tfidf_prod"] = pickle.load(f)

            # Encontra e carrega todos os arquivos de modelo
            modelos_carregados = {}
            for filename in os.listdir(modelo_dir):
                if filename.startswith('modelo_') and filename.endswith('.pkl'):
                    nome_modelo = filename.replace('modelo_', '').replace('.pkl', '')
                    with open(os.path.join(modelo_dir, filename), 'rb') as f:
                        modelos_carregados[nome_modelo] = pickle.load(f)
            
            modelo_cache["modelos"] = modelos_carregados
            logging.info(f"Carregados {len(modelos_carregados)} modelos do disco para o cache.")

    except FileNotFoundError:
        logging.warning("Nenhum arquivo de modelo (.pkl) encontrado no disco. O cache iniciará vazio. Use a rota /train para treinar e popular.")
    except Exception as e:
        logging.error(f"Falha ao carregar modelos do disco: {e}", exc_info=True)

if __name__ == "__main__":
    carregar_modelos_do_disco()