import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from github import Github
import io

st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CSS para o design
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .stApp { background-color: #f8f9fa; }
    div[data-baseweb="tab-list"] { justify-content: center; gap: 8px; }
    button[data-baseweb="tab"] { background-color: transparent !important; border-radius: 8px !important; border: 1px solid #e2e8f0 !important; }
    button[aria-selected="true"] { background-color: #e2e8f0 !important; color: #1e293b !important; border: 1px solid #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("### 🍗 Acesso Restrito - RotiFácil")
        u = st.text_input("👤 Usuário")
        s = st.text_input("🔑 Senha", type="password")
        if st.button("Entrar", type="primary"):
            if u.lower() in ["hadassa", "thiago", "mariana", "geyzzon"]:
                st.session_state['logado'] = True
                st.session_state['usuario_logado'] = u.strip().title()
                st.rerun()
            else: st.error("❌ Usuário ou senha incorretos.")
    st.stop()

META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925
PRECIFICACAO_REAL = {"ARROZ C/ CREME FRANGO KG": [16.39, 39.99], "PANQUECA CARNE MOIDA KG": [12.16, 29.99]}

@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except: return pd.DataFrame()

col_logo, _, col_filial, col_data = st.columns([2, 0.5, 1.5, 2])
with col_logo:
    st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=250)
    if st.button("Sair (Logout)"): st.session_state['logado'] = False; st.rerun()

unidade = col_filial.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
datas_sel = col_data.date_input("📅 Selecione o Período:", value=(datetime.today().date().replace(day=1), datetime.today().date()))
st.divider()

arquivo_vendas = "vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv"
arquivo_avarias = "avarias_filial2.csv" if "Filial 2" in unidade else "avarias_filial5.csv"
df_base = carregar(arquivo_vendas)

if not df_base.empty and len(datas_sel) == 2:
    ini, fim = datas_sel
    df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
    fat_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
    
    st.subheader(f"🎯 Performance: R$ {fat_periodo:,.2f}")
    
    tabs = st.tabs(["📈 Margem Real", "📊 Visão Diária", "🔥 Picos", "🏆 ABC", "🗑️ Avaria"])
    
    with tabs[0]:
        v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
        st.dataframe(v_prod, use_container_width=True)
    with tabs[1]:
        df_filt['Val'] = df_filt['Valor_Final']
        tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns=df_filt['Data_Ref'].dt.strftime('%d/%m'), aggfunc='sum', fill_value=0)
        st.dataframe(tab, use_container_width=True)
    with tabs[4]:
        st.subheader("Controle de Avarias")
        # (Sua lógica de avarias aqui)
else:
    st.info("Selecione um período.")
