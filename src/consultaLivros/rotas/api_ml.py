from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from ..ml.preparacao_dados import preparar_dados_livros, preparar_input_para_predicao
from ..ml.treinamento_modelo import treinar_e_salvar_modelo
from ..schemas.livros import LivroBase
import pickle
from ..db.database import get_db
import pandas as pd
from typing import List, Dict, Any
import os
import logging
from threading import Lock

# Constantes para os caminhos dos modelos, facilitando a manutenção
MODELOS_DIR = "modelos_ml"
CAMINHO_MODELO = os.path.join(MODELOS_DIR, 'modelo_livros.pkl')
CAMINHO_ENCODER = os.path.join(MODELOS_DIR, 'encoder_livros.pkl')
CAMINHO_TFIDF = os.path.join(MODELOS_DIR, 'tfidf_livros.pkl')

# Cache para armazenar o modelo e o encoder
modelo_cache: Dict[str, Any] = {
    "modelo": None,
    "encoder": None,
    "tfidf": None,
    "lock": Lock()  # Adiciona um lock para garantir acesso thread-safe ao cache
}

def carregar_modelo_e_encoder():
    """
    Carrega o modelo, o encoder e o vetorizador TF-IDF do disco para o cache.
    Levanta um FileNotFoundError se algum arquivo não for encontrado.
    Esta função é chamada na inicialização da aplicação (lifespan).
    """
    logging.info("Tentando carregar modelo, encoder e TF-IDF do disco...")
    try:
        with open(CAMINHO_MODELO, 'rb') as model_file:
            modelo_cache["modelo"] = pickle.load(model_file)
        with open(CAMINHO_ENCODER, 'rb') as encoder_file:
            modelo_cache["encoder"] = pickle.load(encoder_file)
        with open(CAMINHO_TFIDF, 'rb') as tfidf_file:
            modelo_cache["tfidf"] = pickle.load(tfidf_file)

        logging.info("Modelo, encoder e TF-IDF carregados com sucesso para o cache.")
    except FileNotFoundError:
        logging.warning("Arquivos de modelo não encontrados. A API iniciará sem modelo carregado. Use o endpoint /train para treinar um.")
        # Limpa o cache para garantir um estado consistente
        modelo_cache["modelo"] = None
        modelo_cache["encoder"] = None
        modelo_cache["tfidf"] = None


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
        # A tarefa em segundo plano agora também atualiza o cache em memória de forma segura
        background_tasks.add_task(treinar_e_salvar_modelo, cache_para_atualizar=modelo_cache)
        return {"message": "Processo do treino do Modelo iniciado em segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# O endpoint de predição agora usa os modelos carregados do cache
@router.post("/predictions", response_model=dict)
async def get_prediction(livro_input: LivroBase):
    """Recebe os dados de um livro e retorna uma predição de rating (bom/ruim)."""
    
    # Utiliza o lock para garantir que o cache não seja modificado durante a leitura
    with modelo_cache["lock"]:
        if modelo_cache["modelo"] is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Modelo não está carregado. Treine o modelo ou verifique os logs do servidor."
            )
        
        try:
            # Prepara os dados de entrada usando a função auxiliar
            model = modelo_cache["modelo"]
            encoder = modelo_cache["encoder"]
            tfidf = modelo_cache["tfidf"]
            
            input_df_processed = preparar_input_para_predicao(
                livro_input,
                encoder,
                tfidf,
                model.feature_names_in_
            )
            # Faz a predição
            model = modelo_cache["modelo"]
            prediction = model.predict(input_df_processed)
            predicted_class = int(prediction[0])
        except Exception as e:
            # Captura e loga possíveis erros durante o pré-processamento ou predição
            logging.error(f"Erro ao processar predição para o livro '{livro_input.titulo}': {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Erro ao processar os dados de entrada: {e}")
    
    return {
        "livro": livro_input.titulo, 
        "rating_predito": predicted_class # Ex: 0 para 'ruim', 1 para 'bom'
    }
