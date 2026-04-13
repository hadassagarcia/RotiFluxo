import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CSS para deixar o visual mais limpo (Clean Design)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_index=True)

# --- BARRA LATERAL ---
st.sidebar.title("🏢 Gestão de Performance")
unidade = st.sidebar.selectbox("Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

# 2. CARGA DE DADOS COM TRATAMENTO DE ERROS
@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        if 'Data' in df.columns:
            df['Data_Ref'] = pd.to_datetime(df['Data'])
            df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except:
        return pd.DataFrame()

# Carregando as fontes de dados
arq_vendas = "vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv"
df_base = carregar(arq_vendas)
df_custos = carregar("custos.csv") # Você criará este arquivo com colunas: Produto, Custo_KG
df_avarias = carregar("avarias.csv") # Colunas: Produto, Data, Qtd_Avaria_KG

if not df_base.empty:
    st.title(f"🍗 RotiFácil - {unidade}")
    
    # --- FILTROS E KPIS TOTAIS ---
    hoje = df_base['Data_Date'].max()
    primeiro_dia = hoje.replace(day=1)
    datas = st.date_input("Período de Análise:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # Cálculos de Performance
        venda_bruta = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
        devolucoes = df_filt[df_filt['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
        faturamento_liquido = venda_bruta - devolucoes

        # --- EXIBIÇÃO EM ABAS ÚNICAS (SEM DUPLICAÇÃO) ---
        aba_vendas, aba_abc, aba_performance, aba_avaria = st.tabs([
            "📊 Visão Diária", "🏆 Curva ABC", "📈 Performance & Margem", "🗑️ Controle de Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        with aba_vendas:
            # Cards de resumo no topo da aba
            c1, c2, c3 = st.columns(3)
            c1.metric("Faturamento Líquido", fmt(faturamento_liquido))
            c2.metric("Qtd Itens Vendidos", f"{df_filt['Qtd_KG'].sum():,.2f} kg")
            c3.metric("Ticket Médio/KG", fmt(faturamento_liquido / df_filt['Qtd_KG'].sum() if df_filt['Qtd_KG'].sum() > 0 else 0))

            # Tabela Dinâmica
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab.empty:
                tab['TOTAL'] = tab.sum(axis=1)
                st.dataframe(tab.sort_values('TOTAL', ascending=False).map(fmt), use_container_width=True)

        with aba_abc:
            st.subheader("Análise de Relevância (Pareto)")
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
            abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            st.table(abc)

        with aba_performance:
            st.subheader("🔮 Projeção e Lucratividade")
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.write("**Projeção de Produção para Amanhã**")
                amanha_num = (datetime.now().weekday() + 1) % 7
                proj = df_base[df_base['CODOPER'] == 'S'].copy()
                proj['Dia_Num'] = proj['Data_Ref'].dt.weekday
                sugestao = proj[proj['Dia_Num'] == amanha_num].groupby('Produto')['Qtd_KG'].mean().reset_index()
                sugestao['Sugestão (KG)'] = sugestao['Qtd_KG'] * 1.10 # 10% segurança
                st.dataframe(sugestao.sort_values('Sugestão (KG)', ascending=False), use_container_width=True)

            with col_p2:
                st.write("**Margem de Contribuição Estimada**")
                if not df_custos.empty:
                    margem = abc.merge(df_custos, on='Produto', how='left')
                    # Cálculo: (Venda - Custo) / Venda
                    st.write("Exibindo lucratividade por produto...")
                else:
                    st.warning("⚠️ Carregue o arquivo 'custos.csv' para visualizar as margens.")

        with aba_avaria:
            st.subheader("Controle de Perdas (Avarias)")
            if not df_avarias.empty:
                # Lógica similar à Visão Diária, mas para perdas
                st.write("Dados de avaria por dia...")
            else:
                st.info("💡 Dica: O dono quer ver onde o dinheiro está indo para o lixo. Registre as avarias no arquivo 'avarias.csv'.")

else:
    st.info("🚀 RotiFácil: Sincronizando com a base de dados...")