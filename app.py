import streamlit as st
import pandas as pd
from datetime import timedelta
import time

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="RotiVision", layout="wide", page_icon="🍗")

# --- BARRA LATERAL ---
st.sidebar.title("🏢 Unidade")
unidade = st.sidebar.selectbox("Escolha a Loja:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

if st.sidebar.button('🔄 Atualizar Agora'):
    st.cache_data.clear()
    st.rerun()

# 2. CARGA DE DADOS (Lê o arquivo conforme a loja selecionada)
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
    st.title(f"🍗 {unidade}")

    # --- DATAS E FILTROS ---
    hoje = df_base['Data_Date'].max()
    primeiro_dia_mes = hoje.replace(day=1)
    
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        datas = st.date_input("Filtrar Período:", value=(primeiro_dia_mes, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- CARDS ESPECÍFICOS PARA FILIAL 2 ---
        if "Filial 2" in unidade:
            v_bruta_local = df_filt[(df_filt['CODOPER'] == 'S') & (df_filt['CODCLI'] != 6613)]['Valor_Final'].sum()
            v_planalto = df_filt[(df_filt['CODOPER'] == 'S') & (df_filt['CODCLI'] == 6613)]['Valor_Final'].sum()
            total_periodo = v_bruta_local + v_planalto
            
            # Acumulado sempre do dia 01 até Hoje
            df_mes_total = df_base[df_base['Data_Date'] >= primeiro_dia_mes]
            v_acumulado = df_mes_total[df_mes_total['CODOPER'] == 'S']['Valor_Final'].sum() - \
                          df_mes_total[df_mes_total['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🛒 VENDA LOCAL", fmt(v_bruta_local))
            c2.metric("🏪 VENDA PLANALTO", fmt(v_planalto))
            c3.metric("📊 TOTAL NO PERÍODO", fmt(total_periodo))
            c4.metric("💰 ACUMULADO MÊS", fmt(v_acumulado))
        
        # --- CARDS ESPECÍFICOS PARA FILIAL 5 ---
        else:
            v_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum() - \
                        df_filt[df_filt['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
            
            df_mes_total = df_base[df_base['Data_Date'] >= primeiro_dia_mes]
            v_acumulado = df_mes_total[df_mes_total['CODOPER'] == 'S']['Valor_Final'].sum() - \
                          df_mes_total[df_mes_total['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("🛒 VENDA NO PERÍODO", fmt(v_periodo))
            c2.metric("💰 ACUMULADO MÊS", fmt(v_acumulado))
            c3.metric("📅 ATUALIZAÇÃO", hoje.strftime('%d/%m'))

        st.divider()

        # --- ABAS ---
        aba1, aba2 = st.tabs(["🗓️ Visão Diária", "🏆 Curva ABC"])

        with aba1:
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab.empty:
                ordem = df_filt.sort_values('Data_Ref')['Dia'].unique()
                tab = tab.reindex(columns=ordem)
                tab['TOTAL'] = tab.sum(axis=1)
                tab =