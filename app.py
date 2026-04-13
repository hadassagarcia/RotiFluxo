import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL ---
st.sidebar.title("🏢 RotiFácil Performance")
unidade = st.sidebar.selectbox("Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

# 2. CARGA DE DADOS
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

df_base = carregar("vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv")
df_custos = carregar("custos.csv")
df_avarias = carregar("avarias.csv")

if not df_base.empty:
    st.title(f"🍗 Gestão de Unidade: {unidade}")
    
    hoje = df_base['Data_Date'].max()
    primeiro_dia = hoje.replace(day=1)
    datas = st.date_input("Período de Análise:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # --- ABAS ESTRATÉGICAS ---
        aba_vendas, aba_abc, aba_performance, aba_avaria = st.tabs([
            "📊 Visão Diária", "🏆 Curva ABC", "📈 Margem & Projeções", "🗑️ Controle de Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA 1: VISÃO DIÁRIA ---
        with aba_vendas:
            v_bruta = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
            devolucoes = df_filt[df_filt['CODOPER'].isin(['E', 'ED'])]['Valor_Final'].sum()
            faturamento_liquido = v_bruta - devolucoes

            c1, c2, c3 = st.columns(3)
            c1.metric("Faturamento Líquido", fmt(faturamento_liquido))
            
            # Verificação de segurança para evitar o erro do print
            peso_total = df_filt['Qtd_KG'].sum() if 'Qtd_KG' in df_filt.columns else 0
            c2.metric("Peso Total Vendido", f"{peso_total:,.2f} kg")
            
            ticket = faturamento_liquido / peso_total if peso_total > 0 else 0
            c3.metric("Ticket Médio/KG", fmt(ticket))

            # Tabela Dinâmica
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            
            tab_vendas = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab_vendas.empty:
                tab_vendas['TOTAL'] = tab_vendas.sum(axis=1)
                st.dataframe(tab_vendas.sort_values('TOTAL', ascending=False).map(fmt), use_container_width=True)

        # --- ABA 2: CURVA ABC ---
        with aba_abc:
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            if not abc.empty:
                abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
                abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                st.table(abc[['Curva', 'Produto', 'Valor_Final']].map(lambda x: fmt(x) if isinstance(x, float) else x))

        # --- ABA 3: PERFORMANCE E PROJEÇÕES ---
        with aba_performance:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.subheader("🔮 Projeção para Amanhã")
                amanha_num = (datetime.now().weekday() + 1) % 7
                proj = df_base[df_base['CODOPER'] == 'S'].copy()
                if 'Qtd_KG' in proj.columns:
                    proj['Dia_Num'] = proj['Data_Ref'].dt.weekday
                    sugestao = proj[proj['Dia_Num'] == amanha_num].groupby('Produto')['Qtd_KG'].mean().reset_index()
                    sugestao['Sugestão (KG)'] = sugestao['Qtd_KG'] * 1.15
                    st.dataframe(sugestao.sort_values('Sugestão (KG)', ascending=False), use_container_width=True)
                else:
                    st.warning("Coluna de peso (KG) não encontrada para projeção.")

            with col_p2:
                st.subheader("💰 Margem de Lucro")
                if not df_custos.empty:
                    st.write("Análise cruzando venda real vs custo de produção...")
                else:
                    st.info("💡 Envie o arquivo 'custos.csv' com colunas [Produto, Custo_KG] para ativar esta visão.")

        # --- ABA 4: AVARIAS ---
        with aba_avaria:
            st.subheader("🗑️ Controle de Desperdício")
            if not df_avarias.empty:
                st.write("Monitoramento de perdas por produto e data.")
            else:
                st.info("Registre as perdas diárias no arquivo 'avarias.csv' para reduzir o prejuízo.")

else:
    st.info("🚀 RotiFácil Performance: Aguardando sincronização com o banco de dados...")