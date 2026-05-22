import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925  # 29,25% sobre o Preço de Venda

# --- TABELA DE PRECIFICAÇÃO ATUALIZADA ---
PRECIFICACAO_REAL = {
    "ARROZ C/ CREME FRANGO KG": [16.39, 39.99],
    "ARROZ CREMOSO FRANGO KG": [16.44, 43.99],
    "ARROZ LEITE C/ CARNE SOL KG": [15.05, 47.99],
    "BAIAO DE DOIS CF KG": [16.99, 36.99],
    "CARNE C/ MACAXEIRA KG": [16.50, 29.99], # Assumindo 16.50 como base
    "CUSCUZ C/ CARNE KG": [14.90, 32.99],
    "CUSCUZ C/ CARNE MOIDA KG": [10.23, 29.99],
    "CUSCUZ C/ SALSICHA KG": [7.90, 24.99],
    "EMPADAO CARNE SOL KG": [21.82, 55.99],
    "EMPADAO FRANGO KG": [16.69, 52.99],
    "ESCONDIDINHO CARNE MOIDA KG": [17.18, 44.99],
    "FRANGO ASSADO CORTE FACIL KG": [23.92, 34.99],
    "LASANHA CARNE MOIDA KG": [21.24, 45.99],
    "LASANHA FRANGO KG": [25.41, 45.99],
    "MACAXEIRA C/ CALABRESA ACEB KG": [9.89, 37.99],
    "PATE FRANGO KG": [21.85, 44.99],
    "SOPA CARNE KG": [8.71, 32.99],
    "TAPIOCA CARNE SOL KG": [21.05, 47.99],
    "TAPIOCA FRANGO KG": [15.30, 43.99],
    "TAPIOCA MISTA KG": [14.32, 47.99],
    "TAPIOCA QUEIJO KG": [19.54, 47.99],
}

# --- ESTILIZAÇÃO CSS (INSPIRADO NO NEXA AI) ---
st.markdown("""
    <style>
    /* Esconder Sidebar */
    [data-testid="stSidebar"] { display: none; }
    
    /* Cor de fundo da página principal */
    .stApp { background-color: #F4F7FA; }
    
    /* Estilização dos painéis/cards (Métricas e Dataframes) */
    [data-testid="stMetric"], .stDataFrame {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #E8EEF3;
    }
    
    /* Letras das métricas */
    [data-testid="stMetricValue"] { font-size: 38px !important; font-weight: 800; color: #111827; }
    [data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 500; color: #6B7280; }
    
    /* Estilo das Abas (Tabs) inspirado no Nexa AI */
    div[data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 15px;
        justify-content: center;
        border-bottom: none;
        margin-bottom: 20px;
    }
    button[data-baseweb="tab"] { 
        background-color: #FFFFFF !important; 
        border-radius: 30px !important; 
        padding: 10px 24px !important;
        font-size: 16px !important; 
        font-weight: 600 !important;
        color: #6B7280 !important;
        border: 1px solid #E8EEF3 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    button[aria-selected="true"] { 
        background-color: #1F2937 !important; /* Cor escura do botão selecionado */
        color: #FFFFFF !important; 
        border: none !important;
    }
    
    /* Ajustes gerais de fonte */
    h1, h2, h3, p { font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DADOS ---
@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except: return pd.DataFrame()

# ==========================================
# CABEÇALHO CLEAN (LOGO NA ESQUERDA, CONTROLES NA DIREITA)
# ==========================================
col_logo, col_vazia, col_filial, col_data = st.columns([1.5, 1, 1, 1.5])

with col_logo:
    # Ajuste o nome da sua logo aqui se necessário
    try:
        st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=220)
    except:
        st.markdown("### 🍗 RotiFácil")

# Lógica de seleção
if 'unidade_selecionada' not in st.session_state:
    st.session_state.unidade_selecionada = "Filial 2"

df_temp = carregar("vendas_filial2.csv") # Apenas para pegar a data máxima inicial
hoje_dados = df_temp['Data_Date'].max() if not df_temp.empty else datetime.today().date()

with col_filial:
    st.write("") # Espaçador para alinhar verticalmente
    unidade = st.selectbox("📍 Unidade", ["Filial 2", "Filial 5"], label_visibility="collapsed")
    st.session_state.unidade_selecionada = unidade

with col_data:
    st.write("") # Espaçador
    datas_sel = st.date_input("📅 Período", value=(hoje_dados.replace(day=1), hoje_dados), max_value=hoje_dados, label_visibility="collapsed")

st.write("") # Espaço extra
# ==========================================

df_base = carregar("vendas_filial2.csv" if unidade == "Filial 2" else "vendas_filial5.csv")
df_avarias = carregar("avarias.csv")

if not df_base.empty and len(datas_sel) == 2:
    ini, fim = datas_sel
    df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
    
    # --- PAINEL DE VISÃO GERAL (CARDS) ---
    fat_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
    progresso = min(fat_periodo / META_FATURAMENTO, 1.0)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💰 Faturamento do Período", f"R$ {fat_periodo:,.2f}")
    with c2:
        st.metric("🎯 Meta Mensal (R$ 50k)", f"{progresso*100:.1f}%")
        st.progress(progresso)
    with c3:
        qtd_kg = df_filt[df_filt['CODOPER'] == 'S']['Qtd_KG'].sum()
        st.metric("⚖️ Volume Vendido", f"{qtd_kg:,.1f} KG")

    st.write("<br>", unsafe_allow_html=True)

    # --- ABAS MODERNAS ---
    aba_perf, aba_vendas, aba_pico, aba_abc, aba_ruptura, aba_avaria = st.tabs([
        "📈 Margem Real", "📊 Visão Diária", "🔥 Mapa de Calor", "🏆 Curva ABC", "🚨 Ruptura", "🗑️ Avarias"
    ])

    def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # --- ABA PERFORMANCE & MARGEM REAL ---
    with aba_perf:
        v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
        if not v_prod.empty:
            v_prod['Custo_Base_Unit'] = v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[0])
            v_prod['Preco_Venda_Unit'] = v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[1])
            v_prod['Faturamento_Gerencial'] = v_prod['Qtd_KG'] * v_prod['Preco_Venda_Unit']
            v_prod['Imposto_Total'] = v_prod['Faturamento_Gerencial'] * IMPOSTO_PERCENTUAL
            v_prod['Custo_Total_Materia_Prima'] = v_prod['Qtd_KG'] * v_prod['Custo_Base_Unit']
            v_prod['Lucro_R$'] = v_prod['Faturamento_Gerencial'] - v_prod['Imposto_Total'] - v_prod['Custo_Total_Materia_Prima']
            v_prod['Margem_Real'] = v_prod.apply(lambda r: (r['Lucro_R$'] / r['Faturamento_Gerencial'] * 100) if r['Faturamento_Gerencial'] > 0 else 0, axis=1)
            
            df_mostrar = v_prod.sort_values('Lucro_R$', ascending=False)[['Produto', 'Faturamento_Gerencial', 'Lucro_R$', 'Margem_Real']]
            st.dataframe(df_mostrar.style.format({
                'Faturamento_Gerencial': fmt, 
                'Lucro_R$': fmt, 
                'Margem_Real': '{:.2f}%'
            }).map(lambda x: 'color: #EF4444; font-weight: bold' if isinstance(x, float) and x < 10 else None, subset=['Margem_Real']), 
            use_container_width=True)

    # --- ABA VISÃO DIÁRIA ---
    with aba_vendas:
        df_filt['Val'] = df_filt['Valor_Final']
        dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
        df_filt['Data_Rotulo'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} {dias_pt[d.weekday()]}")
        tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Data_Rotulo', aggfunc='sum', fill_value=0)
        if not tab.empty:
            ordem_cols = sorted(df_filt['Data_Rotulo'].unique(), key=lambda x: x[:5])
            tab = tab.reindex(columns=ordem_cols)
            tab['TOTAL'] = tab.sum(axis=1)
            tab = tab.sort_values('TOTAL', ascending=False)
            tab.loc['TOTAL DIA ➔'] = tab.sum(axis=0)
            st.dataframe(tab.map(fmt), use_container_width=True)

    # --- NOVA ABA: HORÁRIOS DE PICO ---
    with aba_pico:
        if 'Hora' in df_filt.columns:
            df_pico = df_filt[df_filt['CODOPER'] == 'S'].copy()
            if not df_pico.empty:
                dias_semana_num = {0:'0-Seg', 1:'1-Ter', 2:'2-Qua', 3:'3-Qui', 4:'4-Sex', 5:'5-Sáb', 6:'6-Dom'}
                df_pico['Dia_Semana'] = df_pico['Data_Ref'].dt.weekday.map(dias_semana_num)
                mapa_pico = pd.pivot_table(df_pico, values='Valor_Final', index='Dia_Semana', columns='Hora', aggfunc='sum', fill_value=0)
                
                if not mapa_pico.empty:
                    mapa_pico.index = mapa_pico.index.str[2:]
                    dia_sel = st.selectbox("📊 Veja a curva de fluxo de um dia específico:", mapa_pico.index)
                    st.bar_chart(mapa_pico.loc[dia_sel], color="#3B82F6")
                    
                    st.write("### 🌡️ Matriz Semanal de Faturamento por Hora")
                    st.dataframe(mapa_pico.style.background_gradient(cmap='Blues', axis=None).format(fmt), use_container_width=True)
        else:
            st.warning("⚠️ Os dados de horário ainda não foram sincronizados pelo robô.")

    # --- ABA CURVA ABC ---
    with aba_abc:
        abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
        if not abc.empty:
            abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
            abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            st.dataframe(abc[['Curva', 'Produto', 'Valor_Final']].style.format({'Valor_Final': fmt}), use_container_width=True)

    # --- ABA RUPTURA ---
    with aba_ruptura:
        if 'Hora' in df_filt.columns:
            vendas_abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            if not vendas_abc.empty:
                vendas_abc['% Acum'] = (vendas_abc['Valor_Final'] / vendas_abc['Valor_Final'].sum()).cumsum() * 100
                lista_a = vendas_abc[vendas_abc['% Acum'] <= 80]['Produto'].tolist()
                prod_analise = st.selectbox("Auditar Fluxo Horário (Dia Final):", lista_a if lista_a else vendas_abc['Produto'].head(5).tolist())
                df_hora = df_filt[(df_filt['Produto'] == prod_analise) & (df_filt['Data_Date'] == fim)].copy()
                if not df_hora.empty:
                    fluxo_hora = df_hora.groupby('Hora')['Valor_Final'].sum().reset_index().sort_values('Hora')
                    st.line_chart(fluxo_hora.set_index('Hora')['Valor_Final'], color="#EF4444")
                    ult_h = int(fluxo_hora['Hora'].max())
                    if ult_h < 13: st.error(f"Ruptura! Parou de vender às {ult_h}h.")
                    else: st.success(f"Fluxo normal até às {ult_h}h.")

    # --- ABA AVARIA ---
    with aba_avaria:
        if not df_avarias.empty:
            st.dataframe(df_avarias, use_container_width=True)
        else: st.info("Sem avarias registradas.")

else: st.info("Aguardando seleção de datas ou sincronizando dados...")