import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN CLEAN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# Estilização para cartões de métricas (Corrigido o erro do unsafe_allow_html)
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL ---
st.sidebar.title("🏢 RotiFácil Performance")
unidade = st.sidebar.selectbox("Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

# 2. FUNÇÃO DE CARGA DE DADOS
@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        if 'Data' in df.columns:
            df['Data_Ref'] = pd.to_datetime(df['Data'])
            df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except:
        return pd.DataFrame()

# Carregando bases
arq_vendas = "vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv"
df_base = carregar(arq_vendas)
df_custos = carregar("custos.csv")
df_avarias = carregar("avarias.csv")

if not df_base.empty:
    st.title(f"🍗 Gestão de Unidade: {unidade}")
    
    # --- FILTRO GLOBAL ---
    hoje = df_base['Data_Date'].max()
    primeiro_dia = hoje.replace(day=1)
    datas = st.date_input("Período de Análise:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # --- ABAS ÚNICAS E ESTRATÉGICAS ---
        aba_vendas, aba_abc, aba_performance, aba_avaria = st.tabs([
            "📊 Visão Diária", "🏆 Curva ABC", "📈 Margem & Projeções", "🗑️ Controle de Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA 1: VISÃO DIÁRIA ---
        with aba_vendas:
            v_bruta = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
            devolucoes = df_filt[df_filt['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
            faturamento_liquido = v_bruta - devolucoes

            c1, c2, c3 = st.columns(3)
            c1.metric("Faturamento Líquido", fmt(faturamento_liquido))
            c2.metric("Peso Total Vendido", f"{df_filt['Qtd_KG'].sum():,.2f} kg")
            c3.metric("Ticket Médio/KG", fmt(faturamento_liquido / df_filt['Qtd_KG'].sum() if df_filt['Qtd_KG'].sum() > 0 else 0))

            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            
            tab_vendas = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab_vendas.empty:
                tab_vendas['TOTAL'] = tab_vendas.sum(axis=1)
                st.dataframe(tab_vendas.sort_values('TOTAL', ascending=False).map(fmt), use_container_width=True)

        # --- ABA 2: CURVA ABC ---
        with aba_abc:
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
            abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            st.table(abc[['Curva', 'Produto', 'Valor_Final']].head(20).map(lambda x: fmt(x) if isinstance(x, float) else x))

        # --- ABA 3: PERFORMANCE E PROJEÇÕES ---
        with aba_performance:
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.subheader("🔮 Projeção para Amanhã")
                amanha_num = (datetime.now().weekday() + 1) % 7
                proj = df_base[df_base['CODOPER'] == 'S'].copy()
                proj['Dia_Num'] = proj['Data_Ref'].dt.weekday
                sugestao = proj[proj['Dia_Num'] == amanha_num].groupby('Produto')['Qtd_KG'].mean().reset_index()
                sugestao['Sugestão Produção (KG)'] = sugestao['Qtd_KG'] * 1.15 # Margem de segurança
                st.dataframe(sugestao.sort_values('Sugestão Produção (KG)', ascending=False), use_container_width=True)

            with col_p2:
                st.subheader("💰 Margem de Contribuição")
                if not df_custos.empty:
                    margem_df = abc.merge(df_custos, on='Produto', how='left')
                    st.write("Cálculo de lucratividade baseado no arquivo de custos...")
                else:
                    st.warning("⚠️ Arquivo 'custos.csv' não encontrado no GitHub. Crie-o para ver a margem.")

        # --- ABA 4: AVARIAS ---
        with aba_avaria:
            st.subheader("🗑️ Registro de Desperdício")
            if not df_avarias.empty:
                st.write("Visão diária de perdas em quilos e reais...")
            else:
                st.info("Para performance máxima, registre as avarias diárias no arquivo 'avarias.csv'.")

else:
    st.info("🚀 RotiFácil: Sincronizando com o WinThor... Aguarde um instante.")