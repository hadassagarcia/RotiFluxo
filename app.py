import streamlit as st
import pandas as pd
from datetime import datetime
import time
from github import Github
import io

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# --- ESTILIZAÇÃO CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .block-container { 
        background-color: white !important; border-radius: 24px !important; 
        padding: 40px 60px !important; margin: 40px auto !important; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.05); max-width: 95% !important;
    }
    [data-testid="metric-container"] {
        background: #ffffff; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { justify-content: center; gap: 10px; }
    div[data-testid="stTabs"] button {
        border-radius: 12px !important; background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important; padding: 10px 20px !important; font-weight: 600 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] { background: #c92a2a !important; color: white !important; }
    h1, h2, h3 { color: #1e293b !important; font-family: 'Inter', sans-serif !important; }
    </style>
""", unsafe_allow_html=True)

# 🔐 LOGIN
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("### 🍗 Acesso Restrito - RotiFácil")
        usuario = st.text_input("👤 Usuário")
        senha = st.text_input("🔑 Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            if usuario.strip().lower() in ["hadassa", "thiago", "mariana", "geyzzon"]:
                st.session_state['logado'] = True
                st.session_state['usuario_logado'] = usuario.strip().title()
                st.rerun()
            else: st.error("❌ Usuário ou senha incorretos.")
    st.stop()

# CONSTANTES
META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925
PRECIFICACAO_REAL = {
    "ARROZ C/ CREME FRANGO KG": [16.39, 39.99], "PANQUECA CARNE MOIDA KG": [12.16, 29.99],
    "PANQUECA FRANGO KG": [14.23, 29.99], "ARROZ CREMOSO FRANGO KG": [16.44, 43.99]
}

@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except Exception as e:
        st.error(f"🚨 Erro ao ler {arq}: {e}")
        return pd.DataFrame()

# CABEÇALHO
col_logo, _, col_filial, col_data = st.columns([2, 0.5, 1.5, 2])
with col_logo:
    st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=200)
    if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

unidade = col_filial.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
datas_sel = col_data.date_input("📅 Período:", value=(datetime.today().date().replace(day=1), datetime.today().date()))
st.divider()

# LÓGICA E DASHBOARD
arquivo_vendas = "vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv"
arquivo_avarias = "avarias_filial2.csv" if "Filial 2" in unidade else "avarias_filial5.csv"
df_base = carregar(arquivo_vendas)

try:
    repo = Github(st.secrets["token_github"]).get_repo("hadassagarcia/RotiFluxo")
    df_avarias = pd.read_csv(io.StringIO(repo.get_contents(arquivo_avarias).decoded_content.decode('utf-8')))
except: df_avarias = pd.DataFrame()

if not df_base.empty and len(datas_sel) == 2:
    ini, fim = datas_sel
    df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
    
    fat_atual = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
    ini_ant = (pd.to_datetime(ini) - pd.DateOffset(months=1)).date()
    fim_ant = (pd.to_datetime(fim) - pd.DateOffset(months=1)).date()
    fat_ant = df_base[(df_base['Data_Date'] >= ini_ant) & (df_base['Data_Date'] <= fim_ant) & (df_base['CODOPER'] == 'S')]['Valor_Final'].sum()
    dif = fat_atual - fat_ant
    
    # METRICAS
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento Atual", f"R$ {fat_atual:,.2f}", f"{'+' if dif>=0 else ''}{dif:,.2f} vs mês anterior")
    c2.metric("📅 Referência Anterior", f"{ini_ant.strftime('%d/%m')} - {fim_ant.strftime('%d/%m')}", "Período Base")
    c3.metric("🚀 Meta", f"{min(fat_atual/META_FATURAMENTO, 1.0)*100:.1f}%", f"Falta R$ {max(0, META_FATURAMENTO - fat_atual):,.2f}")

    # ABAS
    tabs = st.tabs(["📈 Margem", "📊 Vendas", "🔥 Picos", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"])
    
    with tabs[0]:
        st.subheader("Margem Real")
        v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
        st.dataframe(v_prod, use_container_width=True)
    with tabs[1]:
        st.subheader("Visão Diária")
        st.dataframe(pd.pivot_table(df_filt, values='Valor_Final', index='Produto', columns=df_filt['Data_Ref'].dt.strftime('%d/%m'), aggfunc='sum', fill_value=0), use_container_width=True)
    with tabs[2]:
        if 'Hora' in df_filt.columns: st.bar_chart(df_filt[df_filt['CODOPER'] == 'S'].groupby('Hora')['Valor_Final'].sum())
    with tabs[3]:
        st.table(df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().sort_values(ascending=False))
    with tabs[5]:
        st.subheader("Controle de Avarias")
        if not df_avarias.empty:
            df_avarias['Data'] = pd.to_datetime(df_avarias['Data']).dt.date
            st.dataframe(df_avarias[(df_avarias['Data'] >= ini) & (df_avarias['Data'] <= fim)], use_container_width=True)
else:
    st.info("Selecione um período.")
