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
def load_prediction_logs_from_db():
    """Carrega os logs de predição do banco de dados."""
    if not DATABASE_URL:
        # A função principal já mostra um erro, então aqui podemos retornar um DataFrame vazio
        return pd.DataFrame()
    try:
        engine = create_engine(DATABASE_URL)
        query = "SELECT timestamp, input_features, output_predicao FROM log_predicoes ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, engine)
        return df
    except Exception:
        # Se a tabela ainda não existir, apenas retorna um DF vazio
        return pd.DataFrame()


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


st.divider()
st.header("Monitoramento de Predições do Modelo de ML")

# Carrega os dados das predições
df_preds = load_prediction_logs_from_db()

if not df_preds.empty:
    df_preds['timestamp'] = pd.to_datetime(df_preds['timestamp'])

    # Mapeia a predição numérica para um texto mais claro
    df_preds['predicao_label'] = df_preds['output_predicao'].map({1: 'Bom Rating', 0: 'Ruim Rating'})

    st.subheader("Distribuição das Predições (Bom vs. Ruim Rating)")
    pred_counts = df_preds['predicao_label'].value_counts()
    st.bar_chart(pred_counts)

    st.subheader("Predições ao Longo do Tempo")
    # Agrupa por dia e conta as ocorrências de cada predição
    preds_over_time = df_preds.set_index('timestamp').resample('D')['predicao_label'].value_counts().unstack(fill_value=0)
    st.line_chart(preds_over_time)

    with st.expander("Ver Logs de Predições Brutos"):
        st.dataframe(df_preds)
else:
    st.warning("Nenhum dado de log de predição para exibir.")



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