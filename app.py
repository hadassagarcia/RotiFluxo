import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="RotiVision", layout="wide", page_icon="🍗")

# --- BOTÃO DE ATUALIZAÇÃO MANUAL ---
if st.sidebar.button('🔄 Atualizar Vendas Agora'):
    st.cache_data.clear()
    st.rerun()

# 2. CARGA DE DADOS
@st.cache_data(ttl=30) 
def carregar_dados():
    try:
        url = "https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/vendas_geral.csv"
        url_com_timestamp = f"{url}?v={int(time.time())}"
        df = pd.read_csv(url_com_timestamp)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    st.title("🍗 RotiVision - Inteligência de Vendas")
    
    # --- FILTRO DE DATA (AFETA APENAS A TABELA E GRÁFICO) ---
    data_max = df_base['Data_Date'].max()
    data_ini_padrao = data_max - timedelta(days=6)
    
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        datas = st.date_input("Filtrar Período da Tabela:", 
                              value=(data_ini_padrao, data_max), 
                              max_value=data_max)

    if len(datas) == 2:
        ini, fim = datas
        # DF filtrado para a tabela
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # --- CÁLCULO MENSAL (DIA 01 ATÉ HOJE) ---
        primeiro_dia_mes = data_max.replace(day=1)
        df_mes = df_base[df_base['Data_Date'] >= primeiro_dia_mes]
        faturamente_mensal = df_mes[df_mes['CODOPER'] == 'S']['Valor_Final'].sum() - \
                             df_mes[df_mes['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()

        # --- CÁLCULOS DOS CARDS (FILTRO SELECIONADO) ---
        venda_bruta_total = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
        venda_planalto = df_filt[(df_filt['CODOPER'] == 'S') & (df_filt['CODCLI'] == 6613)]['Valor_Final'].sum()
        venda_real_loja = venda_bruta_total - venda_planalto
        
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- EXIBIÇÃO DOS CARDS ---
        st.subheader(f"📊 Resumo Financeiro ({ini.strftime('%d/%m')} a {fim.strftime('%d/%m')})")
        c1, c2, c3, c4 = st.columns(4)
        
        c1.metric("🛒 VENDA BRUTA (Total)", fmt(venda_bruta_total))
        c2.metric("🏪 VENDA PLANALTO", fmt(venda_planalto))
        c3.metric("📈 VENDA REAL LOJA", fmt(venda_real_loja), help="Venda Total menos Saída para Planalto")
        c4.metric("💰 TOTAL ACUMULADO MÊS", fmt(faturamente_mensal))

        st.divider()

        # --- ABAS ---
        aba1, aba2 = st.tabs(["🗓️ Visão Diária", "🏆 Curva ABC"])
        
        with aba1:
            # Tabela Diária mantendo sua lógica de soma no rodapé
            df_filt['Valor_Tabela'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia_Exibicao'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            
            tab_dados = pd.pivot_table(df_filt, values='Valor_Tabela', index='Produto', columns='Dia_Exibicao', aggfunc='sum', fill_value=0)
            if not tab_dados.empty:
                ordem_colunas = df_filt.sort_values('Data_Ref')['Dia_Exibicao'].unique()
                tab_dados = tab_dados.reindex(columns=ordem_colunas)
                tab_dados['TOTAL'] = tab_dados.sum(axis=1)
                tab_dados = tab_dados.sort_values('TOTAL', ascending=False)
                tab_dados.loc['TOTAL DIA ➔'] = tab_dados.sum(axis=0)
                st.dataframe(tab_dados.map(fmt), use_container_width=True)