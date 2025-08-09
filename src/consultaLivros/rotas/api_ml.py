from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from ..ml.preparacao_dados import preparar_dados_livros
from ..ml.treinamento_modelo import treinar_e_salvar_modelo
from ..schemas.livros import LivroBase
import pickle
from ..db.database import get_db
import pandas as pd
from typing import List
import os   


# Cache para armazenar o modelo e o encoder
modelo_cache = {
    "modelo": None,
    "encoder": None,
    "tfidf": None
}

def carregar_modelo_e_encoder():
    """
    Carrega o modelo, o encoder e o vetorizador TF-IDF do disco para o cache.
    Levanta um FileNotFoundError se algum arquivo não for encontrado.
    Esta função é chamada na inicialização da aplicação (lifespan).
    """
    modelos_dir = "modelos_ml"
    caminho_modelo = os.path.join(modelos_dir, 'modelo_livros.pkl')
    caminho_encoder = os.path.join(modelos_dir, 'encoder_livros.pkl')
    caminho_tfidf = os.path.join(modelos_dir, 'tfidf_livros.pkl')

    print("Carregando modelo e encoder...")
    try:
        with open(caminho_modelo, 'rb') as model_file:
            modelo_cache["modelo"] = pickle.load(model_file)
        with open(caminho_encoder, 'rb') as encoder_file:
            modelo_cache["encoder"] = pickle.load(encoder_file)
        with open(caminho_tfidf, 'rb') as tfidf_file:
            modelo_cache["tfidf"] = pickle.load(tfidf_file)

        print("Modelo e encoder carregados com sucesso.")
    except FileNotFoundError:
        print("Modelo ou encoder não encontrados. Certifique-se de que foram treinados e salvos corretamente.")
        # Limpa o cache para garantir um estado consistente
        modelo_cache["modelo"] = None
        modelo_cache["encoder"] = None
        modelo_cache["tfidf"] = None


def _preparar_input_para_predicao(livro_input: LivroBase, cache: dict) -> pd.DataFrame:
    """
    Prepara o DataFrame de entrada para a predição usando os artefatos em cache.
    """
    input_df = pd.DataFrame([livro_input.model_dump()])

    # Extrai e transforma as features
    features_numericas = input_df[['preco', 'rating', 'disponibilidade']].copy()
    features_numericas['disponibilidade'] = features_numericas['disponibilidade'].astype(int)

    encoder = cache["encoder"]
    categorias_encoded = encoder.transform(input_df[['categoria']])
    categorias_df = pd.DataFrame(categorias_encoded, columns=encoder.get_feature_names_out(['categoria']))

    tfidf = cache["tfidf"]
    titulos_features = tfidf.transform(input_df['titulo'])
    titulos_df = pd.DataFrame(titulos_features.toarray(), columns=tfidf.get_feature_names_out())

    # Concatena e alinha as colunas com as do modelo treinado
    input_completo_df = pd.concat([features_numericas, categorias_df, titulos_df], axis=1)
    
    modelo = cache["modelo"]
    colunas_modelo = modelo.feature_names_in_
    input_final_df = input_completo_df.reindex(columns=colunas_modelo, fill_value=0)
    
    return input_final_df

router = APIRouter(
    prefix="/api/v1/ml",
    tags=["machine_learning"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Não encontrado"}},
)


@router.get("/features", response_model=List[dict])
async def get_features(db: Session = Depends(get_db)):
    """Retorna os dados dos livros formatados como features para ML."""
    features_df, encoder, tfidf = preparar_dados_livros(db)
    if features_df.empty:
        return []
    
    # Remove a coluna de rating para retornar apenas as features
    features_only_df = features_df.drop(columns=['rating'])
    return features_only_df.to_dict(orient='records')


@router.get("/training-data", response_model=List[dict])
async def get_training_data(db: Session = Depends(get_db)):
    """Retorna o dataset completo (features + target) usado para treinamento."""
    features_df, encoder, tfidf = preparar_dados_livros(db)
    if features_df.empty:
        return []
    # O 'preco' é o nosso target (alvo)
    return features_df.to_dict(orient='records')


@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
async def train_model(background_tasks: BackgroundTasks):
    """Treina o modelo de machine learning e salva os artefatos."""
    try:
        # A tarefa em segundo plano agora também atualiza o cache em memória
        background_tasks.add_task(treinar_e_salvar_modelo, cache_para_atualizar=modelo_cache)
        return {"message": "Processo do treino do Modelo iniciado em segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# O endpoint de predição agora usa os modelos carregados do cache
@router.post("/predictions", response_model=dict)
async def get_prediction(livro_input: LivroBase):
    """Recebe os dados de um livro e retorna uma predição de rating (bom/ruim)."""

    if modelo_cache["modelo"] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Modelo não está carregado. Treine o modelo ou verifique os logs do servidor."
        )
    
    try:
        # Prepara os dados de entrada usando a função auxiliar
        input_df_processed = _preparar_input_para_predicao(livro_input, modelo_cache)
        
        # Faz a predição
        model = modelo_cache["modelo"]
        prediction = model.predict(input_df_processed)
        predicted_class = int(prediction[0])
    except Exception as e:
        # Captura possíveis erros durante o pré-processamento ou predição
        raise HTTPException(status_code=400, detail=f"Erro ao processar os dados de entrada: {e}")
    
    return {
        "livro": livro_input.titulo, 
        "rating_predito": predicted_class # Ex: 0 para 'ruim', 1 para 'bom'
    }
