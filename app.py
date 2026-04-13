import streamlit as st
import pandas as pd
from datetime import timedelta
import time

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="RotiFácil", layout="wide", page_icon="🍗")

# --- BARRA LATERAL ---
st.sidebar.title("🏢 Unidade")
unidade = st.sidebar.selectbox("Escolha a Loja:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

@st.cache_data(ttl=30)
def carregar_dados(loja):
    nome_arq = "vendas_filial2.csv" if "Filial 2" in loja else "vendas_filial5.csv"
    url = f"https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/{nome_arq}?v={int(time.time())}"
    df = pd.read_csv(url)
    df['Data_Ref'] = pd.to_datetime(df['Data'])
    df['Data_Date'] = df['Data_Ref'].dt.date
    return df

try:
    df_base = carregar_dados(unidade)
    st.title(f"🍗 {unidade} - RotiFácil")

    hoje = df_base['Data_Date'].max()
    primeiro_dia = hoje.replace(day=1)
    
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        datas = st.date_input("Filtrar Período:", value=(primeiro_dia, hoje), max_value=hoje)

    if len(datas) == 2:
        ini, fim = datas
        df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
        
        def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        total_venda = df_filt['Valor_Final'].sum()

        if "Filial 2" in unidade:
            # Venda para o Planalto via cliente 6613
            v_planalto = df_filt[df_filt['CODCLI'] == 6613]['Valor_Final'].sum()
            v_local = total_venda - v_planalto
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🛒 VENDA LOCAL", fmt(v_local))
            c2.metric("🏪 SAÍDA P/ PLANALTO", fmt(v_planalto))
            c3.metric("📊 TOTAL BRUTO", fmt(total_venda))
            c4.metric("💰 ACUMULADO MÊS", fmt(total_venda) if ini == primeiro_dia else "---")
        else:
            # Filial 5: Mostra apenas a venda direta (já filtrada no robô)
            c1, c2, c3 = st.columns(3)
            c1.metric("🛒 VENDA BRUTA (Checkout)", fmt(total_venda))
            c2.metric("💰 ACUMULADO MÊS", fmt(total_venda) if ini == primeiro_dia else "---")
            c3.metric("📅 ATUALIZAÇÃO", hoje.strftime('%d/%m'))

        st.divider()
        aba1, aba2 = st.tabs(["🗓️ Visão Diária", "🏆 Curva ABC"])
        with aba1:
            dias_pt = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}
            df_filt['Dia'] = df_filt['Data_Ref'].apply(lambda d: f"{d.strftime('%d/%m')} ({dias_pt[d.weekday()]})")
            tab = pd.pivot_table(df_filt, values='Valor_Final', index='Produto', columns='Dia', aggfunc='sum', fill_value=0)
            if not tab.empty:
                ordem = df_filt.sort_values('Data_Ref')['Dia'].unique()
                tab = tab.reindex(columns=ordem)
                tab['TOTAL'] = tab.sum(axis=1)
                tab = tab.sort_values('TOTAL', ascending=False)
                tab.loc['TOTAL DIA ➔'] = tab.sum(axis=0)
                st.dataframe(tab.map(fmt), use_container_width=True)

        with aba2:
            st.subheader("Análise de Curva ABC")
            abc = df_filt.groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
            if not abc.empty:
                abc['% Total'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()) * 100
                abc['% Acum'] = abc['% Total'].cumsum()
                abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
                st.table(abc.map(lambda x: fmt(x) if isinstance(x, float) and x > 100 else x))

except Exception as e:
    st.info("Sincronizando dados... O RotiFácil está sendo atualizado.")

    # --- ADICIONE ESTE BLOCO AO FINAL DO SEU app.py (DENTRO DO BLOCO 'if not df_base.empty') ---

# Adicionamos a terceira aba
aba1, aba2, aba3 = st.tabs(["🗓️ Visão Diária", "🏆 Curva ABC", "🔮 Projeções de Produção"])

# (O código das abas 1 e 2 você mantém exatamente como está)

with aba3:
    st.subheader("Sugestão de Produção para Amanhã")
    st.write("Esta projeção analisa o comportamento das últimas semanas para sugerir a quantidade ideal de produção.")

    # 1. Preparação dos Dados de Tendência
    df_tendencia = df_base[df_base['CODOPER'] == 'S'].copy()
    df_tendencia['Dia_Semana_Num'] = df_tendencia['Data_Ref'].dt.weekday
    
    # Mapeamento para amanhã
    dias_semana = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 
                   3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
    
    amanha_num = (datetime.now().weekday() + 1) % 7
    nome_amanha = dias_semana[amanha_num]

    st.info(f"📅 Analisando tendências para: **{nome_amanha}**")

    # 2. Cálculo da Média por Dia da Semana
    # Agrupamos por Produto e Dia da Semana para ver quanto sai em média naquele dia específico
    previsao = df_tendencia.groupby(['Produto', 'Dia_Semana_Num'])['Qtd_KG'].mean().reset_index()
    
    # Filtramos apenas a previsão para amanhã
    sugestao_amanha = previsao[previsao['Dia_Semana_Num'] == amanha_num].copy()
    
    if not sugestao_amanha.empty:
        # Adicionamos uma margem de segurança de 15% para não faltar
        sugestao_amanha['Sugestão (KG)'] = sugestao_amanha['Qtd_KG'] * 1.15
        
        # Cruzamos com a Curva ABC para priorizar o que é Classe A
        # (Assumindo que você já calculou a curva ABC no bloco anterior)
        sugestao_final = sugestao_amanha.merge(abc[['Produto', 'Curva']], on='Produto', how='left')
        
        # Organização visual
        sugestao_final = sugestao_final.sort_values(by=['Curva', 'Sugestão (KG)'], ascending=[True, False])
        
        # Tabela de Decisão
        st.dataframe(
            sugestao_final[['Curva', 'Produto', 'Sugestão (KG)']].style.format({'Sugestão (KG)': '{:.2f} kg'}),
            use_container_width=True
        )
        
        st.warning(f"💡 **Dica de Performance:** Produtos de **Classe C** com baixa saída na {nome_amanha} devem ser produzidos apenas para exposição (variedade), priorizando o volume nos itens de **Classe A**.")
    else:
        st.write("Ainda não temos dados históricos suficientes para projetar este dia da semana.")