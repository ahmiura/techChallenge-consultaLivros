import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy.orm import Session
from typing import Tuple, Optional
from ..modelos import livros as modelo_livros

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
        # Usar read_sql_query é mais direto e potencialmente mais eficiente em memória
        query = db.query(modelo_livros.Livro).statement
        df = pd.read_sql_query(query, db.bind)

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
        logging.error(f"Erro ao preparar os dados dos livros: {e}", exc_info=True)
        # Retorna vazio em caso de erro para não quebrar o pipeline
        return pd.DataFrame(), None, None