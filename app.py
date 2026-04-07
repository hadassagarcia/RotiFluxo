<<<<<<< HEAD
import streamlit as st
import pandas as pd
from datetime import timedelta

# Configuração visual
st.set_page_config(page_title="RotiFluxo", layout="wide")

st.title("Análise de Vendas - Rotisseria")

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        # Lê o arquivo enviado pelo seu computador (vendas_filial2.csv)
        df = pd.read_csv("vendas_filial2.csv")
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except:
        st.error("⚠️ Aguardando sincronização dos dados do computador local...")
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    # --- FILTROS ---
    st.subheader("Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Intervalo:", value=(data_ini_padrao, data_max))

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data'] >= ini) & (df_base['Data'] <= fim)].copy()
        
        # --- LÓGICA DE SEPARAÇÃO (Filial 5 vs Loja) ---
        
        # 1. Venda Direta para Filial 5 (Cliente 6613)
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        # 2. Venda Líquida Loja (S - E, excluindo cliente 6613)
        # Aqui filtramos apenas o que é venda real de balcão
        df_loja = df[df['CODCLI'] != 6613].copy()
        
        def calc_liq(l):
            if l['CODOPER'] == 'S': return l['Valor_Final']
            if l['CODOPER'] in ['E', 'ED']: return -l['Valor_Final']
            return 0
        
        fat_liquido = df_loja.apply(calc_liq, axis=1).sum() if not df_loja.empty else 0
        
        # --- EXIBIÇÃO DOS CARDS (SÓ OS 3 DESEJADOS) ---
        st.subheader("Resumo Financeiro - Filial 2")
        c1, c2, c3 = st.columns(3)
        
        def fmt(v): 
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("💰 VENDA LÍQUIDA (Loja)", fmt(fat_liquido))
        c2.metric("🏪 VENDA FILIAL 5", fmt(venda_f5))
        c3.metric("📈 FATURAMENTO TOTAL", fmt(fat_liquido + venda_f5))

        st.divider()

        # --- TABELA DIÁRIA ---
        st.subheader("🗓️ Visão Diária: Faturamento (Loja + Filial 5)")
        
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia'] = df['Data'].apply(lambda d: f"{dias_pt[d.weekday()]} ({d.strftime('%d/%m')})")
        ordem = df.sort_values('Data')['Dia'].unique()

        # Cálculo do valor líquido para a tabela (Venda - Devolução)
        df['V_Liq_Final'] = df.apply(lambda r: r['Valor_Final'] if r['CODOPER']=='S' else (-r['Valor_Final'] if r['CODOPER'] in ['E','ED'] else 0), axis=1)
        
        tab = pd.pivot_table(df, values='V_Liq_Final', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
        tab = tab.reindex(columns=ordem)
        tab['Total'] = tab.sum(axis=1)
        tab = tab.sort_values('Total', ascending=False)
        
        # Exibição da Tabela com formatação de moeda
        st.dataframe(tab.applymap(fmt), use_container_width=True)
        
        # Gráfico de Tendência
        st.subheader("📈 Tendência Diária")
        graf = pd.pivot_table(df.sort_values('Data'), values='V_Liq_Final', index='Dia', columns='Produto', aggfunc='sum', fill_value=0, sort=False)
        st.line_chart(graf)

else:
    st.info("Aguardando os dados da Filial 2 serem sincronizados...")
=======
import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="RotiFluxo - Filial 2", layout="wide", page_icon="🍗")

st.title("🍗 Análise de Vendas - Rotisseria (Filial 2)")

# Função para carregar os dados do arquivo CSV que seu PC enviou
@st.cache_data(ttl=600)
def carregar_dados_sincronizados():
    try:
        # Ele lê o arquivo vendas_filial2.csv que já está na mesma pasta do GitHub
        df = pd.read_csv("vendas_filial2.csv")
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except Exception as e:
        st.error("⚠️ Arquivo de dados não encontrado ou ainda não sincronizado.")
        return pd.DataFrame()

# Executa a carga
df_base = carregar_dados_sincronizados()

if not df_base.empty:
    st.subheader("Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Intervalo de datas:", value=(data_ini_padrao, data_max))

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data'] >= ini) & (df_base['Data'] <= fim)].copy()
        
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia_Exibicao'] = df['Data'].apply(lambda d: f"{dias_pt[d.weekday()]} ({d.strftime('%d/%m')})")
        dias_ord = df.sort_values('Data')['Dia_Exibicao'].unique()

        def calcular_liquido(linha):
            if linha['CODOPER'] == 'S': return linha['Valor_Final']
            if linha['CODOPER'] in ['E', 'ED']: return -linha['Valor_Final']
            return 0 

        df['Valor_Liquido'] = df.apply(calcular_liquido, axis=1)

        # KPIs
        fat_liquido = df['Valor_Liquido'].sum()
        transferencias = df[df['CODOPER'] == 'ST']['Valor_Final'].sum()
        consumo_sm = df[df['CODOPER'] == 'SM']['Valor_Final'].sum()

        st.subheader("Resumo Financeiro - Filial 2")
        c1, c2, c3 = st.columns(3)
        def fmt(valor):
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("💰 VENDA LÍQUIDA (S-E)", fmt(fat_liquido))
        c2.metric("🚚 Transferências (ST)", fmt(transferencias))
        c3.metric("⚙️ Consumo/Perda (SM)", fmt(consumo_sm))

        st.divider()

        # TABELA
        st.subheader("🗓️ Visão Diária: Faturamento Líquido")
        tab = pd.pivot_table(df, values='Valor_Liquido', index='Produto', columns='Dia_Exibicao', aggfunc='sum', fill_value=0)
        tab = tab.reindex(columns=dias_ord)
        tab['Total'] = tab.sum(axis=1)
        tab = tab.sort_values('Total', ascending=False)

        tab_v = tab.copy()
        for col in tab_v.columns:
            tab_v[col] = tab_v[col].apply(fmt)
        
        st.dataframe(tab_v, use_container_width=True)
        st.line_chart(pd.pivot_table(df.sort_values('Data'), values='Valor_Liquido', index='Dia_Exibicao', columns='Produto', aggfunc='sum', fill_value=0, sort=False))
>>>>>>> 4cb9e7c271a5319dbc9b72c7a3a0d4625c8ea0a3
