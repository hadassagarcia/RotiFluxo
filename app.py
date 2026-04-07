import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="RotiFluxo", layout="wide",)

st.title("Análise de Vendas - Rotisseria")

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv("vendas_filial2.csv")
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except:
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    st.subheader("Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Intervalo:", value=(data_ini_padrao, data_max))

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data'] >= ini) & (df_base['Data'] <= fim)].copy()
        
        # 1. Venda Direta para Filial 5 (Cliente 6613)
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        # 2. Venda Líquida Loja (S - E, excluindo cliente 6613)
        df_loja = df[df['CODCLI'] != 6613].copy()
        def calc_liq(l):
            if l['CODOPER'] == 'S': return l['Valor_Final']
            if l['CODOPER'] in ['E', 'ED']: return -l['Valor_Final']
            return 0
        fat_liquido = df_loja.apply(calc_liq, axis=1).sum() if not df_loja.empty else 0
        
        st.subheader("Resumo Financeiro - Filial 2")
        c1, c2, c3 = st.columns(3)
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("💰 VENDA LÍQUIDA", fmt(fat_liquido))
        c2.metric("🏪 VENDA FILIAL 5", fmt(venda_f5))
        c3.metric("📈 FATURAMENTO TOTAL", fmt(fat_liquido + venda_f5))

        st.divider()

        st.subheader("🗓️ Visão Diária: Faturamento")
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia'] = df['Data'].apply(lambda d: f"{dias_pt[d.weekday()]} ({d.strftime('%d/%m')})")
        ordem = df.sort_values('Data')['Dia'].unique()
        df['V_Liq_Final'] = df.apply(lambda r: r['Valor_Final'] if r['CODOPER']=='S' else (-r['Valor_Final'] if r['CODOPER'] in ['E','ED'] else 0), axis=1)
        
        tab = pd.pivot_table(df, values='V_Liq_Final', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
        tab = tab.reindex(columns=ordem)
        tab['Total'] = tab.sum(axis=1)
        tab = tab.sort_values('Total', ascending=False)
        st.dataframe(tab.applymap(fmt), use_container_width=True)
        st.line_chart(pd.pivot_table(df.sort_values('Data'), values='V_Liq_Final', index='Dia', columns='Produto', aggfunc='sum', fill_value=0, sort=False))
else:
    st.info("Aguardando sincronização de dados...")