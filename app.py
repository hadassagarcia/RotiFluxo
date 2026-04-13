import streamlit as st
import pandas as pd
from datetime import timedelta
import time

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="RotiFácil", layout="wide", page_icon="🍗")

# --- BARRA LATERAL ---
st.sidebar.title("🏢 Unidade")
unidade = st.sidebar.selectbox("Escolha a Loja:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

# 2. CARGA DE DADOS
@st.cache_data(ttl=60)
def carregar_dados(loja):
    arq = "vendas_filial2.csv" if "Filial 2" in loja else "vendas_filial5.csv"
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except:
        return pd.DataFrame()

df_base = carregar_dados(unidade)

if not df_base.empty:
    st.title(f"🍗 {unidade} - RotiFácil")

    # --- DATAS ---
    hoje = df_base['Data_Date'].max()
    primeiro_dia_mes = hoje.replace(day=1)
    
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        datas = st.date_input("Filtrar Período:", value=(primeiro_dia_mes, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Cálculo unificado de faturamento líquido (Vendas S - Devoluções E/ED)
        vendas_s = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
        devolucoes = df_filt[df_filt['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
        total_periodo = vendas_s - devolucoes

        if "Filial 2" in unidade:
            # Parnamirim: Separação do cliente 6613 (Planalto)
            v_planalto = df_filt[(df_filt['CODOPER'] == 'S') & (df_filt['CODCLI'] == 6613)]['Valor_Final'].sum()
            v_local_pura = total_periodo - v_planalto
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🛒 VENDA LOCAL", fmt(v_local_pura))
            c2.metric("🏪 VENDA P/ PLANALTO", fmt(v_planalto))
            c3.metric("📊 TOTAL LÍQUIDO", fmt(total_periodo))
            c4.metric("💰 ACUMULADO MÊS", fmt(total_periodo) if ini == primeiro_dia_mes else "---")
        else:
            # Planalto: Valor Total Líquido
            c1, c2, c3 = st.columns(3)
            c1.metric("🛒 VENDA NO PERÍODO", fmt(total_periodo))
            c2.metric("💰 ACUMULADO MÊS", fmt(total_periodo) if ini == primeiro_dia_mes else "---")
            c3.metric("📅 ATUALIZAÇÃO", hoje.strftime('%d/%m'))

        st.divider()

        # --- ABAS ---
        aba1, aba2 = st.tabs(["🗓️ Visão Diária", "🏆 Curva ABC"])

        with aba1:
            # Lógica de sinal para a tabela: Venda é positivo, Devolução é negativo
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab.empty:
                ordem = df_filt.sort_values('Data_Ref')['Dia'].unique()
                tab = tab.reindex(columns=ordem)
                tab['TOTAL'] = tab.sum(axis=1)
                tab = tab.sort_values('TOTAL', ascending=False)
                tab.loc['TOTAL DIA ➔'] = tab.sum(axis=0)
                st.dataframe(tab.map(fmt), use_container_width=True)

        with aba2:
            st.subheader("Análise de Curva ABC (Faturamento)")
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            if not abc.empty:
                abc['% Total'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()) * 100
                abc['% Acum'] = abc['% Total'].cumsum()
                abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                
                abc_exibir = abc.copy()
                abc_exibir['Valor_Final'] = abc_exibir['Valor_Final'].apply(fmt)
                abc_exibir['% Total'] = abc_exibir['% Total'].map('{:.2f}%'.format)
                abc_exibir['% Acum'] = abc_exibir['% Acum'].map('{:.2f}%'.format)
                st.table(abc_exibir[['Curva', 'Produto', 'Valor_Final', '% Total', '% Acum']])
else:
    st.info("Aguardando sincronização do RotiFácil...")