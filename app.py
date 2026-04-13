import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# --- BANCO DE DADOS MANUAL DE CUSTOS E PREÇOS ---
# Aqui você gerencia os valores. Nomes devem ser IDÊNTICOS aos do WinThor.
TABELA_PRECOS_CUSTOS = {
    "EMPADAO FRANGO KG": {"venda": 45.90, "custo": 18.50},
    "CUSCUZ C/ CARNE MOIDA KG": {"venda": 32.00, "custo": 12.00},
    "LASANHA FRANGO KG": {"venda": 48.00, "custo": 19.80},
    "PATE FRANGO KG": {"venda": 38.00, "custo": 14.50},
    "SOPA CARNE KG": {"venda": 25.00, "custo": 9.50},
    "LASANHA CARNE MOIDA KG": {"venda": 52.00, "custo": 22.00},
    "CUSCUZ C/ SALSICHA KG": {"venda": 22.00, "custo": 7.50},
    "MACAXEIRA C/ CALABRESA ACEB KG": {"venda": 28.00, "custo": 11.00},
    "CARNE C/ MACAXEIRA KG": {"venda": 42.00, "custo": 16.50},
    "BAIAO DE DOIS CF KG": {"venda": 35.00, "custo": 13.00},
}

IMPOSTO_CMV_FIXO = 0.2925 # 29,25%

# --- DESIGN ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL ---
st.sidebar.title("🏢 RotiFácil Performance")
unidade = st.sidebar.selectbox("Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

# --- CARGA DE DADOS ---
@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except:
        return pd.DataFrame()

df_base = carregar("vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv")

if not df_base.empty:
    st.title(f"🍗 Gestão de Unidade: {unidade}")
    
    hoje = df_base['Data_Date'].max()
    primeiro_dia = hoje.replace(day=1)
    datas = st.date_input("Período de Análise:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        aba_vendas, aba_abc, aba_performance = st.tabs(["📊 Visão Diária", "🏆 Curva ABC", "📈 Margem & Projeções"])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA VISÃO DIÁRIA ---
        with aba_vendas:
            v_bruta = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
            devolucoes = df_filt[df_filt['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
            fat_liq = v_bruta - devolucoes
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Faturamento Líquido", fmt(fat_liq))
            peso = df_filt['Qtd_KG'].sum() if 'Qtd_KG' in df_filt.columns else 0
            c2.metric("Peso Vendido", f"{peso:,.2f} kg")
            c3.metric("Ticket Médio/KG", fmt(fat_liq/peso if peso > 0 else 0))

            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab.empty:
                tab['TOTAL'] = tab.sum(axis=1)
                st.dataframe(tab.sort_values('TOTAL', ascending=False).map(fmt), use_container_width=True)

        # --- ABA ABC ---
        with aba_abc:
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
            abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            st.table(abc[['Curva', 'Produto', 'Valor_Final']].map(lambda x: fmt(x) if isinstance(x, float) else x))

        # --- ABA PERFORMANCE & MARGEM ---
        with aba_performance:
            st.subheader("💰 Análise de Lucratividade (CMV + Imposto: 29,25%)")
            
            # Criando DataFrame de Margem
            vendas_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
            
            # Adiciona dados manuais
            vendas_prod['Custo_Unit'] = vendas_prod['Produto'].apply(lambda x: TABELA_PRECOS_CUSTOS.get(x, {}).get('custo', 0))
            vendas_prod['Preco_Venda'] = vendas_prod['Produto'].apply(lambda x: TABELA_PRECOS_CUSTOS.get(x, {}).get('venda', 0))
            
            # Cálculos Financeiros
            vendas_prod['Imposto_Total'] = vendas_prod['Valor_Final'] * IMPOSTO_CMV_FIXO
            vendas_prod['Custo_Total'] = vendas_prod['Qtd_KG'] * vendas_prod['Custo_Unit']
            vendas_prod['Lucro_Liquido'] = vendas_prod['Valor_Final'] - vendas_prod['Imposto_Total'] - vendas_prod['Custo_Total']
            vendas_prod['Margem_%'] = (vendas_prod['Lucro_Liquido'] / vendas_prod['Valor_Final']) * 100

            # Exibição
            st.write("Abaixo, os produtos que realmente estão gerando lucro para a rotisseria:")
            df_margem_final = vendas_prod[vendas_prod['Custo_Unit'] > 0].sort_values('Lucro_Liquido', ascending=False)
            
            st.dataframe(df_margem_final[['Produto', 'Valor_Final', 'Lucro_Liquido', 'Margem_%']].style.format({
                'Valor_Final': fmt, 'Lucro_Liquido': fmt, 'Margem_%': '{:.2f}%'
            }), use_container_width=True)

            st.divider()
            
            # --- PROJEÇÃO SEMANAL ---
            st.subheader("📈 Projeção de Performance Semanal")
            sem_atual = df_base[df_base['Data_Date'] >= (hoje - timedelta(days=7))]['Valor_Final'].sum()
            sem_ant = df_base[(df_base['Data_Date'] >= (hoje - timedelta(days=14))) & (df_base['Data_Date'] < (hoje - timedelta(days=7)))]['Valor_Final'].sum()
            
            if sem_ant > 0:
                cresc = ((sem_atual - sem_ant) / sem_ant) * 100
                st.metric("Crescimento vs Semana Anterior", fmt(sem_atual), delta=f"{cresc:.2f}%")

else:
    st.info("🚀 RotiFácil: Carregando dados de performance...")