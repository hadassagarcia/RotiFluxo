import streamlit as st
import pandas as pd
from datetime import timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="RotiFluxo", layout="wide")

st.title("Análise de Vendas - Rotisseria")

# 2. FUNÇÃO DE CARGA DE DADOS (LÊ O CSV GERADO PELO SEU PC)
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv("vendas_filial2.csv")
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao ler dados: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

if not df_base.empty:
    # --- FILTROS ---
    st.subheader("📅 Filtros de Análise")
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        data_max = df_base['Data'].max()
        data_ini_padrao = data_max - timedelta(days=6)
        datas = st.date_input("Selecione o Intervalo:", value=(data_ini_padrao, data_max))

    if len(datas) == 2:
        ini, fim = datas
        df = df_base[(df_base['Data'] >= ini) & (df_base['Data'] <= fim)].copy()
        
        # --- CÁLCULOS DOS KPIs (VALORES TOTAIS) ---
        
        # Venda para Filial 5 (Cliente 6613)
        venda_f5 = df[(df['CODOPER'] == 'S') & (df['CODCLI'] == 6613)]['Valor_Final'].sum()
        
        # Venda Líquida Loja (Balcão: Vendas - Devoluções, excluindo cliente 6613)
        df_loja_vendas = df[(df['CODOPER'] == 'S') & (df['CODCLI'] != 6613)]['Valor_Final'].sum()
        df_loja_devol  = df[(df['CODOPER'].isin(['E', 'ED'])) & (df['CODCLI'] != 6613)]['Valor_Final'].sum()
        fat_liquido_loja = df_loja_vendas - df_loja_devol
        
        # --- EXIBIÇÃO DOS INDICADORES DE TOPO ---
        st.subheader("💰 Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        
        def fmt(v): 
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        c1.metric("🛒 VENDA LÍQUIDA (Loja)", fmt(fat_liquido_loja))
        c2.metric("🏪 VENDA FILIAL 5", fmt(venda_f5))
        c3.metric("📊 FATURAMENTO TOTAL", fmt(fat_liquido_loja + venda_f5))

        st.divider()

        # --- VISÃO DIÁRIA: FOCO NO CONSUMO LOCAL (BALCÃO) ---
        st.subheader("🗓️ Visão Diária: Giro Real da Loja")
        st.info("Os dados abaixo mostram apenas o consumo dos seus clientes locais (exclui transferências para a Filial 5).")
        
        # Preparação de datas e nomes dos dias
        dias_pt = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        df['Dia'] = df['Data'].apply(lambda d: f"{dias_pt[d.weekday()]} ({d.strftime('%d/%m')})")
        ordem_dias = df.sort_values('Data')['Dia'].unique()

        # Criar coluna de Valor Líquido apenas para a Loja
        def calc_valor_loja(linha):
            if linha['CODCLI'] == 6613: return 0 # Zera o que foi pro Planalto
            if linha['CODOPER'] == 'S': return linha['Valor_Final']
            if linha['CODOPER'] in ['E', 'ED']: return -linha['Valor_Final']
            return 0

        df['V_Liq_Loja'] = df.apply(calc_valor_loja, axis=1)

        # TABELA PIVOTADA (LOJA APENAS)
        tab_loja = pd.pivot_table(
            df[df['V_Liq_Loja'] != 0], 
            values='V_Liq_Loja', 
            index='Produto', 
            columns='Dia', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Ordenar e formatar
        if not tab_loja.empty:
            tab_loja = tab_loja.reindex(columns=ordem_dias)
            tab_loja['Total Loja'] = tab_loja.sum(axis=1)
            tab_loja = tab_loja.sort_values('Total Loja', ascending=False)
            
            # Exibição da Tabela
            st.dataframe(tab_loja.map(fmt), use_container_width=True)

            # GRÁFICO DE LINHAS (TENDÊNCIA DA LOJA)
            # --- GRÁFICO DE LINHAS (TENDÊNCIA DA LOJA COM ORDEM CRONOLÓGICA) ---
            st.subheader("📈 Tendência Diária de Vendas (Loja)")
            
            # 1. Criamos a pivot table usando a DATA REAL (datetime) como índice
            # Isso garante que a ordem no gráfico seja 01, 02, 03...
            graf_dados = pd.pivot_table(
                df[df['V_Liq_Loja'] != 0], 
                values='V_Liq_Loja', 
                index='Data',  # USANDO A DATA AQUI (Índice cronológico)
                columns='Produto', 
                aggfunc='sum', 
                fill_value=0
            )

            # 2. Agora, trocamos o índice de 'Data' para 'Dia' (o texto bonito) 
            # apenas para exibição no gráfico, sem perder a ordem que o Pandas já criou
            mapa_dias = df.set_index('Data')['Dia'].to_dict()
            graf_dados.index = graf_dados.index.map(mapa_dias)

            # 3. Plota o gráfico com a ordem corrigida
            st.line_chart(graf_dados)
            
            
        else:
            st.warning("Sem vendas registradas na loja para este período.")

else:
    st.warning("⚠️ Aguardando dados sincronizados do WinThor...")