import streamlit as st
import pandas as pd
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="RotiFluxo", layout="wide", page_icon="🍗")

st.title("Análise de Vendas - Rotisseria")

# 2. FUNÇÃO DE CARGA DE DADOS
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv("vendas_filial2.csv")
        # Garantir que a coluna Data seja tratada como data real para ordenação
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar o arquivo CSV: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    # --- SEÇÃO DE FILTROS ---
    st.subheader("📅 Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Selecione o Intervalo:", value=(data_ini_padrao, data_max))

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data'] >= ini) & (df_base['Data'] <= fim)].copy()
        
        # --- CÁLCULOS DOS KPIs ---
        # Venda para Filial 5 (Cliente 6613)
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        # Venda Líquida Loja (Apenas balcão, excluindo cliente 6613)
        def calc_valor_loja(linha):
            if linha['CODCLI'] == 6613: return 0
            if linha['CODOPER'] == 'S': return linha['Valor_Final']
            if linha['CODOPER'] in ['E', 'ED']: return -linha['Valor_Final']
            return 0

        df['V_Liq_Loja'] = df.apply(calc_valor_loja, axis=1)
        fat_liquido_loja = df['V_Liq_Loja'].sum()
        
        # --- EXIBIÇÃO DOS CARDS (INDICADORES) ---
        st.subheader("💰 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        
        def fmt(v): 
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("🛒 VENDA LÍQUIDA (Loja)", fmt(fat_liquido_loja))
        c2.metric("🏪 VENDA FILIAL 5", fmt(venda_f5))
        c3.metric("📊 FATURAMENTO TOTAL", fmt(fat_liquido_loja + venda_f5))

        st.divider()

        # --- TABELA DIÁRIA (GIRO REAL DA LOJA) ---
        st.subheader("🗓️ Visão Diária: Giro Real da Loja")
        st.info("Esta visão foca no que realmente sai no seu balcão (exclui Filial 5).")
        
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia'] = df['Data'].apply(lambda d: f"{dias_pt[d.weekday()]} ({d.strftime('%d/%m')})")
        
        # Tabela Pivotada para a Loja
        tab_loja = pd.pivot_table(
            df[df['V_Liq_Loja'] != 0], 
            values='V_Liq_Loja', 
            index='Produto', 
            columns='Dia', 
            aggfunc='sum', 
            fill_value=0
        )
        
        if not tab_loja.empty:
            # Ordenar colunas conforme a sequência de datas selecionadas
            ordem_dias = df.sort_values('Data')['Dia'].unique()
            tab_loja = tab_loja.reindex(columns=ordem_dias)
            tab_loja['Total Loja'] = tab_loja.sum(axis=1)
            tab_loja = tab_loja.sort_values('Total Loja', ascending=False)
            
            # Exibir a tabela formatada
            st.dataframe(tab_loja.map(fmt), use_container_width=True)

            # --- GRÁFICO DE TENDÊNCIA (ORDEM CRONOLÓGICA) ---
            st.subheader("📈 Tendência Diária de Vendas (Loja)")
            
            # Pivotamos pela Data (que é ordenada) e depois renomeamos o índice
            graf_dados = pd.pivot_table(
                df[df['V_Liq_Loja'] != 0], 
                values='V_Liq_Loja', 
                index='Data', 
                columns='Produto', 
                aggfunc='sum', 
                fill_value=0
            )
            
            # Converter índice de Data para o nome do Dia para o gráfico ficar bonito
            mapa_dias = df.sort_values('Data').set_index('Data')['Dia'].to_dict()
            graf_dados.index = [mapa_dias[d] for d in graf_dados.index]

            st.line_chart(graf_dados)
        else:
            st.warning("Sem dados de venda local para o período selecionado.")

else:
    st.info("🚀 Aguardando primeira sincronização de dados do WinThor...")