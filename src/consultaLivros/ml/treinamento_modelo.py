import pickle
import os
from datetime import datetime
from sqlalchemy.orm import Session
from .preparacao_dados import preparar_dados_livros
from ..db.database import SessionLocal
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from joblib import Parallel, delayed

# Importa o novo repositório para registrar os modelos
from ..repositorios import registro_modelos_repositorio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _treinar_um_modelo(nome_modelo, modelo_instancia, X_train, y_train, X_test, y_test, X, y, versao_artefatos, caminhos_artefatos):
    """
    Função auxiliar para treinar, avaliar e registrar um único modelo.
    Projetada para ser executada em um processo paralelo.
    """
    # Cada processo paralelo cria sua própria sessão de DB para garantir a segurança.
    db = SessionLocal()
    try:
        logging.info(f"--- Processando modelo: {nome_modelo} ---")

        # Treinamento com dados de treino
        modelo_instancia.fit(X_train, y_train)

        # Avaliação com dados de teste
        predictions = modelo_instancia.predict(X_test)
        report_dict = classification_report(y_test, predictions, output_dict=True, zero_division=0)
        
        metricas = {
            "acuracia": report_dict["accuracy"],
            "f1_score_macro": report_dict["macro avg"]["f1-score"],
            "precisao_macro": report_dict["macro avg"]["precision"],
            "recall_macro": report_dict["macro avg"]["recall"]
        }
        logging.info(f"Métricas para '{nome_modelo}': {metricas}")

        # Retreinamento com todos os dados para o modelo final
        logging.info(f"Retreinando '{nome_modelo}' com todos os dados...")
        modelo_instancia.fit(X, y)

        # Salvando o modelo versionado
        modelo_dir = 'modelos_ml'
        caminho_modelo = os.path.join(modelo_dir, f'modelo_{nome_modelo}_{versao_artefatos}.pkl')
        with open(caminho_modelo, 'wb') as f:
            pickle.dump(modelo_instancia, f)

        # Registrando no banco de dados
        caminhos = {
            "modelo": caminho_modelo,
            "encoder": caminhos_artefatos["encoder"],
            "tfidf": caminhos_artefatos["tfidf"]
        }
        registro_modelos_repositorio.registrar_modelo(db, nome_modelo, versao_artefatos, caminhos, metricas)
        logging.info(f"Modelo '{nome_modelo}' versão '{versao_artefatos}' registrado com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Erro ao processar o modelo {nome_modelo}: {e}", exc_info=True)
        return False
    finally:
        db.close()


def treinar_e_salvar_modelos():
    """
    Busca dados, treina múltiplos modelos de classificação EM PARALELO, avalia,
    registra os resultados no banco de dados e salva os artefatos versionados.
    """
    logging.info("Iniciando o pipeline de treinamento de múltiplos modelos...")
    SEED = 42
    db = SessionLocal()
    try:
        # --- 1. Preparação dos Dados (Feita uma única vez) ---
        features_df, encoder, tfidf = preparar_dados_livros(db)

        if features_df.empty:
            raise ValueError("Nenhum dado de livro disponível para treinar o modelo.")

        features_df['bom_rating'] = features_df['rating'].apply(lambda x: 1 if x >= 4 else 0)
        X = features_df.drop(columns=['rating', 'bom_rating'])
        y = features_df['bom_rating']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
        logging.info(f"Dados divididos: {len(X_train)} para treino, {len(X_test)} para teste.")

        # --- 2. Salvar Artefatos de Pré-processamento (Versionados) ---
        modelo_dir = 'modelos_ml'
        os.makedirs(modelo_dir, exist_ok=True)
        versao_artefatos = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        caminho_encoder = os.path.join(modelo_dir, f'encoder_{versao_artefatos}.pkl')
        caminho_tfidf = os.path.join(modelo_dir, f'tfidf_{versao_artefatos}.pkl')

        with open(caminho_encoder, 'wb') as f: pickle.dump(encoder, f)
        with open(caminho_tfidf, 'wb') as f: pickle.dump(tfidf, f)
        
        caminhos_artefatos = {"encoder": caminho_encoder, "tfidf": caminho_tfidf}

        # --- 3. Definição dos Modelos a Treinar ---
        modelos_a_treinar = {
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=1, class_weight='balanced'),
            "regressao_logistica": LogisticRegression(random_state=SEED, class_weight='balanced', max_iter=1000),
            "svm": SVC(random_state=SEED, class_weight='balanced')
        }
        
        # --- 4. Execução do Treinamento em Paralelo ---
        logging.info("Iniciando treinamento paralelo dos modelos...")
        resultados = Parallel(n_jobs=-1, backend="multiprocessing")(
            delayed(_treinar_um_modelo)(
                nome, modelo, X_train, y_train, X_test, y_test, X, y, versao_artefatos, caminhos_artefatos
            ) for nome, modelo in modelos_a_treinar.items()
        )
        
        if all(resultados):
            logging.info("Todos os modelos foram processados com sucesso.")
        else:
            logging.warning("Alguns modelos falharam durante o processamento. Verifique os logs de erro.")

    except Exception as e:
        logging.error(f"Erro crítico durante o pipeline de treinamento: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logging.info("\nPipeline de treinamento de múltiplos modelos finalizado.")

if __name__ == "__main__":
    treinar_e_salvar_modelos()