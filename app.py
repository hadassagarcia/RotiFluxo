import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_CMV_FIXO = 0.2925 
TABELA_PRECOS_CUSTOS = {
    "EMPADAO FRANGO KG": {"venda": 45.90, "custo": 18.50},
    "CUSCUZ C/ CARNE MOIDA KG": {"venda": 32.00, "custo": 12.00},
    "LASANHA FRANGO KG": {"venda": 48.00, "custo": 19.80},
    "PATE FRANGO KG": {"venda": 38.00, "custo": 14.50},
    "SOPA CARNE KG": {"venda": 25.00, "custo": 9.50},
    "LASANHA CARNE MOIDA KG": {"venda": 52.00, "custo": 22.00},
    "CUSCUZ C/ SALSICHA KG": {"venda": 22.00, "custo": 7.50},
    "MACAXEIRA C/ CALABRESA ACEB KG": {"venda": 28.00, "custo": 11.00},
    "CARNE C/ MACAXEIRA KG": {"venda": 42.00, "custo": 16.50},
    "BAIAO DE DOIS CF KG": {"venda": 35.00, "custo": 13.00},
}

# ESTILIZAÇÃO
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# CARGA DE DADOS
@st.cache_data(ttl=60)
def carregar(arq):
    try:
        url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{arq}?v={int(time.time())}"
        df = pd.read_csv(url)
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except: return pd.DataFrame()

unidade = st.sidebar.selectbox("🏢 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
df_base = carregar("vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv")
df_avarias = carregar("avarias.csv")

if not df_base.empty:
    st.title(f"RotiFácil - {unidade}")
    
    # --- STATUS DA META (Sempre Fixo no Topo - Acumulado do Mês) ---
    fat_mes_atual = df_base[df_base['CODOPER'] == 'S']['Valor_Final'].sum()
    progresso = min(fat_mes_atual / META_FATURAMENTO, 1.0)
    
    st.subheader(f"🎯 Status de Performance (Meta Mensal: R$ {META_FATURAMENTO:,.2f})")
    st.progress(progresso)
    st.write(f"Acumulado no Mês: **R$ {fat_mes_atual:,.2f}** ({progresso*100:.1f}%)")

    # --- SELETOR DE DATAS (Controla as abas abaixo) ---
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
            st.subheader("🚀 Indicadores do Período Selecionado")
            c1, c2 = st.columns(2)
            with c1:
                v_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
                st.metric("Venda no Período", fmt(v_periodo))
            with c2:
                st.write("**🏆 Top 3 do Período**")
                top3 = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().nlargest(3)
                for i, (p, v) in enumerate(top3.items(), 1): st.write(f"{i}º - {p} ({fmt(v)})")

            st.divider()
            st.subheader("💰 Lucratividade do Período")
            v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
            v_prod['Custo_U'] = v_prod['Produto'].apply(lambda x: TABELA_PRECOS_CUSTOS.get(x, {}).get('custo', 0))
            v_prod['Lucro_Liq'] = v_prod['Valor_Final'] - (v_prod['Valor_Final'] * IMPOSTO_CMV_FIXO) - (v_prod['Qtd_KG'] * v_prod['Custo_U'])
            v_prod['Margem_%'] = (v_prod['Lucro_Liq'] / v_prod['Valor_Final']) * 100
            st.dataframe(v_prod[v_prod['Custo_U'] > 0].sort_values('Lucro_Liq', ascending=False)[['Produto', 'Valor_Final', 'Lucro_Liq', 'Margem_%']].style.format({'Valor_Final': fmt, 'Lucro_Liq': fmt, 'Margem_%': '{:.2f}%'}))

        # --- ABA VISÃO DIÁRIA (REFORMULADA) ---
        with aba_vendas:
            st.subheader("📊 Faturamento por Dia e Produto")
            df_filt['Val'] = df_filt.apply(lambda r: r['Valor_Final'] if r['CODOPER'] == 'S' else -r['Valor_Final'], axis=1)
            
            # Formatação da data: "13/04 Seg"
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Data_Rotulo'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} {dias_pt[d.weekday()]}")
            
            # Criar Tabela Pivot
            tab = pd.pivot_table(df_filt, values='Val', index='Produto', columns='Data_Rotulo', aggfunc='sum', fill_value=0)
            
            if not tab.empty:
                # Ordenar colunas cronologicamente
                ordem_cols = sorted(df_filt['Data_Rotulo'].unique(), key=lambda x: x[:5])
                tab = tab.reindex(columns=ordem_cols)
                
                # Totais Horizontais e Verticais
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
            st.info("Monitorando produtos Classe A que não registraram vendas na data final selecionada.")
            classe_a = abc[abc['Curva'] == 'A']['Produto'].tolist()
            vendas_ultimo_dia = df_filt[df_filt['Data_Date'] == fim]['Produto'].unique()
            rupturas = [p for p in classe_a if p not in vendas_ultimo_dia]
            if rupturas: st.warning(f"Possível Ruptura detectada em: {', '.join(rupturas)}")
            else: st.success("Nenhuma ruptura detectada no encerramento do período.")

        # --- ABA AVARIA ---
        with aba_avaria:
            st.subheader("🗑️ Controle de Avaria")
            if not df_avarias.empty: st.dataframe(df_avarias)
            else: st.info("Sem registros de avaria para o período.")

else: st.info("Sincronizando dados...")
