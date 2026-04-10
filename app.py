import streamlit as st
import pandas as pd
from datetime import timedelta
import time

st.set_page_config(page_title="RotiVision", layout="wide", page_icon="🍗")

st.sidebar.title("🏢 Unidade")
unidade = st.sidebar.selectbox("Escolha a Loja:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

@st.cache_data(ttl=60)
def carregar_dados(loja):
    # Seleção de arquivo limpa e sem erro
    arq = "vendas_filial2.csv" if "Filial 2" in loja else "vendas_filial5.csv"
    url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
    return pd.read_csv(url)

try:
    df_base = carregar_dados(unidade)
    df_base['Data_Ref'] = pd.to_datetime(df_base['Data'])
    df_base['Data_Date'] = df_base['Data_Ref'].dt.date
    
    st.title(f"🍗 {unidade}")

    # --- LÓGICA DE CARDS ---
    data_max = df_base['Data_Date'].max()
    df_mes = df_base[df_base['Data_Date'] >= data_max.replace(day=1)]
    
    def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if "Filial 2" in unidade:
        # Venda Local (Tira o 6613) | Venda Planalto (Só o 6613)
        v_local = df_base[(df_base['CODOPER'] == 'S') & (df_base['CODCLI'] != 6613)]['Valor_Final'].sum()
        v_plan = df_base[(df_base['CODOPER'] == 'S') & (df_base['CODCLI'] == 6613)]['Valor_Final'].sum()
        acum_mes = df_mes[df_mes['CODOPER'] == 'S']['Valor_Final'].sum() - df_mes[df_mes['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🛒 VENDA LOCAL", fmt(v_local))
        c2.metric("🏪 VENDA PLANALTO", fmt(v_plan))
        c3.metric("📊 TOTAL PERÍODO", fmt(v_local + v_plan))
        c4.metric("💰 ACUMULADO MÊS", fmt(acum_mes))
    else:
        # Filial 5 simplificada
        v_bruta = df_base[df_base['CODOPER'] == 'S']['Valor_Final'].sum()
        acum_mes = df_mes[df_mes['CODOPER'] == 'S']['Valor_Final'].sum() - df_mes[df_mes['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("🛒 VENDA BRUTA", fmt(v_bruta))
        c2.metric("💰 ACUMULADO MÊS", fmt(acum_mes))
        c3.metric("📅 ATUALIZAÇÃO", data_max.strftime('%d/%m'))

    # ... (Restante do código de abas e tabela permanece igual) ...
    st.info("Utilize as abas abaixo para detalhes de produtos e Curva ABC.")

except Exception as e:
    st.warning(f"Aguardando dados da {unidade}... Certifique-se de que o robô já enviou o arquivo.")