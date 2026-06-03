import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925  # 29,25% sobre o Preço de Venda

# --- TABELA DE PRECIFICAÇÃO ATUALIZADA ---
PRECIFICACAO_REAL = {
    "ARROZ C/ CREME FRANGO KG": [16.39, 39.99],
    "ARROZ CREMOSO FRANGO KG": [16.44, 43.99],
    "ARROZ LEITE C/ CARNE SOL KG": [15.05, 47.99],
    "BAIAO DE DOIS CF KG": [16.99, 36.99],
    "CARNE C/ MACAXEIRA KG": [16.50, 29.99], # Assumindo 16.50 como base
    "CUSCUZ C/ CARNE KG": [14.90, 32.99],
    "CUSCUZ C/ CARNE MOIDA KG": [10.23, 29.99],
    "CUSCUZ C/ SALSICHA KG": [7.90, 24.99],
    "EMPADAO CARNE SOL KG": [21.82, 55.99],
    "EMPADAO FRANGO KG": [16.69, 52.99],
    "ESCONDIDINHO CARNE MOIDA KG": [17.18, 44.99],
    "FRANGO ASSADO CORTE FACIL KG": [23.92, 34.99],
    "LASANHA CARNE MOIDA KG": [21.24, 45.99],
    "LASANHA FRANGO KG": [25.41, 45.99],
    "MACAXEIRA C/ CALABRESA ACEB KG": [9.89, 37.99],
    "PATE FRANGO KG": [21.85, 44.99],
    "SOPA CARNE KG": [8.71, 32.99],
    "TAPIOCA CARNE SOL KG": [21.05, 47.99],
    "TAPIOCA FRANGO KG": [15.30, 43.99],
    "TAPIOCA MISTA KG": [14.32, 47.99],
    "TAPIOCA QUEIJO KG": [19.54, 47.99],
}

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    /* Esconder a barra lateral antiga */
    [data-testid="stSidebar"] { display: none; }
    
    /* Centralizar as abas e configurar a aba selecionada em tom de cinza */
    div[data-baseweb="tab-list"] {
        justify-content: center;
        gap: 8px;
    }
    button[data-baseweb="tab"] { 
        background-color: transparent !important; 
        border-radius: 8px !important; 
        border: 1px solid #e2e8f0 !important;
    }
    button[aria-selected="true"] { 
        background-color: #e2e8f0 !important; /* Tom de cinza suave */
        color: #1e293b !important; /* Texto escuro para dar contraste */
        border: 1px solid #cbd5e1 !important;
    }
    button[data-baseweb="tab"] p { font-size: 16px !important; font-weight: 600 !important; }
    
    /* Fonte e fundo padrão */
    label[data-testid="stWidgetLabel"] p { font-size: 16px !important; font-weight: bold !important; }
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

# ==========================================
# CABEÇALHO: LOGO (ESQUERDA) | FILTROS (DIREITA)
# ==========================================
col_logo, col_vazia, col_filial, col_data = st.columns([2, 0.5, 1.5, 2])

with col_logo:
    try:
        # Puxa a logo nova direto do seu GitHub
        st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=250)
    except:
        st.markdown("### 🍗 RotiFácil")

# Pegar uma data base para o calendário carregar corretamente
df_temp = carregar("vendas_filial2.csv")
hoje_dados = df_temp['Data_Date'].max() if not df_temp.empty else datetime.today().date()

with col_filial:
    st.write("") # Espaço pequeno para alinhar com a logo
    unidade = st.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

with col_data:
    st.write("") # Espaço pequeno para alinhar com a logo
    datas_sel = st.date_input("📅 Selecione o Período:", value=(hoje_dados.replace(day=1), hoje_dados), max_value=hoje_dados)

st.divider() # Linha separadora elegante

# Carrega os dados reais baseados na filial escolhida
df_base = carregar("vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv")
df_avarias = carregar("avarias.csv")

if not df_base.empty and len(datas_sel) == 2:
    ini, fim = datas_sel
    df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()
    
    # --- STATUS DA META DINÂMICO (NO PADRÃO ANTIGO) ---
    fat_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
    progresso = min(fat_periodo / META_FATURAMENTO, 1.0)
    
    st.subheader(f"🎯 Performance no Período (Meta: R$ {META_FATURAMENTO:,.2f})")
    st.progress(progresso)
    st.write(f"Total Vendido: **R$ {fat_periodo:,.2f}** ({progresso*100:.1f}%)")

    st.write("<br>", unsafe_allow_html=True) # Quebra de linha para dar um respiro antes das abas

    aba_perf, aba_vendas, aba_pico, aba_abc, aba_ruptura, aba_avaria = st.tabs([
        "📈 Margem Real", "📊 Visão Diária", "🔥 Mapa de Calor", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"
    ])

    def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # --- ABA PERFORMANCE & MARGEM REAL ---
    with aba_perf:
        v_prod = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto').agg({'Valor_Final': 'sum', 'Qtd_KG': 'sum'}).reset_index()
        if not v_prod.empty:
            v_prod['Custo_Base_Unit'] = v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[0])
            v_prod['Preco_Venda_Unit'] = v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[1])
            v_prod['Faturamento_Gerencial'] = v_prod['Qtd_KG'] * v_prod['Preco_Venda_Unit']
            v_prod['Imposto_Total'] = v_prod['Faturamento_Gerencial'] * IMPOSTO_PERCENTUAL
            v_prod['Custo_Total_Materia_Prima'] = v_prod['Qtd_KG'] * v_prod['Custo_Base_Unit']
            v_prod['Lucro_R$'] = v_prod['Faturamento_Gerencial'] - v_prod['Imposto_Total'] - v_prod['Custo_Total_Materia_Prima']
            v_prod['Margem_Real'] = v_prod.apply(lambda r: (r['Lucro_R$'] / r['Faturamento_Gerencial'] * 100) if r['Faturamento_Gerencial'] > 0 else 0, axis=1)
            
            df_mostrar = v_prod.sort_values('Lucro_R$', ascending=False)[['Produto', 'Faturamento_Gerencial', 'Lucro_R$', 'Margem_Real']]
            st.dataframe(df_mostrar.style.format({
                'Faturamento_Gerencial': fmt, 
                'Lucro_R$': fmt, 
                'Margem_Real': '{:.2f}%'
            }).map(lambda x: 'color: red; font-weight: bold' if isinstance(x, float) and x < 10 else None, subset=['Margem_Real']), 
            use_container_width=True)

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

    # --- ABA HORÁRIOS DE PICO ---
    with aba_pico:
        st.subheader("🔥 Mapa de Calor")
        st.write("Descubra os horários de maior fluxo em cada dia da semana para alinhar a produção da mesa.")
        
        if 'Hora' in df_filt.columns:
            df_pico = df_filt[df_filt['CODOPER'] == 'S'].copy()
            
            if not df_pico.empty:
                dias_semana_num = {0:'0-Seg', 1:'1-Ter', 2:'2-Qua', 3:'3-Qui', 4:'4-Sex', 5:'5-Sáb', 6:'6-Dom'}
                df_pico['Dia_Semana'] = df_pico['Data_Ref'].dt.weekday.map(dias_semana_num)
                
                mapa_pico = pd.pivot_table(df_pico, values='Valor_Final', index='Dia_Semana', columns='Hora', aggfunc='sum', fill_value=0)
                
                if not mapa_pico.empty:
                    mapa_pico.index = mapa_pico.index.str[2:]
                    
                    dia_sel = st.selectbox("📊 Veja a curva de fluxo de um dia específico:", mapa_pico.index)
                    st.bar_chart(mapa_pico.loc[dia_sel], color="#1E3A8A")
                    
                    st.divider()
                    st.write("### 🌡️ Matriz Semanal de Faturamento por Hora")
                    st.caption("Quanto mais forte o tom de vermelho, maior o faturamento. Use isso para saber que horas a comida precisa estar pronta!")
                    
                    st.dataframe(mapa_pico.style.background_gradient(cmap='Reds', axis=None).format(fmt), use_container_width=True)
        else:
            st.warning("⚠️ Os dados de horário ainda não foram sincronizados pelo robô.")

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
                lista_a = vendas_abc[vendas_abc['% Acum'] <= 80]['Produto'].tolist()
                prod_analise = st.selectbox("Auditar Fluxo Horário (Dia Final):", lista_a if lista_a else vendas_abc['Produto'].head(5).tolist())
                df_hora = df_filt[(df_filt['Produto'] == prod_analise) & (df_filt['Data_Date'] == fim)].copy()
                if not df_hora.empty:
                    fluxo_hora = df_hora.groupby('Hora')['Valor_Final'].sum().reset_index().sort_values('Hora')
                    st.line_chart(fluxo_hora.set_index('Hora')['Valor_Final'])
                    ult_h = int(fluxo_hora['Hora'].max())
                    if ult_h < 13: st.error(f"Ruptura! Parou de vender às {ult_h}h.")
                    else: st.success(f"Fluxo normal até às {ult_h}h.")

    # --- ABA AVARIA ---
        with aba_avaria:
            st.subheader("🗑️ Controle e Radar de Avarias")
            
            # --- DETETIVE ---
            try:
                st.warning(f"🔎 O Streamlit está lendo estas chaves no cofre: {list(st.secrets.keys())}")
            except Exception as e:
                st.error("O cofre está totalmente vazio ou inacessível.")
            # ----------------
            
            # 1. ÁREA DE LANÇAMENTO
            with st.expander("➕ Lançar Nova Avaria", expanded=False):
                data_avaria = st.date_input("Selecione a Data da Avaria:", value=datetime.today().date())
                
                lista_produtos = list(PRECIFICACAO_REAL.keys())
                df_lancamento = pd.DataFrame({
                    "Produto": lista_produtos,
                    "Qtd_KG": [0.0] * len(lista_produtos)
                })
                
                st.write("Digite a quantidade perdida (em KG) na coluna abaixo:")
                df_editado = st.data_editor(df_lancamento, hide_index=True, use_container_width=True)
                
                if st.button("💾 Gravar Avaria do Dia", type="primary"):
                    avarias_reais = df_editado[df_editado['Qtd_KG'] > 0].copy()
                    
                    if not avarias_reais.empty:
                        avarias_reais['Data'] = data_avaria.strftime("%Y-%m-%d")
                        
                        try:
                            # Traz a ferramenta do GitHub e a senha do cofre do Streamlit
                            from github import Github
                            token = st.secrets["token_github"]
                            g = Github(token)
                            repo = g.get_repo("hadassagarcia/RotiFluxo")
                            
                            # Puxa o arquivo atual
                            file_contents = repo.get_contents("avarias.csv")
                            
                            # Junta o histórico antigo com o lançamento de agora
                            df_novas_avarias = pd.concat([df_avarias, avarias_reais], ignore_index=True)
                            novo_csv = df_novas_avarias.to_csv(index=False)
                            
                            # Salva a atualização no GitHub
                            repo.update_file(file_contents.path, f"Avaria registrada em {data_avaria}", novo_csv, file_contents.sha)
                            
                            st.success(f"✅ Sucesso! Avaria de {len(avarias_reais)} produto(s) gravada definitivamente no sistema.")
                            time.sleep(2) # Pausa rápida para você ler a mensagem
                            st.cache_data.clear()
                            st.rerun() # Recarrega a tela para atualizar a tabela de baixo
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar no GitHub. Verifique se o token foi configurado certinho nos Secrets. Erro: {e}")
                    else:
                        st.warning("⚠️ Você não informou nenhuma quantidade. Preencha a tabela antes de gravar.")
            
            st.divider()
            
            # 2. ÁREA DE VISUALIZAÇÃO DO HISTÓRICO
            st.write("### 📋 Histórico de Avarias")
            if not df_avarias.empty:
                st.dataframe(df_avarias, use_container_width=True)
            else: 
                st.info("Nenhuma avaria registrada no sistema ainda.")

else: st.info("Sincronizando dados...")
