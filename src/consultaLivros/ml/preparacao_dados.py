import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy.orm import Session
from typing import Tuple, Optional
from ..schemas.livros import LivroBase
from ..repositorios import livros_repositorio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def preparar_dados_livros(db: Session) -> Tuple[pd.DataFrame, Optional[OneHotEncoder], Optional[TfidfVectorizer]]:
    """
    Busca os dados dos livros no banco, realiza o pré-processamento e retorna
    um DataFrame de features junto com os transformadores (encoder e TF-IDF).

    Args:
        db: A sessão do SQLAlchemy para consulta ao banco de dados.

    Returns:
        Uma tupla contendo:
        - features_df: DataFrame com todas as features prontas para o modelo.
        - encoder: O OneHotEncoder treinado.
        - tfidf: O TfidfVectorizer treinado.
        Retorna (pd.DataFrame(), None, None) se não houver livros ou em caso de erro.
    """
    try:
        # Acesso ao banco de dados agora é feito através do repositório
        df = livros_repositorio.busca_todos_livros_para_dataframe(db)

        if df.empty:
            logging.warning("Nenhum livro encontrado no banco de dados para preparação.")
            return pd.DataFrame(), None, None

        # Definir colunas para maior clareza e manutenibilidade
        colunas_numericas = ['preco', 'rating', 'disponibilidade']
        coluna_categorica = ['categoria']
        coluna_texto = 'titulo'

        # 1. Processar features numéricas
        features_numericas = df[colunas_numericas].copy()
        features_numericas['disponibilidade'] = features_numericas['disponibilidade'].astype(int)

        # 2. Codificar features categóricas
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        categorias_encoded = encoder.fit_transform(df[coluna_categorica])
        categorias_df = pd.DataFrame(
            categorias_encoded, columns=encoder.get_feature_names_out(coluna_categorica)
        )

        # 3. Vetorizar a feature de texto
        tfidf = TfidfVectorizer(max_features=200, stop_words='english', ngram_range=(1, 2))
        titulos_features = tfidf.fit_transform(df[coluna_texto])
        titulos_df = pd.DataFrame(titulos_features.toarray(), columns=tfidf.get_feature_names_out())

        # 4. Concatenar todas as features
        features_df = pd.concat([features_numericas, categorias_df, titulos_df], axis=1)

        logging.info(f"Dados preparados: {features_df.shape[0]} livros, {features_df.shape[1]} colunas.")

        return features_df, encoder, tfidf

    except Exception as e:
        logging.error(f"Erro inesperado ao preparar os dados dos livros: {e}", exc_info=True)
        # Retorna vazio em caso de erro para não quebrar o pipeline
        return pd.DataFrame(), None, None


def preparar_input_para_predicao(
    livro_input: LivroBase,
    encoder: OneHotEncoder,
    tfidf: TfidfVectorizer,
    colunas_modelo: list
) -> pd.DataFrame:
    """
    Prepara um único registro (livro) para predição usando os transformadores treinados.
    Garante que as colunas do input correspondam exatamente às do modelo.
    """
    input_df = pd.DataFrame([livro_input.model_dump()])

    # Extrai e transforma as features
    features_numericas = input_df[['preco', 'rating', 'disponibilidade']].copy()
    features_numericas['disponibilidade'] = features_numericas['disponibilidade'].astype(int)

    categorias_encoded = encoder.transform(input_df[['categoria']])
    categorias_df = pd.DataFrame(categorias_encoded, columns=encoder.get_feature_names_out(['categoria']))

    titulos_features = tfidf.transform(input_df['titulo'])
    titulos_df = pd.DataFrame(titulos_features.toarray(), columns=tfidf.get_feature_names_out())

    # Concatena e alinha as colunas com as do modelo treinado
    input_completo_df = pd.concat([features_numericas, categorias_df, titulos_df], axis=1)
    
    input_final_df = input_completo_df.reindex(columns=colunas_modelo, fill_value=0)
    
    return input_final_df
