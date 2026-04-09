import streamlit as st
import pandas as pd
from datetime import timedelta
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="RotiFácil", layout="wide", page_icon="🍗")

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
    data_max = df_base['Data_Date'].max()
    data_ini_padrao = data_max - timedelta(days=6)
    
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        datas = st.date_input("Selecione o Intervalo:", 
                              value=(data_ini_padrao, data_max), 
                              max_value=data_max)

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # --- CÁLCULOS DOS KPIs ---
        # 1. Faturamento Total (S - Devoluções)
        venda_bruta = df[df['CODOPER'] == 'S']['Valor_Final'].sum()
        devolucoes = df[df['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
        total_geral = venda_bruta - devolucoes
        
        # 2. Venda específica para a Filial 5 (Cliente 6613)
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        # --- EXIBIÇÃO DOS CARDS (4 COLUNAS) ---
        c1, c2, c3, c4 = st.columns(4)
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        c1.metric("🛒 VENDA BRUTA", fmt(venda_bruta))
        c2.metric("🏪 SAÍDA FILIAL 5 (6613)", fmt(venda_f5)) # VOLTOU O CARD!
        c3.metric("📈 FATURAMENTO LÍQUIDO", fmt(total_geral))
        c4.metric("📅 ÚLTIMA CARGA", data_max.strftime('%d/%m'))

        st.divider()

        # --- ABAS ---
        aba1, aba2 = st.tabs(["📊 Visão Diária", "🏆 Curva ABC"])

        with aba1:
            # Lógica da Tabela com soma no rodapé
            df['Valor_Tabela'] = df.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df['Dia_Exibicao'] = df['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            
            tab_dados = pd.pivot_table(df, values='Valor_Tabela', index='Produto', columns='Dia_Exibicao', aggfunc='sum', fill_value=0)
            if not tab_dados.empty:
                ordem_colunas = df.sort_values('Data_Ref')['Dia_Exibicao'].unique()
                tab_dados = tab_dados.reindex(columns=ordem_colunas)
                tab_dados['TOTAL'] = tab_dados.sum(axis=1)
                tab_dados = tab_dados.sort_values('TOTAL', ascending=False)
                tab_dados.loc['TOTAL DIA ➔'] = tab_dados.sum(axis=0)
                st.dataframe(tab_dados.map(fmt), use_container_width=True)
                st.line_chart(pd.pivot_table(df, values='Valor_Tabela', index='Dia_Exibicao', columns='Produto', aggfunc='sum').reindex(ordem_colunas))

        with aba2:
            st.subheader("Análise de Curva ABC")
            abc = df[df['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index()
            abc = abc.sort_values('Valor_Final', ascending=False)
            abc['% Total'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()) * 100
            abc['% Acumulada'] = abc['% Total'].cumsum()
            abc['Curva'] = abc['% Acumulada'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            
            # Cards de resumo da curva
            ca, cb, cc = st.columns(3)
            ca.success(f"Classe A: {len(abc[abc['Curva']=='A'])} itens")
            cb.warning(f"Classe B: {len(abc[abc['Curva']=='B'])} itens")
            cc.error(f"Classe C: {len(abc[abc['Curva']=='C'])} itens")
            
            # Tabela ABC formatada
            abc_disp = abc.copy()
            abc_disp['Valor_Final'] = abc_disp['Valor_Final'].apply(fmt)
            abc_disp['% Total'] = abc_disp['% Total'].map('{:.2f}%'.format)
            abc_disp['% Acumulada'] = abc_disp['% Acumulada'].map('{:.2f}%'.format)
            st.table(abc_disp[['Curva', 'Produto', 'Valor_Final', '% Total', '% Acumulada']])

else:
    st.info("🚀 Sincronizando dados...")