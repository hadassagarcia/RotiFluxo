import streamlit as st
import pandas as pd
from datetime import timedelta
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="RotiFluxo", layout="wide", page_icon="🍗")

st.title("Análise de Vendas - Rotisseria")

# 2. FUNÇÃO DE CARGA DE DADOS
@st.cache_data(ttl=30) 
def carregar_dados():
    try:
        url = "https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/vendas_filial2.csv"
        url_com_timestamp = f"{url}?v={int(time.time())}"
        df = pd.read_csv(url_com_timestamp)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    # --- FILTROS ---
    st.subheader("📅 Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data_Date'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Selecione o Intervalo:", value=(data_ini_padrao, data_max), max_value=data_max)

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia_Exibicao'] = df['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
        
        # --- CÁLCULOS DOS KPIs ---
        venda_bruta = df[df['CODOPER'] == 'S']['Valor_Final'].sum()
        devolucoes = df[df['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
        total_geral = venda_bruta - devolucoes
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        # --- EXIBIÇÃO DOS CARDS ---
        st.subheader("💰 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("🛒 VENDA BRUTA", fmt(venda_bruta))
        c2.metric("🏪 SAÍDA FILIAL 5", fmt(venda_f5))
        c3.metric("📈 FATURAMENTO LÍQUIDO", fmt(total_geral))

        st.divider()

        # --- TABELA COM LINHA DE TOTAL ---
        df['Valor_Tabela'] = df.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)

        tab_dados = pd.pivot_table(
            df, values='Valor_Tabela', index='Produto', columns='Dia_Exibicao', aggfunc='sum', fill_value=0
        )

        if not tab_dados.empty:
            # Ordenar colunas cronologicamente
            ordem_colunas = df.sort_values('Data_Ref')['Dia_Exibicao'].unique()
            tab_dados = tab_dados.reindex(columns=ordem_colunas)

            # 1. Criar a coluna de Total por Produto (Horizontal)
            tab_dados['TOTAL PRODUTO'] = tab_dados.sum(axis=1)
            
            # 2. Ordenar por quem vende mais antes de adicionar a linha de total
            tab_dados = tab_dados.sort_values('TOTAL PRODUTO', ascending=False)

            # 3. CRIAR A LINHA DE TOTAL POR DIA (Vertical)
            # Somamos todas as colunas numéricas
            linha_total_dia = tab_dados.sum(axis=0)
            tab_dados.loc['TOTAL DIA ➔'] = linha_total_dia

            st.subheader("🗓️ Visão Diária: Faturamento por Produto")
            st.dataframe(tab_dados.map(fmt), use_container_width=True)

            # --- GRÁFICO ---
            st.subheader("📈 Tendência de Vendas")
            graf_dados = pd.pivot_table(
                df, values='Valor_Tabela', index='Dia_Exibicao', columns='Produto', aggfunc='sum', fill_value=0
            ).reindex(ordem_colunas)
            st.line_chart(graf_dados)
        else:
            st.warning("Sem dados para o período.")
else:
    st.info("🚀 Sincronizando dados...")