import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import requests

st.set_page_config(layout="wide", page_title="Dashboard de Uso da API")
st.title("📊 Dashboard de Monitoramento da API de Livros")

# Carrega as variáveis de ambiente do arquivo .env (para desenvolvimento local)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("API_URL")

@st.cache_data(ttl=60)  # Adiciona cache para não consultar o DB a cada interação
def carregar_status_do_cache():
    """Busca o estado atual do cache de modelos da API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/ml/cache-status")
        response.raise_for_status()  # Lança um erro para status code >= 400
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Não foi possível conectar à API para buscar o status do cache: {e}")
        return None


def load_logs_from_db():
    """Carrega os logs do banco de dados e os converte em um DataFrame."""
    if not DATABASE_URL:
        st.error("A variável de ambiente DATABASE_URL não está configurada.")
        return pd.DataFrame()

    try:
        engine = create_engine(DATABASE_URL)
        # Uma query simples é suficiente para o dashboard
        query = "SELECT timestamp, method, path, status_code, process_time_ms FROM log_requests ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ou buscar dados do banco: {e}")
        return pd.DataFrame()


# --- Monitoramento de Modelos (Lendo do Cache da API) ---
st.header("🤖 Monitoramento de Modelos em Memória")

cache_info = carregar_status_do_cache()

if cache_info and cache_info.get("detalhes_modelos"):
    # Converte os detalhes dos modelos em um DataFrame
    df_modelos = pd.DataFrame(cache_info["detalhes_modelos"])
    
    # Expande a coluna de métricas (que é um dicionário) em múltiplas colunas
    metricas_df = pd.json_normalize(df_modelos['metricas'])
    df_modelos_vis = pd.concat([df_modelos.drop('metricas', axis=1), metricas_df], axis=1)

    st.subheader("Leaderboard de Modelos em Cache")
    st.dataframe(
        df_modelos_vis.style.format({
            'acuracia': '{:.2%}',
            'f1_score_macro': '{:.3f}',
            'precisao_macro': '{:.3f}',
            'recall_macro': '{:.3f}'
        })
    )

    st.subheader("Comparativo de Performance (F1-Score)")
    # Garante que a coluna existe antes de tentar plotar
    if 'f1_score_macro' in df_modelos_vis.columns:
        chart_data = df_modelos_vis[['nome', 'f1_score_macro']].set_index('nome')
        st.bar_chart(chart_data)
    else:
        st.warning("Métricas de F1-Score não disponíveis.")

else:
    st.info("Nenhum modelo treinado encontrado no cache da API. Dispare o treinamento na rota /train.")


st.divider()

# Carrega os dados das requisicoes
df = load_logs_from_db()

if not df.empty:
    # Converte o timestamp para o formato datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # --- Métricas Principais ---
    st.header("Métricas Gerais")
    total_requests = len(df)
    avg_latency = df['process_time_ms'].mean()
    error_rate = (df['status_code'] >= 500).sum() / total_requests * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Requisições", f"{total_requests}")
    col2.metric("Latência Média (ms)", f"{avg_latency:.2f}")
    col3.metric("Taxa de Erros (5xx)", f"{error_rate:.2f}%")

    st.divider()

    # --- Visualizações ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.header("Requisições por Endpoint")
        requests_by_path = df['path'].value_counts()
        st.bar_chart(requests_by_path)

    with col_b:
        st.header("Distribuição de Status Code")
        status_code_counts = df['status_code'].value_counts()
        st.bar_chart(status_code_counts)

    st.header("Latência ao Longo do Tempo")
    # Agrupa por minuto para não poluir o gráfico
    latency_over_time = df.set_index('timestamp').resample('T')['process_time_ms'].mean()
    st.line_chart(latency_over_time)

    # --- Logs Brutos ---
    with st.expander("Ver Logs Brutos"):
        st.dataframe(df.sort_values('timestamp', ascending=False))

else:
    st.warning("Nenhum dado de log para exibir.")