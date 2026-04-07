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
        # Converte para datetime e depois para date para garantir ordenação numérica
        df['Data_Full'] = pd.to_datetime(df['Data'])
        df['Data'] = df['Data_Full'].dt.date
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
        # Filtragem rigorosa por data
        df = df_base[(df_base['Data'] >= ini) & (df_base['Data'] <= fim)].copy()
        
        # Criar a coluna de Dia formatada: "Seg (01/04)"
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia'] = df['Data_Full'].apply(lambda d: f"{dias_pt[d.weekday()]} ({d.strftime('%d/%m')})")
        
        # --- ORDENAÇÃO CRONOLÓGICA ---
        # Criamos uma lista oficial da ordem dos dias baseada na Data real
        lista_ordem_cronologica = df.sort_values('Data_Full')['Dia'].unique().tolist()

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

        # --- TABELA DIÁRIA (GIRO REAL DA LOJA) ---
        st.subheader("🗓️ Visão Diária: Giro Real da Loja")
        
        tab_loja = pd.pivot_table(
            df[df['V_Liq_Loja'] != 0], 
            values='V_Liq_Loja', 
            index='Produto', 
            columns='Dia', 
            aggfunc='sum', 
            fill_value=0
        )
        
        if not tab_loja.empty:
            # FORÇANDO A ORDEM NA TABELA
            tab_loja = tab_loja.reindex(columns=lista_ordem_cronologica)
            tab_loja['Total Loja'] = tab_loja.sum(axis=1)
            tab_loja = tab_loja.sort_values('Total Loja', ascending=False)
            st.dataframe(tab_loja.map(fmt), use_container_width=True)

            # --- GRÁFICO DE TENDÊNCIA ---
            st.subheader("📈 Tendência Diária de Vendas (Loja)")
            
            graf_dados = pd.pivot_table(
                df[df['V_Liq_Loja'] != 0], 
                values='V_Liq_Loja', 
                index='Dia', 
                columns='Produto', 
                aggfunc='sum', 
                fill_value=0
            )
            
            # FORÇANDO A ORDEM NO GRÁFICO
            graf_dados = graf_dados.reindex(lista_ordem_cronologica)

            st.line_chart(graf_dados)
        else:
            st.warning("Sem dados de venda local para o período.")

else:
    st.info("🚀 Aguardando sincronização de dados...")