import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from github import Github
import io

# 1. CONFIGURAÇÃO - Layout Wide
st.set_page_config(page_title="RotiFácil Pro", layout="wide", page_icon="🍗")

# --- DESIGN SYSTEM PROFISSIONAL (CSS) ---
st.markdown("""
    <style>
    /* Fundo do App */
    .stApp { background-color: #f8fafc; }

    /* A "Caixa Mestre" que você queria */
    .main-dashboard {
        background: #ffffff;
        border-radius: 24px;
        padding: 40px;
        margin: 20px auto;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        max-width: 1200px;
    }

    /* Cards de Métricas (estilo Donezo) */
    .card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    
    /* Abas como botões modernos */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { justify-content: center; gap: 15px; }
    div[data-testid="stTabs"] button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        background: #f1f5f9 !important;
        border: none !important;
        padding: 10px 25px !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: #0f172a !important; /* Cor sólida profissional */
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Início do contêiner mestre
st.markdown('<div class="main-dashboard">', unsafe_allow_html=True)

# --- SEU CÓDIGO DE LÓGICA E DADOS ---
# [AQUI VOCÊ MANTÉM SEU CÓDIGO DE LOGIN, CARGA DE DADOS E FILTROS...]

# --- DASHBOARD PROFISSIONAL ---
# Exemplo de como usar os novos cartões de métrica
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('''<div class="card">
        <p style="color: #64748b; font-size: 14px; margin:0;">Faturamento Atual</p>
        <p style="font-size: 28px; font-weight: 800; margin:0;">R$ 10.648,31</p>
    </div>''', unsafe_allow_html=True)

# [AQUI VOCÊ SEGUE COM SUAS ABAS ABAIXO]
# tabs = st.tabs(["📈 Margem", "📊 Vendas", ...])

# Fechamento do contêiner mestre
st.markdown('</div>', unsafe_allow_html=True)

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
PRECIFICACAO_REAL = { "ARROZ C/ CREME FRANGO KG": [16.39, 39.99], "PANQUECA CARNE MOIDA KG": [12.16, 29.99], "PANQUECA FRANGO KG": [14.23, 29.99] }

@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except: return pd.DataFrame()

# CABEÇALHO
col_logo, _, col_filial, col_data = st.columns([2, 0.5, 1.5, 2])
with col_logo:
    st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=200)
    if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

unidade = col_filial.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
datas_sel = col_data.date_input("📅 Período:", value=(datetime.today().date().replace(day=1), datetime.today().date()))
st.divider()

# DADOS
arquivo_vendas = "vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv"
arquivo_avarias = "avarias_filial2.csv" if "Filial 2" in unidade else "avarias_filial5.csv"
df_base = carregar(arquivo_vendas)
try:
    repo = Github(st.secrets["token_github"]).get_repo("hadassagarcia/RotiFluxo")
    df_avarias = pd.read_csv(io.StringIO(repo.get_contents(arquivo_avarias).decoded_content.decode('utf-8')))
except: df_avarias = pd.DataFrame()

# DASHBOARD
if not df_base.empty and len(datas_sel) == 2:
    ini, fim = datas_sel
    df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
    
    fat_atual = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
    ini_ant = (pd.to_datetime(ini) - pd.DateOffset(months=1)).date()
    fim_ant = (pd.to_datetime(fim) - pd.DateOffset(months=1)).date()
    fat_ant = df_base[(df_base['Data_Date'] >= ini_ant) & (df_base['Data_Date'] <= fim_ant) & (df_base['CODOPER'] == 'S')]['Valor_Final'].sum()
    dif = fat_atual - fat_ant
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>Faturamento</h3><p style="font-size:24px; font-weight:800">R$ {fat_atual:,.2f}</p>{"🔺" if dif >= 0 else "🔻"} R$ {abs(dif):,.2f} vs mês anterior</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>Comparação</h3><p style="font-size:24px; font-weight:800">{ini_ant.strftime("%d/%m")} a {fim_ant.strftime("%d/%m")}</p>Referência anterior</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>Meta</h3><p style="font-size:24px; font-weight:800">{min(fat_atual/META_FATURAMENTO, 1.0)*100:.1f}%</p>Falta R$ {max(0, META_FATURAMENTO - fat_atual):,.2f}</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📈 Margem", "📊 Vendas", "🔥 Picos", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"])
    
    with tabs[0]:
        st.subheader("Margem Real")
        v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
        st.dataframe(v_prod, use_container_width=True)

    with tabs[1]:
        st.subheader("Visão Diária")
        st.dataframe(pd.pivot_table(df_filt, values='Valor_Final', index='Produto', columns=df_filt['Data_Ref'].dt.strftime('%d/%m'), aggfunc='sum', fill_value=0), use_container_width=True)

    with tabs[2]:
        st.subheader("Picos de Fluxo")
        if 'Hora' in df_filt.columns: st.bar_chart(df_filt[df_filt['CODOPER'] == 'S'].groupby('Hora')['Valor_Final'].sum(), color="#c92a2a")

    with tabs[3]:
        st.subheader("Curva ABC")
        st.table(df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().sort_values(ascending=False))

    with tabs[4]:
        st.subheader("Análise de Ruptura")
        st.info("Fluxo monitorado.")

    with tabs[5]:
        st.subheader("Controle de Avarias")
        if not df_avarias.empty:
            df_avarias['Data'] = pd.to_datetime(df_avarias['Data']).dt.date
            st.dataframe(df_avarias[(df_avarias['Data'] >= ini) & (df_avarias['Data'] <= fim)], use_container_width=True)
else:
    st.info("Selecione um período para iniciar.")
