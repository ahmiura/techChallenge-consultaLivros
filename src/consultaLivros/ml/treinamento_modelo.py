import pickle
import os
from .preparacao_dados import preparar_dados_livros
from ..db.database import SessionLocal
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from joblib import Parallel, delayed
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _treinar_um_modelo(nome_modelo: str, modelo_instancia: Any, X_train, y_train, X_test, y_test, X, y) -> tuple[str, Any, Dict]:
    """
    Função auxiliar para treinar, avaliar e registrar um único modelo.
    Retorna o nome do modelo e a instância final treinada.
    """
    logging.info(f"--- Processando modelo: {nome_modelo} ---")

    # Treinamento e avaliação
    modelo_instancia.fit(X_train, y_train)
    predictions = modelo_instancia.predict(X_test)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    logging.info(f"Acurácia para '{nome_modelo}': {report['accuracy']:.2%}")

    report_dict = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    metricas = {
        "acuracia": report_dict["accuracy"],
        "f1_score_macro": report_dict["macro avg"]["f1-score"]
    }
    logging.info(f"Métricas para '{nome_modelo}': {metricas}")

    # Retreinamento com todos os dados para o modelo final
    logging.info(f"Retreinando '{nome_modelo}' com todos os dados...")
    modelo_instancia.fit(X, y)
    
    return nome_modelo, modelo_instancia, metricas


def treinar_e_carregar_modelos_em_cache(cache: Dict[str, Any]):
    """
    Busca dados, treina múltiplos modelos em paralelo e os carrega diretamente
    em um dicionário de cache em memória, além de salvar os artefatos em disco.
    """
    logging.info("Iniciando pipeline de treinamento para atualização do cache...")
    SEED = 42

    db = SessionLocal()
    try:
        # 1. Preparação dos Dados (feita uma única vez)
        features_df, encoder, tfidf = preparar_dados_livros(db)

        if features_df.empty:
            logging.warning("Nenhum dado para treinamento. O cache não será atualizado.")
            return

        features_df['bom_rating'] = features_df['rating'].apply(lambda x: 1 if x >= 4 else 0)
        X = features_df.drop(columns=['rating', 'bom_rating'])
        y = features_df['bom_rating']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)

        # 2. Definição dos Modelos a Treinar
        modelos_a_treinar = {
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=1, class_weight='balanced'),
            "regressao_logistica": LogisticRegression(random_state=SEED, class_weight='balanced', max_iter=1000),
            "svm": SVC(random_state=SEED, class_weight='balanced')
        }
        
        # 3. Execução do Treinamento em Paralelo
        logging.info("Iniciando treinamento paralelo dos modelos...")
        resultados = Parallel(n_jobs=-1)(
            delayed(_treinar_um_modelo)(nome, modelo, X_train, y_train, X_test, y_test, X, y)
            for nome, modelo in modelos_a_treinar.items()
        )

        # 4. Coleta dos modelos treinados e atualização do cache
        modelos_treinados = {nome: modelo for nome, modelo, metricas in resultados}
        metricas_treinamento = {nome: metricas for nome, modelo, metricas in resultados}
        
        with cache["lock"]:
            cache["modelos"] = modelos_treinados
            cache["metricas"] = metricas_treinamento
            cache["encoder_prod"] = encoder
            cache["tfidf_prod"] = tfidf
            logging.info(f"Cache atualizado com {len(modelos_treinados)} novos modelos.")

        # 5. (Opcional) Salvar os artefatos em disco para persistência entre reinicializações
        modelo_dir = 'modelos_ml'
        os.makedirs(modelo_dir, exist_ok=True)
        
        for nome_modelo, modelo_instancia in modelos_treinados.items():
            with open(os.path.join(modelo_dir, f'modelo_{nome_modelo}.pkl'), 'wb') as f:
                pickle.dump(modelo_instancia, f)

        with open(os.path.join(modelo_dir, 'encoder.pkl'), 'wb') as f:
            pickle.dump(encoder, f)
        with open(os.path.join(modelo_dir, 'tfidf.pkl'), 'wb') as f:
            pickle.dump(tfidf, f)
        
        logging.info(f"Artefatos salvos com sucesso na pasta '{modelo_dir}'.")

    except Exception as e:
        logging.error(f"Falha crítica durante o pipeline de treinamento: {e}", exc_info=True)
    finally:
        db.close()
        logging.info("\nPipeline de treinamento de múltiplos modelos finalizado.")


if __name__ == "__main__":
    treinar_e_carregar_modelos_em_cache()