from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from ..ml.preparacao_dados import preparar_dados_livros, preparar_input_para_predicao
from ..ml.treinamento_modelo import treinar_e_carregar_modelos_em_cache
from ..schemas.livros import LivroBase
import pickle
from ..db.database import get_db, SessionLocal
import pandas as pd
from typing import List, Dict, Any
import os
import logging
from threading import Lock


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



router = APIRouter(
    prefix="/api/v1/ml",
    tags=["machine_learning"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)


@router.get("/features", response_model=List[dict])
async def get_features(db: Session = Depends(get_db)):
    """Retorna os dados dos livros formatados como features para ML."""
    features_df, _, _ = preparar_dados_livros(db)
    if features_df.empty:
        return []
    
    # Retorna o DataFrame de features (sem a coluna alvo, se houver)
    return features_df.to_dict(orient='records')


@router.get("/training-data", response_model=List[dict])
async def get_training_data(db: Session = Depends(get_db)):
    """
    Retorna o dataset com features e a coluna 'rating' original.
    A coluna 'rating' é usada para gerar o alvo (target) no processo de treinamento.
    """
    features_df, _, _ = preparar_dados_livros(db)
    if features_df.empty:
        return []
    return features_df.to_dict(orient='records')


@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
async def train_model(background_tasks: BackgroundTasks):
    """Treina o modelo de machine learning e salva os artefatos."""
    try:
        # Tarefa em segundo plano 
        background_tasks.add_task(treinar_e_carregar_modelos_em_cache, cache=modelo_cache)
        return {"message": "Processo do treino do Modelo iniciado em segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# O endpoint de predição agora usa os modelos carregados do cache
@router.post("/predictions", response_model=dict)
async def get_prediction(
    livro_input: LivroBase, 
    nome_modelo: str = "random_forest", 
    db: Session = Depends(get_db)):
    """
        Recebe os dados de um livro e retorna uma predição usando um modelo do cache.
    """
    with modelo_cache["lock"]:
        modelo_selecionado = modelo_cache["modelos"].get(nome_modelo)

        logging.info(f"Todos os modelos disponíveis no cache: {modelo_cache['modelos'].keys()}")
        logging.info(f"Modelo selecionado: {modelo_selecionado}")
        
        if modelo_selecionado is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Modelo '{nome_modelo}' não está treinado ou disponível no cache. Execute o treinamento primeiro."
            )
        
        encoder = modelo_cache.get("encoder_prod")
        tfidf = modelo_cache.get("tfidf_prod")
        
        if not encoder or not tfidf:
             raise HTTPException(status_code=503, detail="Artefatos de pré-processamento não carregados.")

        # A lógica de preparação e predição continua a mesma...
        input_df_processed = preparar_input_para_predicao(
            livro_input,
            encoder,
            tfidf,
            modelo_selecionado.feature_names_in_
        )
        prediction = modelo_selecionado.predict(input_df_processed)
        predicted_class = int(prediction[0])

    return {
        "livro": livro_input.titulo, 
        "modelo_usado": nome_modelo,
        "rating_predito": predicted_class
    }


@router.get("/cache-status", response_model=dict)
async def get_cache_status():
    """
    Retorna o estado atual do cache de modelos de ML, incluindo os modelos
    carregados e suas métricas de treinamento mais recentes.
    """
    with modelo_cache["lock"]:
        # Prepara uma resposta segura sem expor os objetos do modelo
        modelos_info = {}
        metricas = modelo_cache.get("metricas", {})
        for nome_modelo in modelo_cache.get("modelos", {}).keys():
            modelos_info[nome_modelo] = {
                "nome": nome_modelo,
                "metricas": metricas.get(nome_modelo, "N/A")
            }

    return {
        "modelos_carregados": list(modelo_cache.get("modelos", {}).keys()),
        "artefatos_carregados": "encoder_prod" in modelo_cache and "tfidf_prod" in modelo_cache,
        "detalhes_modelos": list(modelos_info.values())
    }