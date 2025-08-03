import pickle
import os
from .preparacao_dados import preparar_dados_livros
from ..db.database import SessionLocal
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


def treinar_e_salvar_modelo():
    """
    Busca dados, divide em treino/teste, avalia o modelo e,
    finalmente, retreina com todos os dados e salva os artefatos.
    """
    print("Iniciando o treinamento do modelo de machine learning...")

    SEED = 42

    # Obtendo dados do banco de dados
    db = SessionLocal()
    try:
        # Prepara os dados dos livros
        features_df, encoder, tfidf = preparar_dados_livros(db)
    finally:
        db.close()

    if features_df.empty:
        raise ValueError("Nenhum dado de livro disponível para treinar o modelo.")

    # Adiciona uma coluna de classificação binária para rating
    # Considera rating >= 4 como 'bom' (1) e < 4 como 'ruim' (0)
    features_df['bom_rating'] = features_df['rating'].apply(lambda x: 1 if x >= 4 else 0)


    # Treina o modelo 
    X = features_df.drop(columns=['rating', 'bom_rating'])
    y = features_df['bom_rating']

    # Divisão dos dados em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
    print(f"Dados divididos: {len(X_train)} para treino, {len(X_test)} para teste.")

    # Treinamento do modelo
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=SEED,
        n_jobs=-1
    )

    model.fit(X_train, y_train)
    print("Modelo treinado com sucesso.")

    # Avaliação do modelo
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    print(f"Acurácia: {accuracy:.2%}")
    print("\nRelatório de Classificação:")
    print(classification_report(y_test, predictions, zero_division=0))

    # Salva o modelo e o encoder em arquivos
    modelo_dir = 'modelos_ml'
    os.makedirs(modelo_dir, exist_ok=True)

    caminho_modelo = os.path.join(modelo_dir, 'modelo_livros.pkl')
    caminho_encoder = os.path.join(modelo_dir, 'encoder_livros.pkl')
    caminho_tfidf = os.path.join(modelo_dir, 'tfidf_livros.pkl') 

    # Salvando o modelo e o encoder
    with open(caminho_modelo, 'wb') as model_file:
        pickle.dump(model, model_file)
    
    with open(caminho_encoder, 'wb') as encoder_file:
        pickle.dump(encoder, encoder_file)
    
    with open(caminho_tfidf, 'wb') as f:
        pickle.dump(tfidf, f)

    print("Modelo treinado e salvo com sucesso.")
    return {"status": "sucesso", "modelo": caminho_modelo, "encoder": caminho_encoder}


if __name__ == "__main__":
    try:
        treinar_e_salvar_modelo()
    except Exception as e:
        print(f"Erro ao treinar o modelo: {e}")
        raise e 
