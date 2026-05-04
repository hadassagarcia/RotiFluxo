import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_CMV_FIXO = 0.2925 

# --- TABELA DE CONTROLE MANUAL ---
TABELA_GERENCIAL = {
    "EMPADAO FRANGO KG": {"venda": 45.90, "custo": 18.50},
    "CUSCUZ C/ CARNE MOIDA KG": {"venda": 32.00, "custo": 12.00},
    "LASANHA FRANGO KG": {"venda": 48.00, "custo": 19.80},
    "PATE FRANGO KG": {"venda": 38.00, "custo": 14.50},
    "SOPA CARNE KG": {"venda": 25.00, "custo": 9.50},
    "LASANHA CARNE MOIDA KG": {"venda": 49.99, "custo": 21.00},
    "CUSCUZ C/ SALSICHA KG": {"venda": 22.00, "custo": 7.50},
    "MACAXEIRA C/ CALABRESA ACEB KG": {"venda": 28.00, "custo": 11.00},
    "CARNE C/ MACAXEIRA KG": {"venda": 42.00, "custo": 16.50},
    "BAIAO DE DOIS CF KG": {"venda": 35.00, "custo": 13.00},
    "FRANGO ASSADO CORTE FACIL KG": {"venda": 34.99, "custo": 25.84},
    "FRANGO ASSADO": {"venda": 29.90, "custo": 14.00},
}

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: bold; }
    button[data-baseweb="tab"] p { font-size: 20px !important; font-weight: 600 !important; }
    label[data-testid="stWidgetLabel"] p { font-size: 20px !important; font-weight: bold !important; }
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

    # 1. SELETOR DE DATAS (Movido para cima para tornar o resto dinâmico)
    hoje_dados = df_base['Data_Date'].max()
    datas_sel = st.date_input("📅 Selecione o Período de Análise:", value=(hoje_dados.replace(day=1), hoje_dados), max_value=hoje_dados)

    if len(datas_sel) == 2:
        ini, fim = datas_sel
        # Filtragem principal que alimenta TODO o dashboard
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        # --- STATUS DA META DINÂMICO ---
        # Agora ele soma o que foi filtrado no calendário
        fat_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
        progresso = min(fat_periodo / META_FATURAMENTO, 1.0)
        
        st.subheader(f"🎯 Performance no Período (Meta: R$ {META_FATURAMENTO:,.2f})")
        st.progress(progresso)
        
        # Texto dinâmico que avisa qual período está sendo somado
        st.write(f"Total Vendido entre **{ini.strftime('%d/%m')}** e **{fim.strftime('%d/%m')}**: **R$ {fat_periodo:,.2f}** ({progresso*100:.1f}%)")

        st.divider()

        aba_perf, aba_vendas, aba_abc, aba_ruptura, aba_avaria = st.tabs([
            "📈 Margem", "📊 Visão Diária", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA PERFORMANCE ---
        with aba_perf:
            v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
            if not v_prod.empty:
                v_prod['PV_Unit'] = v_prod.apply(lambda r: TABELA_GERENCIAL.get(r['Produto'], {}).get('venda', r['Valor_Final']/r['Qtd_KG'] if r['Qtd_KG'] > 0 else 0), axis=1)
                v_prod['Custo_Unit'] = v_prod['Produto'].apply(lambda x: TABELA_GERENCIAL.get(x, {}).get('custo', 0.0))
                v_prod['Faturamento_Gerencial'] = v_prod['Qtd_KG'] * v_prod['PV_Unit']
                v_prod['Lucro_Liq'] = v_prod['Faturamento_Gerencial'] - (v_prod['Faturamento_Gerencial'] * IMPOSTO_CMV_FIXO) - (v_prod['Qtd_KG'] * v_prod['Custo_Unit'])
                v_prod['Margem_%'] = v_prod.apply(lambda r: (r['Lucro_Liq'] / r['Faturamento_Gerencial'] * 100) if r['Faturamento_Gerencial'] > 0 else 0, axis=1)
                st.dataframe(v_prod.sort_values('Lucro_Liq', ascending=False)[['Produto', 'Faturamento_Gerencial', 'Lucro_Liq', 'Margem_%']].style.format({
                    'Faturamento_Gerencial': fmt, 'Lucro_Liq': fmt, 'Margem_%': '{:.2f}%'
                }), use_container_width=True)

        # --- ABA VISÃO DIÁRIA ---
        with aba_vendas:
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
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
                    vendas_abc['% Acum'] = (vendas_abc['Valor_Final'] / vendas_abc['Valor_Final'].sum()).cumsum() * 100
                    lista_classe_a = vendas_abc[vendas_abc['% Acum'] <= 80]['Produto'].tolist()
                    prod_analise = st.selectbox("Selecione um item Classe A:", lista_classe_a if lista_classe_a else vendas_abc['Produto'].head(5).tolist())
                    df_hora = df_filt[(df_filt['Produto'] == prod_analise) & (df_filt['Data_Date'] == fim)].copy()
                    if not df_hora.empty:
                        fluxo_hora = df_hora.groupby('Hora')['Valor_Final'].sum().reset_index().sort_values('Hora')
                        st.line_chart(fluxo_hora.set_index('Hora')['Valor_Final'])
                        ultima_h = int(fluxo_hora['Hora'].max())
                        if ultima_h < 13: st.error(f"Ruptura Detectada às {ultima_h}h no dia {fim.strftime('%d/%m')}.")
                        else: st.success(f"Fluxo Normal até às {ultima_h}h.")

        # --- ABA AVARIA ---
        with aba_avaria:
            st.dataframe(df_avarias) if not df_avarias.empty else st.info("Sem avarias.")

else: st.info("Sincronizando dados...")