import streamlit as st
import pandas as pd
import json

LOG_FILE = "api_requests.log"

st.set_page_config(layout="wide", page_title="Dashboard de Uso da API")

st.title("📊 Dashboard de Monitoramento da API de Livros")

def load_logs():
    """Carrega os logs do arquivo e os converte em um DataFrame do Pandas."""
    logs = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    # Ignora linhas mal formatadas
                    pass
    except FileNotFoundError:
        st.error(f"Arquivo de log '{LOG_FILE}' não encontrado. A API já foi executada?")
        return pd.DataFrame()
        
    return pd.DataFrame(logs)

# Carrega os dados
df = load_logs()

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