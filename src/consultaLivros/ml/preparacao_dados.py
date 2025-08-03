import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy.orm import Session
from ..repositorios.livros_repositorio import busca_todos_livros
from sklearn.feature_extraction.text import TfidfVectorizer

def preparar_dados_livros(db: Session):
    """Prepara os dados dos livros para o modelo de machine learning."""
    
    livros = busca_todos_livros(db)
    if not livros:
        print("Nenhum livro encontrado no banco de dados.")
        return pd.DataFrame(), None

    # Converte os livros em um DataFrame
    df = pd.DataFrame([livro.__dict__ for livro in livros])

    # Codifica as colunas categóricas usando OneHotEncoder
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    categorias_encoded = encoder.fit_transform(df[['categoria']])
    # Cria um DataFrame com as colunas codificadas
    categorias_df = pd.DataFrame(categorias_encoded, columns=encoder.get_feature_names_out(['categoria']))
    
    # Adiciona a coluna de texto (descrição) usando TF-IDF
    tfidf = TfidfVectorizer(
        max_features=200, # Aumente um pouco o número de features
        stop_words='english',
        ngram_range=(1, 2) # considera palavras sozinhas E pares de palavras
    )
    titulos_features = tfidf.fit_transform(df['titulo'])
    titulos_df = pd.DataFrame(titulos_features.toarray(), columns=tfidf.get_feature_names_out())

    # Seleciona as colunas numéricas originais
    features_numericas = df[['preco', 'rating', 'disponibilidade']].copy()
    features_numericas['disponibilidade'] = features_numericas['disponibilidade'].astype(int)

    # Concatena todas as features processadas em um único DataFrame
    features_df = pd.concat([features_numericas, categorias_df, titulos_df], axis=1)

    print(f"Dados preparados: {features_df.shape[0]} livros, {features_df.shape[1]} colunas.")
    
    return features_df, encoder, tfidf