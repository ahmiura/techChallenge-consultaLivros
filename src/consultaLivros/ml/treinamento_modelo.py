import pickle
import os
from datetime import datetime
from sqlalchemy.orm import Session
from .preparacao_dados import preparar_dados_livros
from ..db.database import SessionLocal
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression  # Importando um segundo modelo
from sklearn.svm import SVC  # Importando um terceiro modelo
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Importa o novo repositório para registrar os modelos
from ..repositorios import registro_modelos_repositorio

def treinar_e_salvar_modelos():
    """
    Busca dados, treina múltiplos modelos de classificação, avalia,
    registra os resultados no banco de dados e salva os artefatos versionados.
    """
    print("Iniciando o pipeline de treinamento de múltiplos modelos...")

    SEED = 42

    # --- 1. Definição dos Modelos a Treinar ---
    # Um dicionário para facilmente adicionar ou remover modelos do pipeline.
    modelos_a_treinar = {
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1, class_weight='balanced'),
        "regressao_logistica": LogisticRegression(random_state=SEED, class_weight='balanced', max_iter=1000),
        "svm": SVC(random_state=SEED, class_weight='balanced')
    }

    db = SessionLocal()
    try:
        # --- 2. Preparação dos Dados (Feita uma única vez) ---
        features_df, encoder, tfidf = preparar_dados_livros(db)

        if features_df.empty:
            raise ValueError("Nenhum dado de livro disponível para treinar o modelo.")

        features_df['bom_rating'] = features_df['rating'].apply(lambda x: 1 if x >= 4 else 0)
        X = features_df.drop(columns=['rating', 'bom_rating'])
        y = features_df['bom_rating']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
        print(f"Dados divididos: {len(X_train)} para treino, {len(X_test)} para teste.")

        # --- 3. Salvar Artefatos de Pré-processamento (Versionados) ---
        # Como são os mesmos para todos os modelos, salvamos uma vez antes do loop.
        modelo_dir = 'modelos_ml'
        os.makedirs(modelo_dir, exist_ok=True)
        versao_artefatos = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        caminho_encoder = os.path.join(modelo_dir, f'encoder_{versao_artefatos}.pkl')
        caminho_tfidf = os.path.join(modelo_dir, f'tfidf_{versao_artefatos}.pkl')

        with open(caminho_encoder, 'wb') as f:
            pickle.dump(encoder, f)
        with open(caminho_tfidf, 'wb') as f:
            pickle.dump(tfidf, f)
        
        # --- 4. Loop para Treinar, Avaliar e Registrar Cada Modelo ---
        for nome_modelo, modelo_instancia in modelos_a_treinar.items():
            print(f"\n--- Treinando modelo: {nome_modelo} ---")

            # Treinamento com dados de treino
            modelo_instancia.fit(X_train, y_train)

            # Avaliação com dados de teste
            predictions = modelo_instancia.predict(X_test)
            report_dict = classification_report(y_test, predictions, output_dict=True, zero_division=0)
            
            # Extrai as métricas que queremos salvar
            metricas = {
                "acuracia": report_dict["accuracy"],
                "f1_score_macro": report_dict["macro avg"]["f1-score"],
                "precisao_macro": report_dict["macro avg"]["precision"],
                "recall_macro": report_dict["macro avg"]["recall"]
            }
            print(f"Métricas para '{nome_modelo}': {metricas}")

            # Retreinamento com todos os dados para o modelo final
            modelo_instancia.fit(X, y)
            print(f"Modelo '{nome_modelo}' retreinado com todos os dados.")

            # Salvando o modelo versionado
            caminho_modelo = os.path.join(modelo_dir, f'modelo_{nome_modelo}_{versao_artefatos}.pkl')
            with open(caminho_modelo, 'wb') as f:
                pickle.dump(modelo_instancia, f)

            # Registrando no banco de dados
            caminhos = {
                "modelo": caminho_modelo,
                "encoder": caminho_encoder,
                "tfidf": caminho_tfidf
            }
            registro_modelos_repositorio.registrar_modelo(db, nome_modelo, versao_artefatos, caminhos, metricas)
            print(f"Modelo '{nome_modelo}' versão '{versao_artefatos}' registrado com sucesso no banco de dados.")

    except Exception as e:
        print(f"Erro durante o pipeline de treinamento: {e}")
        raise
    finally:
        db.close()
        print("\nPipeline de treinamento de múltiplos modelos finalizado.")

if __name__ == "__main__":
    treinar_e_salvar_modelos()