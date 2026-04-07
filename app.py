import streamlit as st
import pandas as pd
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="RotiFluxo - Filial 2", layout="wide", page_icon="🍗")

st.title("🍗 Análise de Vendas - Rotisseria (Filial 2)")

# 2. FUNÇÃO DE CARGA DE DADOS
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv("vendas_filial2.csv")
        # Criar coluna de data real para ordenação rigorosa
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    # --- SEÇÃO DE FILTROS ---
    st.subheader("📅 Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data_Date'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Selecione o Intervalo:", value=(data_ini_padrao, data_max))

    if len(datas) == 2:
        ini, fim = datas
        # Filtragem
        df = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # Criar a coluna de exibição: "01/04 (Qua)" - Colocar a data na frente ajuda o gráfico a ordenar
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia_Exibicao'] = df['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
        
        # --- CÁLCULOS DOS KPIs ---
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        def calc_valor_loja(linha):
            if linha['CODCLI'] == 6613: return 0
            if linha['CODOPER'] == 'S': return linha['Valor_Final']
            if linha['CODOPER'] in ['E', 'ED']: return -linha['Valor_Final']
            return 0

        df['V_Liq_Loja'] = df.apply(calc_valor_loja, axis=1)
        fat_liquido_loja = df['V_Liq_Loja'].sum()
        
        # --- EXIBIÇÃO DOS CARDS ---
        st.subheader("💰 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("🛒 VENDA LÍQUIDA (Loja)", fmt(fat_liquido_loja))
        c2.metric("🏪 VENDA FILIAL 5", fmt(venda_f5))
        c3.metric("📊 FATURAMENTO TOTAL", fmt(fat_liquido_loja + venda_f5))

        st.divider()

        # --- TABELA E GRÁFICO (ORDEM CRONOLÓGICA) ---
        
        # 1. Gerar a Pivot Table usando a DATA REAL como índice para garantir a ordem
        tab_dados = pd.pivot_table(
            df[df['V_Liq_Loja'] != 0], 
            values='V_Liq_Loja', 
            index='Data_Ref', 
            columns='Produto', 
            aggfunc='sum', 
            fill_value=0
        ).sort_index() # Força a ordem 01, 02, 03...

        if not tab_dados.empty:
            # Criar um mapeamento de Data -> Nome Bonito para as colunas/índices
            mapa_nomes = df.sort_values('Data_Ref').set_index('Data_Ref')['Dia_Exibicao'].to_dict()
            
            # --- EXIBIÇÃO DA TABELA ---
            st.subheader("🗓️ Visão Diária: Giro Real da Loja")
            tab_visual = tab_dados.T # Transpor para ter produtos nas linhas
            tab_visual.columns = [mapa_nomes[c] for c in tab_visual.columns]
            tab_visual['Total Loja'] = tab_visual.sum(axis=1)
            tab_visual = tab_visual.sort_values('Total Loja', ascending=False)
            st.dataframe(tab_visual.map(fmt), use_container_width=True)

            # --- EXIBIÇÃO DO GRÁFICO ---
            st.subheader("📈 Tendência Diária de Vendas (Loja)")
            graf_dados = tab_dados.copy()
            graf_dados.index = [mapa_nomes[i] for i in graf_dados.index]
            
            # O st.line_chart às vezes ignora o índice. Vamos usar o st.area_chart 
            # ou forçar o line_chart a não reordenar.
            st.line_chart(graf_dados)
            
        else:
            st.warning("Sem dados para o período.")

else:
    st.info("🚀 Aguardando sincronização de dados...")