import streamlit as st
import pandas as pd
from datetime import timedelta
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="RotiFluxo", layout="wide", page_icon="🍗")

st.title("Análise de Vendas - Rotisseria")

# 2. FUNÇÃO DE CARGA DE DADOS (FORÇANDO ATUALIZAÇÃO)
@st.cache_data(ttl=60) # Diminuí para 60 segundos para ser mais rápido
def carregar_dados():
    try:
        # Usamos o link "raw" (bruto) do GitHub com um parâmetro de tempo no final
        # Isso engana o servidor e força ele a baixar o arquivo novo toda vez
        url = "https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/vendas_filial2.csv"
        url_com_timestamp = f"{url}?v={int(time.time())}"
        
        df = pd.read_csv(url_com_timestamp)
        
        # Criar coluna de data real para ordenação rigorosa
        df['Data_Ref'] = pd.to_datetime(df['Data'])
        df['Data_Date'] = df['Data_Ref'].dt.date
        return df
    except Exception as e:
        # Se falhar o link externo, tenta ler o local como backup
        try:
            df = pd.read_csv("vendas_filial2.csv")
            df['Data_Ref'] = pd.to_datetime(df['Data'])
            df['Data_Date'] = df['Data_Ref'].dt.date
            return df
        except:
            st.error(f"⚠️ Erro ao carregar dados: {e}")
            return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    # --- SEÇÃO DE FILTROS ---
    st.subheader("📅 Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        # Pegamos a data máxima real que está no arquivo
        data_max = df_base['Data_Date'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        
        # O widget de data agora vai até a data máxima encontrada (dia 08)
        datas = st.date_input("Selecione o Intervalo:", 
                              value=(data_ini_padrao, data_max),
                              max_value=data_max)

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia_Exibicao'] = df['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
        
        # --- CÁLCULOS DOS KPIs ---
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        def calc_valor_loja(linha):
            if linha['CODCLI'] == 6613: return 0
            if linha['CODOPER'] == 'S': return linha['Valor_Final']
            if linha['CODOPER'] in ['E', 'ED']: return -linha['Valor_Final']
            return 0

        df['V_Liq_Loja'] = df.apply(calc_valor_loja, axis=1)
        fat_liquido_loja = df['V_Liq_Loja'].sum()
        
        # --- EXIBIÇÃO DOS CARDS ---
        st.subheader("💰 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("🛒 VENDA LÍQUIDA (Loja)", fmt(fat_liquido_loja))
        c2.metric("🏪 VENDA FILIAL 5", fmt(venda_f5))
        c3.metric("📊 FATURAMENTO TOTAL", fmt(fat_liquido_loja + venda_f5))

        st.divider()

        # --- TABELA E GRÁFICO ---
        tab_dados = pd.pivot_table(
            df[df['V_Liq_Loja'] != 0], 
            values='V_Liq_Loja', 
            index='Data_Ref', 
            columns='Produto', 
            aggfunc='sum', 
            fill_value=0
        ).sort_index()

        if not tab_dados.empty:
            mapa_nomes = df.sort_values('Data_Ref').set_index('Data_Ref')['Dia_Exibicao'].to_dict()
            
            st.subheader("🗓️ Visão Diária: Giro Real da Loja")
            tab_visual = tab_dados.T
            tab_visual.columns = [mapa_nomes[c] for c in tab_visual.columns]
            tab_visual['Total Loja'] = tab_visual.sum(axis=1)
            tab_visual = tab_visual.sort_values('Total Loja', ascending=False)
            st.dataframe(tab_visual.map(fmt), use_container_width=True)

            st.subheader("📈 Tendência Diária de Vendas (Loja)")
            graf_dados = tab_dados.copy()
            graf_dados.index = [mapa_nomes[i] for i in graf_dados.index]
            st.line_chart(graf_dados)
        else:
            st.warning("Sem dados para o período.")
else:
    st.info("🚀 Aguardando sincronização de dados...")