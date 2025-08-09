import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

st.set_page_config(layout="wide", page_title="Dashboard de Uso da API")

st.title("📊 Dashboard de Monitoramento da API de Livros")

# Carrega as variáveis de ambiente do arquivo .env (para desenvolvimento local)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

@st.cache_data(ttl=60)  # Adiciona cache para não consultar o DB a cada interação
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

# Carrega os dados
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