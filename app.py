import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_CMV_FIXO = 0.2925 

# --- TABELA DE CONTROLE MANUAL (VENDA E CUSTO) ---
TABELA_GERENCIAL = {
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
    "FRANGO ASSADO KG": {"venda": 29.90, "custo": 14.00},
    "FRANGO ASSADO": {"venda": 29.90, "custo": 14.00},
}

# --- ESTILIZAÇÃO (FONTES AMPLIADAS) ---
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
    datas_sel = st.date_input("📅 Período de Análise:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas_sel) == 2:
        ini, fim = datas_sel
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()

        aba_perf, aba_vendas, aba_abc, aba_ruptura, aba_avaria = st.tabs([
            "📈 Performance & Margem", "📊 Visão Diária", "🏆 Curva ABC", "🚨 Ruptura", "🗑️ Avaria"
        ])

        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- ABA PERFORMANCE ---
        with aba_perf:
            st.subheader("🚀 Indicadores de Performance")
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
                st.write("**🏆 Top 3 Faturamento (Real)**")
                top3 = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().nlargest(3)
                for i, (p, v) in enumerate(top3.items(), 1): st.write(f"{i}º - {p} ({fmt(v)})")

            st.divider()
            st.subheader("💰 Lucratividade Gerencial")
            v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
            v_prod['PV_Unit'] = v_prod.apply(lambda r: TABELA_GERENCIAL.get(r['Produto'], {}).get('venda', r['Valor_Final']/r['Qtd_KG'] if r['Qtd_KG'] > 0 else 0), axis=1)
            v_prod['Custo_Unit'] = v_prod['Produto'].apply(lambda x: TABELA_GERENCIAL.get(x, {}).get('custo', 0.0))
            v_prod['Fat_Gerencial'] = v_prod['Qtd_KG'] * v_prod['PV_Unit']
            v_prod['Lucro_Liq'] = v_prod['Fat_Gerencial'] - (v_prod['Fat_Gerencial'] * IMPOSTO_CMV_FIXO) - (v_prod['Qtd_KG'] * v_prod['Custo_Unit'])
            v_prod['Margem_%'] = (v_prod['Lucro_Liq'] / v_prod['Fat_Gerencial']) * 100
            st.dataframe(v_prod.sort_values('Lucro_Liq', ascending=False)[['Produto', 'Fat_Gerencial', 'Lucro_Liq', 'Margem_%']].style.format({'Fat_Gerencial': fmt, 'Lucro_Liq': fmt, 'Margem_%': '{:.2f}%'}))

        # --- ABA VISÃO DIÁRIA ---
        with aba_vendas:
            st.subheader("📊 Faturamento por Dia")
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

        # --- ABA CURVA ABC (REATIVADA) ---
        with aba_abc:
            st.subheader("🏆 Classificação de Produtos (Período)")
            abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            if not abc.empty:
                abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
                abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                st.table(abc[['Curva', 'Produto', 'Valor_Final']].map(lambda x: fmt(x) if isinstance(x, float) else x))

        # --- ABA RUPTURA (REATIVADA) ---
        with aba_ruptura:
          st.subheader("🚨 Analisador de Ruptura por Fluxo Horário")
          st.write("Identifique se a venda de produtos Classe A parou antes do horário de fechamento.")

    # 1. Verificamos se a coluna 'Hora' existe (vinda do robô atualizado)
    if 'Hora' in df_filt.columns:
        # 2. Calculamos a Classe A dinamicamente para garantir que a variável exista
        vendas_abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
        if not vendas_abc.empty:
            vendas_abc['% Acum'] = (vendas_abc['Valor_Final'] / vendas_abc['Valor_Final'].sum()).cumsum() * 100
            lista_classe_a = vendas_abc[vendas_abc['% Acum'] <= 80]['Produto'].tolist()
            
            if not lista_classe_a: # Caso não tenha Classe A definida
                lista_classe_a = vendas_abc['Produto'].head(5).tolist()

            # 3. Seletor de Produto (Corrigido)
            prod_analise = st.selectbox("Selecione um item Classe A para auditar o fluxo:", lista_classe_a)
            
            if prod_analise:
                df_hora = df_filt[df_filt['Produto'] == prod_analise].copy()
                fluxo_hora = df_hora.groupby('Hora')['Valor_Final'].sum().reset_index().sort_values('Hora')
                
                # Exibe o gráfico de linha (Pulsação da Venda)
                st.line_chart(fluxo_hora.set_index('Hora')['Valor_Final'])
                
                # 4. Lógica de Alerta (Baseado no horário comercial da rotisseria)
                if not fluxo_hora.empty:
                    ultima_h = int(fluxo_hora['Hora'].max())
                    if ultima_h < 13:
                        st.error(f"⚠️ **POSSÍVEL RUPTURA:** {prod_analise} parou de vender às {ultima_h}h. Verifique se a bandeja acabou antes do almoço terminar.")
                    else:
                        st.success(f"✅ Fluxo Normal: Venda registrada até às {ultima_h}h.")
        else:
            st.info("Aguardando dados de vendas para calcular a Classe A.")
    else:
        st.warning("⚠️ **Atenção:** A coluna 'Hora' ainda não está no arquivo. Certifique-se de que o robô já rodou com o novo SQL.")
        st.info("A lógica de ruptura por horário precisa que o robô extraia o campo TO_CHAR(M.DTMOV, 'HH24').")

        # --- ABA AVARIA (REATIVADA) ---
        with aba_avaria:
            st.subheader("🗑️ Controle de Desperdício")
            if not df_avarias.empty:
                st.dataframe(df_avarias)
            else:
                st.info("Nenhuma avaria registrada no arquivo avarisas.csv.")

else: st.info("Sincronizando dados com o WinThor...")