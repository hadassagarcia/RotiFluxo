import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from github import Github
import io

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="RotiFácil Pro", layout="wide", page_icon="🍗")

# --- CSS PROFISSIONAL (DESIGN SAAS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    /* A Caixa Mestre */
    .main-dashboard {
        background: #ffffff;
        border-radius: 24px;
        padding: 40px;
        margin: 20px auto;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        max-width: 1200px;
    }
    .metric-card { 
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; 
        padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); 
    }
    /* Abas Profissionais */
    div[data-testid="stTabs"] button { border-radius: 12px; font-weight: 600; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 20px; }
    div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #c92a2a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# 🔐 LOGIN
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        usuario = st.text_input("👤 Usuário")
        senha = st.text_input("🔑 Senha", type="password")
        if st.button("Entrar", type="primary"):
            if usuario.strip().lower() in ["hadassa", "thiago", "mariana", "geyzzon"]:
                st.session_state['logado'] = True
                st.rerun()
    st.stop()

# --- INÍCIO DA CAIXA MESTRE ---
st.markdown('<div class="main-dashboard">', unsafe_allow_html=True)

# CABEÇALHO E FILTROS
col_logo, _, col_filial, col_data = st.columns([2, 1, 2, 2])
with col_logo:
    st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=180)
unidade = col_filial.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
datas_sel = col_data.date_input("📅 Período:", value=(datetime.today().date().replace(day=1), datetime.today().date()))
st.divider()

# LÓGICA DE DADOS (Mantida conforme seu original)
# [Aqui o seu carregamento de dados permanece igual]
df_base = pd.DataFrame() # Simplificado para estrutura, use sua função carregar()
if len(datas_sel) == 2:
    ini, fim = datas_sel
    # ... (Sua lógica de cálculos e fat_atual aqui)

    # DASHBOARD PROFISSIONAL
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>Faturamento</h3><p style="font-size:24px; font-weight:800">R$ 10.648,31</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>Comparação</h3><p style="font-size:24px; font-weight:800">01/06 a 06/06</p>Referência anterior</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>Meta</h3><p style="font-size:24px; font-weight:800">21.3%</p></div>', unsafe_allow_html=True)

    st.write("<br>")
    tabs = st.tabs(["📈 Margem", "📊 Vendas", "🔥 Picos", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"])
    with tabs[0]: st.subheader("Margem Real"); st.dataframe(pd.DataFrame(), use_container_width=True)
    # ... (Adicione as outras abas aqui)

st.markdown('</div>', unsafe_allow_html=True) # Fim da Caixa Mestre
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
