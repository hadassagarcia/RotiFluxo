import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925  # 29,25% sobre o Preço de Venda

# --- TABELA DE PRECIFICAÇÃO ATUALIZADA (DADOS DA PLANILHA) ---
# Estrutura: "PRODUTO": [Custo_Base, Preco_Venda]
PRECIFICACAO_REAL = {
    "ARROZ C/ CREME FRANGO KG": [16.39, 33.99],
    "ARROZ CREMOSO FRANGO KG": [16.44, 39.99],
    "ARROZ LEITE C/ CARNE SOL KG": [15.05, 41.99],
    "BAIAO DE DOIS CF KG": [16.99, 34.99],
    "CARNE C/ MACAXEIRA KG": [0.00, 29.99], # Custo base não informado na imagem
    "CUSCUZ C/ CARNE KG": [14.90, 29.99],
    "CUSCUZ C/ CARNE MOIDA KG": [10.23, 25.99],
    "CUSCUZ C/ SALSICHA KG": [7.90, 22.99],
    "EMPADAO CARNE SOL KG": [21.82, 54.99],
    "EMPADAO FRANGO KG": [16.69, 49.99],
    "ESCONDIDINHO CARNE MOIDA KG": [17.18, 39.99],
    "FRANGO ASSADO CORTE FACIL KG": [23.92, 34.99],
    "LASANHA CARNE MOIDA KG": [21.24, 39.99],
    "LASANHA FRANGO KG": [25.41, 39.99],
    "MACAXEIRA C/ CALABRESA ACEB KG": [9.89, 29.99],
    "PATE FRANGO KG": [21.85, 39.99],
    "SOPA CARNE KG": [8.71, 29.99],
    "TAPIOCA CARNE SOL KG": [21.05, 45.99],
    "TAPIOCA FRANGO KG": [15.30, 41.99],
    "TAPIOCA MISTA KG": [14.32, 47.99],
    "TAPIOCA QUEIJO KG": [19.54, 47.99],
}

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: bold; color: #1E3A8A; }
    button[data-baseweb="tab"] p { font-size: 20px !important; font-weight: 600 !important; }
    label[data-testid="stWidgetLabel"] p { font-size: 18px !important; font-weight: bold !important; }
    .stDataFrame td, .stDataFrame th { font-size: 16px !important; }
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

    # --- SELETOR DE DATAS ---
    hoje_dados = df_base['Data_Date'].max()
    datas_sel = st.date_input("📅 Selecione o Período de Análise:", value=(hoje_dados.replace(day=1), hoje_dados), max_value=hoje_dados)

    if len(datas_sel) == 2:
        ini, fim = datas_sel
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # --- STATUS DA META DINÂMICO ---
        fat_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
        progresso = min(fat_periodo / META_FATURAMENTO, 1.0)
        st.subheader(f"🎯 Performance no Período (Meta: R$ {META_FATURAMENTO:,.2f})")
        st.progress(progresso)
        st.write(f"Total Vendido: **R$ {fat_periodo:,.2f}** ({progresso*100:.1f}%)")

        st.divider()

        aba_perf, aba_vendas, aba_abc, aba_ruptura, aba_avaria = st.tabs([
            "📈 Margem Real", "📊 Visão Diária", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA PERFORMANCE & MARGEM REAL ---
        with aba_perf:
            st.subheader("🚀 Análise de Lucratividade (Baseada na Planilha de Precificação)")
            v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
            
            if not v_prod.empty:
                # 1. Puxar Custo e Preço do Dicionário
                v_prod['Custo_Base_Unit'] = v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[0])
                v_prod['Preco_Venda_Unit'] = v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[1])
                
                # 2. Cálculos conforme a planilha
                v_prod['Faturamento_Gerencial'] = v_prod['Qtd_KG'] * v_prod['Preco_Venda_Unit']
                v_prod['Imposto_Total'] = v_prod['Faturamento_Gerencial'] * IMPOSTO_PERCENTUAL
                v_prod['Custo_Total_Materia_Prima'] = v_prod['Qtd_KG'] * v_prod['Custo_Base_Unit']
                
                v_prod['Lucro_R$'] = v_prod['Faturamento_Gerencial'] - v_prod['Imposto_Total'] - v_prod['Custo_Total_Materia_Prima']
                
                # Margem Real %
                v_prod['Margem_Real'] = v_prod.apply(lambda r: (r['Lucro_R$'] / r['Faturamento_Gerencial'] * 100) if r['Faturamento_Gerencial'] > 0 else 0, axis=1)
                
                # Exibição
                df_mostrar = v_prod.sort_values('Lucro_R$', ascending=False)[['Produto', 'Faturamento_Gerencial', 'Lucro_R$', 'Margem_Real']]
                
                st.dataframe(df_mostrar.style.format({
                    'Faturamento_Gerencial': fmt, 
                    'Lucro_R$': fmt, 
                    'Margem_Real': '{:.2f}%'
                }).map(lambda x: 'color: red; font-weight: bold' if isinstance(x, float) and x < 10 else None, subset=['Margem_Real']), 
                use_container_width=True)
                
                st.caption("⚠️ Margens em vermelho estão abaixo de 10% (Crítico).")

        # --- ABA VISÃO DIÁRIA ---
        with aba_vendas:
            df_filt['Val'] = df_filt['Valor_Final']
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Data_Rotulo'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} {dias_pt[d.weekday()]}")
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Data_Rotulo', aggfunc='sum', fill_value=0)
            if not tab.empty:
                ordem_cols = sorted(df_filt['Data_Rotulo'].unique(), key=lambda x: x[:5])
                tab = tab.reindex(columns=ordem_cols)
                tab['TOTAL'] = tab.sum(axis=1)
                tab = tab.sort_values('TOTAL', ascending=False)
                tab.loc['TOTAL DIA ➔'] = tab.sum(axis=0)
                st.dataframe(tab.map(fmt), use_container_width=True)

        # --- ABA CURVA ABC ---
        with aba_abc:
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            if not abc.empty:
                abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
                abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                st.table(abc[['Curva', 'Produto', 'Valor_Final']].map(lambda x: fmt(x) if isinstance(x, float) else x))

        # --- ABA RUPTURA ---
        with aba_ruptura:
            if 'Hora' in df_filt.columns:
                vendas_abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
                if not vendas_abc.empty:
                    lista_a = vendas_abc.head(10)['Produto'].tolist()
                    prod_analise = st.selectbox("Auditar Fluxo Horário (Dia Final):", lista_a)
                    df_hora = df_filt[(df_filt['Produto'] == prod_analise) & (df_filt['Data_Date'] == fim)].copy()
                    if not df_hora.empty:
                        fluxo_hora = df_hora.groupby('Hora')['Valor_Final'].sum().reset_index().sort_values('Hora')
                        st.line_chart(fluxo_hora.set_index('Hora')['Valor_Final'])
                        ult_h = int(fluxo_hora['Hora'].max())
                        if ult_h < 13: st.error(f"Ruptura! Parou de vender às {ult_h}h.")
                        else: st.success(f"Fluxo normal até às {ult_h}h.")

        # --- ABA AVARIA ---
        with aba_avaria:
            st.subheader("🗑️ Radar de Avaria")
            if not df_avarias.empty:
                st.dataframe(df_avarias)
            else: st.info("Sem avarias registradas.")

else: st.info("Sincronizando dados...")