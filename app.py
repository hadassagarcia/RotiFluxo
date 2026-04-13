import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_CMV_FIXO = 0.2925 

# --- CADASTRO MANUAL DE PREÇOS E CUSTOS ---
# Adicione os custos aqui. O que não estiver aqui, o sistema assume custo 0 para você completar depois.
TABELA_PRECOS_CUSTOS = {
    "EMPADAO FRANGO KG": {"custo": 18.50},
    "CUSCUZ C/ CARNE MOIDA KG": {"custo": 12.00},
    "LASANHA FRANGO KG": {"custo": 19.80},
    "PATE FRANGO KG": {"custo": 14.50},
    "SOPA CARNE KG": {"custo": 9.50},
    "LASANHA CARNE MOIDA KG": {"custo": 22.00},
    "CUSCUZ C/ SALSICHA KG": {"custo": 7.50},
    "MACAXEIRA C/ CALABRESA ACEB KG": {"custo": 14.00},
    "CARNE C/ MACAXEIRA KG": {"custo": 16.50},
    "BAIAO DE DOIS CF KG": {"custo": 18.00},
    "FRANGO ASSADO KG": {"custo": 24.00},
    "FRANGO ASSADO METADE KG": {"custo": 24.00},
}

# --- ESTILIZAÇÃO PARA ACESSIBILIDADE ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 18px !important; }
    button[data-baseweb="tab"] p { font-size: 20px !important; font-weight: 600 !important; }
    label[data-testid="stWidgetLabel"] p { font-size: 18px !important; font-weight: bold !important; }
    .stDataFrame td, .stDataFrame th { font-size: 16px !important; }
    .stMarkdown p { font-size: 18px !important; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DADOS ---
@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except: return pd.DataFrame()

unidade = st.sidebar.selectbox("Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
df_base = carregar("vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv")
df_avarias = carregar("avarias.csv")

if not df_base.empty:
    st.title(f"🍗 RotiFácil - {unidade}")
    
    # --- STATUS DA META ---
    fat_mes_atual = df_base[df_base['CODOPER'] == 'S']['Valor_Final'].sum()
    progresso = min(fat_mes_atual / META_FATURAMENTO, 1.0)
    st.subheader(f"🎯 Status de Performance (Meta: R$ {META_FATURAMENTO:,.2f})")
    st.progress(progresso)
    st.write(f"Acumulado no Mês: **R$ {fat_mes_atual:,.2f}** ({progresso*100:.1f}%)")

    st.divider()
    hoje = df_base['Data_Date'].max()
    primeiro_dia = hoje.replace(day=1)
    datas_sel = st.date_input("📅 Selecione o período para análise detalhada:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas_sel) == 2:
        ini, fim = datas_sel
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()

        aba_perf, aba_vendas, aba_abc, aba_ruptura, aba_avaria = st.tabs([
            "📈 Performance & Margem", "📊 Visão Diária", "🏆 Curva ABC", "🚨 Ruptura", "🗑️ Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA PERFORMANCE ---
        with aba_perf:
            st.subheader("🚀 Projeções da Performance Semanal")
            c1, c2 = st.columns(2)
            with c1:
                sem_atual = df_base[df_base['Data_Date'] >= (hoje - timedelta(days=7))]['Valor_Final'].sum()
                sem_ant = df_base[(df_base['Data_Date'] >= (hoje - timedelta(days=14))) & (df_base['Data_Date'] < (hoje - timedelta(days=7)))]['Valor_Final'].sum()
                if sem_ant > 0:
                    delta = ((sem_atual - sem_ant) / sem_ant) * 100
                    st.metric("Venda Últimos 7 Dias", fmt(sem_atual), delta=f"{delta:.2f}%")
                else:
                    st.metric("Venda Últimos 7 Dias", fmt(sem_atual))
            
            with c2:
                st.write("**🏆 Top 3 Mais Vendidos (Faturamento)**")
                top3 = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().nlargest(3)
                for i, (p, v) in enumerate(top3.items(), 1): st.write(f"{i}º - {p} ({fmt(v)})")

            st.divider()
            st.subheader("💰 Análise de Lucratividade")
            
            # Agrupamento por produto (Pega TODOS)
            v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
            
            # Puxa custos (se não achar, coloca 0.0)
            v_prod['Custo_U'] = v_prod['Produto'].apply(lambda x: TABELA_PRECOS_CUSTOS.get(x, {}).get('custo', 0.0))
            
            # Cálculos Financeiros
            v_prod['Imposto_CMV'] = v_prod['Valor_Final'] * IMPOSTO_CMV_FIXO
            v_prod['Custo_Total'] = v_prod['Qtd_KG'] * v_prod['Custo_U']
            v_prod['Lucro_Liquido'] = v_prod['Valor_Final'] - v_prod['Imposto_CMV'] - v_prod['Custo_Total']
            v_prod['Margem_%'] = (v_prod['Lucro_Liquido'] / v_prod['Valor_Final']) * 100
            
            # Mostra TODOS os produtos vendidos
            st.dataframe(v_prod.sort_values('Lucro_Liquido', ascending=False)[['Produto', 'Valor_Final', 'Lucro_Liquido', 'Margem_%']].style.format({
                'Valor_Final': fmt, 'Lucro_Liquido': fmt, 'Margem_%': '{:.2f}%'
            }), use_container_width=True)

        # --- ABA VISÃO DIÁRIA ---
        with aba_vendas:
            st.subheader("📊 Faturamento por Dia e Produto")
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Data_Rotulo'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} {dias_pt[d.weekday()]}")
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Data_Rotulo', aggfunc='sum', fill_value=0)
            
            if not tab.empty:
                ordem_cols = sorted(df_filt['Data_Rotulo'].unique(), key=lambda x: x[:5])
                tab = tab.reindex(columns=ordem_cols)
                tab['TOTAL PRODUTO'] = tab.sum(axis=1)
                tab = tab.sort_values('TOTAL PRODUTO', ascending=False)
                tab.loc['TOTAL DIA ➔'] = tab.sum(axis=0)
                st.dataframe(tab.map(fmt), use_container_width=True)

        # --- ABA ABC ---
        with aba_abc:
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            abc['%'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
            abc['Curva'] = abc['%'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            st.table(abc[['Curva', 'Produto', 'Valor_Final']].map(lambda x: fmt(x) if isinstance(x, float) else x))

        # --- ABA RUPTURA ---
        with aba_ruptura:
            st.subheader("🚨 Verificação de Ruptura")
            classe_a = abc[abc['Curva'] == 'A']['Produto'].tolist()
            vendas_fim = df_filt[df_filt['Data_Date'] == fim]['Produto'].unique()
            faltantes = [p for p in classe_a if p not in vendas_fim]
            if faltantes: st.warning(f"Produtos Classe A sem venda no último dia: {', '.join(faltantes)}")
            else: st.success("Principais produtos com venda registrada no fechamento do período.")

        # --- ABA AVARIA ---
        with aba_avaria:
            st.subheader("🗑️ Histórico de Avaria")
            if not df_avarias.empty: st.dataframe(df_avarias)
            else: st.info("Sem dados de avaria no período selecionado.")

else: st.info("Carregando dados de performance...")
