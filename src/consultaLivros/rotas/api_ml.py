from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from ..ml.preparacao_dados import preparar_dados_livros, preparar_input_para_predicao
from ..ml.treinamento_modelo import treinar_e_salvar_modelos
from ..schemas.livros import LivroBase
import pickle
from ..db.database import get_db, SessionLocal
import pandas as pd
from typing import List, Dict, Any
import os
import logging
from threading import Lock
from ..repositorios import logs_predicoes_repositorio
from ..repositorios import registro_modelos_repositorio

# Constantes para os caminhos dos modelos, facilitando a manutenção
MODELOS_DIR = "modelos_ml"
CAMINHO_MODELO = os.path.join(MODELOS_DIR, 'modelo_livros.pkl')
CAMINHO_ENCODER = os.path.join(MODELOS_DIR, 'encoder_livros.pkl')
CAMINHO_TFIDF = os.path.join(MODELOS_DIR, 'tfidf_livros.pkl')

# Cache para armazenar o modelo e o encoder
modelo_cache: Dict[str, Any] = {
    "modelos": {},
    "artefatos": {},
    "lock": Lock()  # Adiciona um lock para garantir acesso thread-safe ao cache
}

def carregar_modelos_em_producao(db_session: Session | None = None):
    """Carrega todos os modelos marcados como 'em_producao' para o cache."""
    logging.info("Carregando modelos em produção para o cache...")
    db = db_session or SessionLocal()
    try:
        modelos_a_carregar = registro_modelos_repositorio.listar_modelos_em_producao(db)
        
        # Limpa o cache antes de carregar
        modelos_carregados = {}
        artefatos_carregados = {}

        for registro in modelos_a_carregar:
            # Carrega o modelo
            with open(registro.caminho_arquivo_modelo, 'rb') as f:
                modelos_carregados[registro.nome_modelo] = pickle.load(f)
            
            # Carrega os artefatos (encoder/tfidf), evitando duplicação
            versao_artefato = registro.versao
            if versao_artefato not in artefatos_carregados:
                with open(registro.caminho_arquivo_encoder, 'rb') as f:
                    encoder = pickle.load(f)
                with open(registro.caminho_arquivo_tfidf, 'rb') as f:
                    tfidf = pickle.load(f)
                artefatos_carregados[versao_artefato] = {"encoder": encoder, "tfidf": tfidf}

        with modelo_cache["lock"]:
            modelo_cache["modelos"] = modelos_carregados
            modelo_cache["artefatos"] = artefatos_carregados # Mapeia versão para seus artefatos
            # Precisamos de um link entre o modelo e seus artefatos, vamos simplificar por agora
            # Para uma solução mais robusta, o registro do modelo teria um FK para a versão do artefato
            # Por simplicidade, vamos assumir que todos os modelos em prod usam o mesmo conjunto de artefatos mais recente.
            if artefatos_carregados:
                 # Pega a última versão de artefatos carregada
                ultima_versao = sorted(artefatos_carregados.keys())[-1]
                modelo_cache["encoder_prod"] = artefatos_carregados[ultima_versao]["encoder"]
                modelo_cache["tfidf_prod"] = artefatos_carregados[ultima_versao]["tfidf"]


        logging.info(f"Carregados {len(modelos_carregados)} modelos em produção.")
    except FileNotFoundError as e:
        logging.error(f"Arquivo de modelo/artefato não encontrado: {e}. A predição pode falhar.")
        # Limpa o cache para garantir estado consistente
        with modelo_cache["lock"]:
            modelo_cache["modelos"] = {}
            modelo_cache["artefatos"] = {}

    except Exception as e:
        logging.error(f"Falha ao carregar modelos para o cache: {e}", exc_info=True)

    finally:
        if not db_session:
            db.close()


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
        background_tasks.add_task(treinar_e_salvar_modelos, cache_para_atualizar=modelo_cache)
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
    Recebe os dados de um livro e retorna uma predição usando um modelo específico.
    """
    with modelo_cache["lock"]:
        # Seleciona o modelo do cache
        modelo_selecionado = modelo_cache["modelos"].get(nome_modelo)

        if modelo_selecionado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Modelo '{nome_modelo}' não está carregado ou não existe."
            )
        
        # Pega os artefatos de produção (encoder e tfidf)
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

        # Loga a predição
        try:
            logs_predicoes_repositorio.cria_log_predicao(
                db=db, 
                livro_input=livro_input, 
                predicao=predicted_class
            )
        except Exception as log_e:
            # Loga um erro se a escrita no banco de logs falhar, mas não interrompe a resposta ao usuário.
            logging.error(f"Falha ao salvar o log da predição: {log_e}", exc_info=True)

    return {
        "livro": livro_input.titulo, 
        "modelo_usado": nome_modelo,
        "rating_predito": predicted_class
    }
      