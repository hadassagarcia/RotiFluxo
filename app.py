import pandas as pd
from datetime import datetime, timedelta
import time
from github import Github
import io

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="RotiFácil Performance", layout="wide", page_icon="🍗")

# ==========================================
# 🔐 SISTEMA DE LOGIN DE ACESSO
# ==========================================
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
# --- ESTILIZAÇÃO CSS PROFISSIONAL (CAIXA MESTRE) ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    .block-container { 
        background-color: white !important; border-radius: 24px !important; 
        padding: 40px 50px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.08); 
        max-width: 1200px !important; margin-top: 40px !important;
    }
    .metric-card { 
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; 
        padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); 
    }
    div[data-testid="stTabs"] button { border-radius: 12px; font-weight: 600; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 20px; }
    div[data-testid="stTabs"] button[aria-selected="true"] { background-color: #c92a2a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Se não estiver logado, mostra a tela de login e trava o resto
# 🔐 LOGIN
if 'logado' not in st.session_state: st.session_state['logado'] = False
if not st.session_state['logado']:
    st.markdown("<br><br>", unsafe_allow_html=True) 
    col1, col2, col3 = st.columns([1, 1, 1]) 
    
    _, col2, _ = st.columns([1, 1, 1])
with col2:
st.markdown("### 🍗 Acesso Restrito - RotiFácil")
        st.info("Digite suas credenciais para acessar o painel.")
        
usuario = st.text_input("👤 Usuário")
senha = st.text_input("🔑 Senha", type="password")
        
if st.button("Entrar", type="primary", use_container_width=True):
            credenciais = {
                "hadassa": "2112",
                "thiago": "0064",
                "mariana": "1288",
                "geyzzon": "0064"
            }
            
            user_formatado = usuario.strip().lower()
            
            if user_formatado in credenciais and credenciais[user_formatado] == senha:
            if usuario.strip().lower() in ["hadassa", "thiago", "mariana", "geyzzon"]:
st.session_state['logado'] = True
st.session_state['usuario_logado'] = usuario.strip().title()
st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")
                
    st.stop() 
    
# CONSTANTES DE GESTÃO
META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925  
    st.stop()

# --- TABELA DE PRECIFICAÇÃO ATUALIZADA ---
# CONSTANTES
META_FATURAMENTO = 50000.00
IMPOSTO_PERCENTUAL = 0.2925
PRECIFICACAO_REAL = {
    "ARROZ C/ CREME FRANGO KG": [16.39, 39.99],
    "ARROZ CREMOSO FRANGO KG": [16.44, 43.99],
    "ARROZ LEITE C/ CARNE SOL KG": [15.05, 47.99],
    "BAIAO DE DOIS CF KG": [16.99, 36.99],
    "CARNE C/ MACAXEIRA KG": [16.50, 29.99],
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
    "TORTA SALGADA FRANGO KG": [11.00, 39.99],
    "ALMOCO CF FRANGO KG": [9.90,29.99],
    "PANQUECA FRANGO KG": [14.23, 29.99],
    "PANQUECA CARNE MOIDA KG": [12.16, 29.99],
    "ARROZ C/ CREME FRANGO KG": [16.39, 39.99], "ARROZ CREMOSO FRANGO KG": [16.44, 43.99],
    "ARROZ LEITE C/ CARNE SOL KG": [15.05, 47.99], "BAIAO DE DOIS CF KG": [16.99, 36.99],
    "CARNE C/ MACAXEIRA KG": [16.50, 29.99], "CUSCUZ C/ CARNE KG": [14.90, 32.99],
    "PANQUECA FRANGO KG": [14.23, 29.99], "PANQUECA CARNE MOIDA KG": [12.16, 29.99]
}

# --- ESTILIZAÇÃO CSS PROFISSIONAL ---
st.markdown("""
    <style>
    /* O "Reset" da página - Tirando o colado da borda */
    .stApp { background-color: #f0f2f6; }
    
    /* A Caixa Mestre: Agora com margens perfeitas e arredondamento */
    .block-container {
        background-color: white;
        border-radius: 24px !important;
        padding: 40px 60px !important;
        margin: 40px auto !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        max-width: 95% !important;
    }

    /* Estilo Profissional para os Cards de Métricas */
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    
    /* Abas com cara de Botões de Navegação */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 10px; }
    div[data-testid="stTabs"] button {
        border-radius: 12px !important;
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: #c92a2a !important;
        color: white !important;
    }
    
    /* Títulos mais elegantes */
    h1, h2, h3 { color: #1e293b !important; font-family: 'Inter', sans-serif !important; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DADOS ---
@st.cache_data(ttl=60)
def carregar(arq):
try:
@@ -129,288 +59,73 @@ def carregar(arq):
df['Data_Ref'] = pd.to_datetime(df['Data'])
df['Data_Date'] = df['Data_Ref'].dt.date
return df
    except Exception as e:
        st.error(f"🚨 Não consegui ler a planilha {arq}. Erro: {e}")
        return pd.DataFrame()

# ==========================================
# CABEÇALHO: LOGO (ESQUERDA) | FILTROS (DIREITA)
# ==========================================
col_logo, col_vazia, col_filial, col_data = st.columns([2, 0.5, 1.5, 2])
    except: return pd.DataFrame()

# CABEÇALHO
col_logo, _, col_filial, col_data = st.columns([2, 0.5, 1.5, 2])
with col_logo:
    try:
        st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=250)
    except:
        st.markdown("### 🍗 RotiFácil")
        
    st.caption(f"👤 Operador(a): **{st.session_state.get('usuario_logado', '')}**")
    if st.button("Sair (Logout)"):
        st.session_state['logado'] = False
        st.rerun()

df_temp = carregar("vendas_filial2.csv")
hoje_dados = df_temp['Data_Date'].max() if not df_temp.empty else datetime.today().date()

with col_filial:
    st.write("")
    unidade = st.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])

with col_data:
    st.write("")
    datas_sel = st.date_input("📅 Selecione o Período:", value=(hoje_dados.replace(day=1), hoje_dados), max_value=hoje_dados)
    st.image("https://raw.githubusercontent.com/hadassagarcia/RotiFluxo/main/logo.png", width=200)
    if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

unidade = col_filial.selectbox("📍 Unidade:", ["Filial 2 (Parnamirim)", "Filial 5 (Planalto)"])
datas_sel = col_data.date_input("📅 Período:", value=(datetime.today().date().replace(day=1), datetime.today().date()))
st.divider()

if "Filial 2" in unidade:
    arquivo_vendas = "vendas_filial2.csv"
    arquivo_avarias = "avarias_filial2.csv"
else:
    arquivo_vendas = "vendas_filial5.csv"
    arquivo_avarias = "avarias_filial5.csv"

# CARGA
arquivo_vendas = "vendas_filial2.csv" if "Filial 2" in unidade else "vendas_filial5.csv"
arquivo_avarias = "avarias_filial2.csv" if "Filial 2" in unidade else "avarias_filial5.csv"
df_base = carregar(arquivo_vendas)

# 🚀 LÊ AVARIAS DIRETO DA API DO GITHUB (Fura o Cache)
try:
    from github import Github
    import io
    g = Github(st.secrets["token_github"])
    repo = g.get_repo("hadassagarcia/RotiFluxo")
    file_contents = repo.get_contents(arquivo_avarias)
    df_avarias = pd.read_csv(io.StringIO(file_contents.decoded_content.decode('utf-8')))
except Exception as e:
    st.error(f"Erro ao ler avarias ao vivo: {e}")
    df_avarias = pd.DataFrame()
    repo = Github(st.secrets["token_github"]).get_repo("hadassagarcia/RotiFluxo")
    df_avarias = pd.read_csv(io.StringIO(repo.get_contents(arquivo_avarias).decoded_content.decode('utf-8')))
except: df_avarias = pd.DataFrame()

# --- INÍCIO DO CÓDIGO CORRIGIDO ---
# LÓGICA E DASHBOARD
if not df_base.empty and len(datas_sel) == 2:
ini, fim = datas_sel
df_filt = df_base[(df_base['Data_Date'] >= ini) & (df_base['Data_Date'] <= fim)].copy()

    # --- CÁLCULO FINANCEIRO vs MÊS PASSADO ---
    # Cálculos Comparativos
    fat_atual = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
ini_ant = (pd.to_datetime(ini) - pd.DateOffset(months=1)).date()
fim_ant = (pd.to_datetime(fim) - pd.DateOffset(months=1)).date()
    fat_ant = df_base[(df_base['Data_Date'] >= ini_ant) & (df_base['Data_Date'] <= fim_ant) & (df_base['CODOPER'] == 'S')]['Valor_Final'].sum()
    dif = fat_atual - fat_ant

    df_filt_ant = df_base[(df_base['Data_Date'] >= ini_ant) & (df_base['Data_Date'] <= fim_ant)].copy()
    
    fat_periodo = df_filt[df_filt['CODOPER'] == 'S']['Valor_Final'].sum()
    fat_periodo_ant = df_filt_ant[df_filt_ant['CODOPER'] == 'S']['Valor_Final'].sum()
    
    # Diferença exata em Reais (R$)
    diferenca_rs = fat_periodo - fat_periodo_ant
    sinal = "+" if diferenca_rs > 0 else ""
    texto_diferenca = f"{sinal} R$ {diferenca_rs:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    progresso = min(fat_periodo / META_FATURAMENTO, 1.0)
    
    st.subheader(f"🎯 Performance no Período (Meta: R$ {META_FATURAMENTO:,.2f})")
    st.progress(progresso)
    
    st.write("<br>", unsafe_allow_html=True)
    
    # --- NOVOS CARTÕES (METRICS) COM IDENTIDADE VISUAL ---
    col_m1, col_m2, col_m3 = st.columns(3)
    
    col_m1.metric(
        label="💰 Faturamento Atual", 
        value=f"R$ {fat_periodo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
        delta=f"{texto_diferenca} vs mês anterior",
        delta_color="normal"
    )
    
    col_m2.metric(
        label="📅 Referência Anterior", 
        value=f"R$ {fat_periodo_ant:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), 
        delta=f"Mesmos dias ({ini_ant.strftime('%d/%m')} a {fim_ant.strftime('%d/%m')})",
        delta_color="off"
    )
    
    falta_rs = max(0, META_FATURAMENTO - fat_periodo)
    col_m3.metric(
        label="🚀 Atingimento da Meta", 
        value=f"{progresso*100:.1f}%", 
        delta=f"Falta R$ {falta_rs:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if progresso < 1 else "Meta Batida!",
        delta_color="normal" if progresso < 1 else "off"
    )

    st.write("<br>", unsafe_allow_html=True)

    aba_perf, aba_vendas, aba_pico, aba_abc, aba_ruptura, aba_avaria = st.tabs([
        "📈 Margem Real", "📊 Visão Diária", "🔥 Mapa de Calor", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"
    ])
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>Faturamento</h3><p style="font-size:24px; font-weight:800">R$ {fat_atual:,.2f}</p>{"🔺" if dif >= 0 else "🔻"} R$ {abs(dif):,.2f} vs mês anterior</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>Comparação</h3><p style="font-size:24px; font-weight:800">{ini_ant.strftime("%d/%m")} a {fim_ant.strftime("%d/%m")}</p>Período anterior</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>Meta</h3><p style="font-size:24px; font-weight:800">{min(fat_atual/META_FATURAMENTO, 1.0)*100:.1f}%</p>Falta R$ {max(0, META_FATURAMENTO - fat_atual):,.2f}</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📈 Margem", "📊 Vendas", "🔥 Picos", "🏆 ABC", "🚨 Ruptura", "🗑️ Avaria"])
def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    with aba_perf:
    with tabs[0]:
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
            }).map(lambda x: 'color: #c92a2a; font-weight: bold' if isinstance(x, float) and x < 10 else None, subset=['Margem_Real']), 
            use_container_width=True)
        v_prod['Lucro_R$'] = (v_prod['Qtd_KG'] * v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[1])) - (v_prod['Qtd_KG'] * v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[0])) - (v_prod['Qtd_KG'] * v_prod['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[1]) * IMPOSTO_PERCENTUAL)
        st.dataframe(v_prod[['Produto', 'Valor_Final', 'Lucro_R$']], use_container_width=True)

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
    with tabs[1]:
        tab = pd.pivot_table(df_filt, values='Valor_Final', index='Produto', columns=df_filt['Data_Ref'].dt.strftime('%d/%m'), aggfunc='sum', fill_value=0)
        st.dataframe(tab.map(fmt), use_container_width=True)

    with aba_pico:
        st.subheader("🔥 Mapa de Calor")
        st.write("Descubra os horários de maior fluxo em cada dia da semana.")
        if 'Hora' in df_filt.columns:
            df_pico = df_filt[df_filt['CODOPER'] == 'S'].copy()
            if not df_pico.empty:
                dias_semana_num = {0:'0-Seg', 1:'1-Ter', 2:'2-Qua', 3:'3-Qui', 4:'4-Sex', 5:'5-Sáb', 6:'6-Dom'}
                df_pico['Dia_Semana'] = df_pico['Data_Ref'].dt.weekday.map(dias_semana_num)
                mapa_pico = pd.pivot_table(df_pico, values='Valor_Final', index='Dia_Semana', columns='Hora', aggfunc='sum', fill_value=0)
                if not mapa_pico.empty:
                    mapa_pico.index = mapa_pico.index.str[2:]
                    dia_sel = st.selectbox("📊 Veja a curva de fluxo de um dia específico:", mapa_pico.index)
                    st.bar_chart(mapa_pico.loc[dia_sel], color="#c92a2a")
                    st.divider()
                    st.dataframe(mapa_pico.style.background_gradient(cmap='Reds', axis=None).format(fmt), use_container_width=True)
        else:
            st.warning("⚠️ Os dados de horário ainda não foram sincronizados.")
    with tabs[2]:
        df_pico = df_filt[df_filt['CODOPER'] == 'S'].copy()
        if 'Hora' in df_pico.columns:
            st.bar_chart(df_pico.groupby('Hora')['Valor_Final'].sum(), color="#c92a2a")

    with aba_abc:
        abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().reset_index().sort_values('Valor_Final', ascending=False)
        if not abc.empty:
            abc['% Acum'] = (abc['Valor_Final'] / abc['Valor_Final'].sum()).cumsum() * 100
            abc['Curva'] = abc['% Acum'].apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            st.table(abc[['Curva', 'Produto', 'Valor_Final']].map(lambda x: fmt(x) if isinstance(x, float) else x))
    with tabs[3]:
        abc = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Valor_Final'].sum().sort_values(ascending=False).reset_index()
        st.table(abc)

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
                    st.line_chart(fluxo_hora.set_index('Hora')['Valor_Final'], color="#f5a623")
                    ult_h = int(fluxo_hora['Hora'].max())
                    if ult_h < 13: st.error(f"Ruptura! Parou de vender às {ult_h}h.")
                    else: st.success(f"Fluxo normal até às {ult_h}h.")
    with tabs[4]:
        st.write("Análise de Ruptura ativa...")

    with aba_avaria:
        st.subheader("🗑️ Controle e Radar de Avarias")
        
        with st.expander("➕ Lançar Nova Avaria", expanded=False):
            data_avaria = st.date_input("Selecione a Data da Avaria:", value=datetime.today().date())
            lista_produtos = list(PRECIFICACAO_REAL.keys())
            df_lancamento = pd.DataFrame({"Produto": lista_produtos, "Qtd_KG": [0.0] * len(lista_produtos)})
            df_editado = st.data_editor(df_lancamento, hide_index=True, use_container_width=True)
            
            if st.button("💾 Gravar Avaria do Dia", type="primary"):
                avarias_reais = df_editado[df_editado['Qtd_KG'] > 0].copy()
                if not avarias_reais.empty:
                    avarias_reais['Data'] = data_avaria.strftime("%Y-%m-%d")
                    try:
                        from github import Github
                        token = st.secrets["token_github"]
                        g = Github(token)
                        repo = g.get_repo("hadassagarcia/RotiFluxo")
                        file_contents = repo.get_contents(arquivo_avarias)
                        df_vivo = pd.read_csv(io.StringIO(file_contents.decoded_content.decode('utf-8')))
                        df_novas_avarias = pd.concat([df_vivo, avarias_reais], ignore_index=True)
                        novo_csv = df_novas_avarias.to_csv(index=False)
                        repo.update_file(file_contents.path, f"Avaria registrada em {data_avaria}", novo_csv, file_contents.sha)
                        st.success("✅ Sucesso! Avaria gravada definitivamente.")
                        time.sleep(2)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar no GitHub: {e}")
                else:
                    st.warning("⚠️ Preencha a tabela antes de gravar.")
        
        st.divider()
        st.write("### 📊 Análise Estratégica de Perdas no Período")
        
    with tabs[5]:
        st.subheader("Controle de Avarias")
if not df_avarias.empty:
df_avarias['Data'] = pd.to_datetime(df_avarias['Data']).dt.date
            df_avarias_periodo = df_avarias[(df_avarias['Data'] >= ini) & (df_avarias['Data'] <= fim)].copy()
            
            if not df_avarias_periodo.empty:
                df_avarias_periodo['Custo_Unit'] = df_avarias_periodo['Produto'].apply(lambda x: PRECIFICACAO_REAL.get(x, [0, 0])[0])
                df_avarias_periodo['Custo_Total_R$'] = df_avarias_periodo['Qtd_KG'] * df_avarias_periodo['Custo_Unit']
                
                total_kg_perdido = df_avarias_periodo['Qtd_KG'].sum()
                total_rs_perdido = df_avarias_periodo['Custo_Total_R$'].sum()
                perc_avaria = (total_rs_perdido / fat_periodo * 100) if fat_periodo > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("🗑️ Total Físico Perdido", f"{total_kg_perdido:.2f} KG")
                col2.metric("💸 Dinheiro no Lixo (Custo)", fmt(total_rs_perdido))
                col3.metric("📉 % Avaria sobre Venda", f"{perc_avaria:.2f}%")
                
                st.write("")
                st.write("#### 🚨 Curva ABC de Desperdício e Proporção")
                
                df_abc_avaria = df_avarias_periodo.groupby('Produto').agg({'Qtd_KG': 'sum', 'Custo_Total_R$': 'sum'}).reset_index()
                df_abc_avaria.rename(columns={'Qtd_KG': 'Qtd_KG_Avaria'}, inplace=True)
                
                df_vendas_kg = df_filt[df_filt['CODOPER'] == 'S'].groupby('Produto')['Qtd_KG'].sum().reset_index()
                df_vendas_kg.rename(columns={'Qtd_KG': 'Qtd_KG_Vendido'}, inplace=True)
                
                df_abc_avaria = pd.merge(df_abc_avaria, df_vendas_kg, on='Produto', how='left')
                df_abc_avaria['Qtd_KG_Vendido'] = df_abc_avaria['Qtd_KG_Vendido'].fillna(0)
                df_abc_avaria = df_abc_avaria.sort_values(by='Custo_Total_R$', ascending=False)
                df_abc_avaria['% Acumulado'] = (df_abc_avaria['Custo_Total_R$'].cumsum() / df_abc_avaria['Custo_Total_R$'].sum()) * 100
                
                def classificar_abc(perc):
                    if perc <= 80: return 'A (Crítico)'
                    elif perc <= 95: return 'B (Atenção)'
                    else: return 'C (Normal)'
                    
                df_abc_avaria['Curva ABC'] = df_abc_avaria['% Acumulado'].apply(classificar_abc)
                df_abc_avaria = df_abc_avaria[['Curva ABC', 'Produto', 'Qtd_KG_Avaria', 'Qtd_KG_Vendido', 'Custo_Total_R$', '% Acumulado']]
                
                st.dataframe(
                    df_abc_avaria.style.apply(lambda r: ['background-color: #ffe8e8; color: #c92a2a'] * len(r) if 'A' in r['Curva ABC'] else [''] * len(r), axis=1).format({
                        'Qtd_KG_Avaria': '{:.2f} KG', 'Qtd_KG_Vendido': '{:.2f} KG', 'Custo_Total_R$': fmt, '% Acumulado': '{:.1f}%'
                    }),
                    use_container_width=True, hide_index=True
                )
                
                st.write("#### 📅 Ritmo Semanal de Lançamento de Avarias")
                df_avarias_periodo['Dia_Semana'] = pd.to_datetime(df_avarias_periodo['Data']).dt.weekday
                mapa_dias = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
                df_dias = df_avarias_periodo.groupby('Dia_Semana')['Custo_Total_R$'].sum().reset_index()
                df_dias['Dia'] = df_dias['Dia_Semana'].map(mapa_dias)
                df_dias = df_dias.sort_values('Dia_Semana').set_index('Dia')
                
                if not df_dias.empty:
                    st.bar_chart(df_dias[['Custo_Total_R$']], color="#c92a2a")
                
                st.divider()
                with st.expander("Ver Histórico de Lançamentos Diários", expanded=False):
                    st.dataframe(df_avarias_periodo[['Data', 'Produto', 'Qtd_KG']], use_container_width=True, hide_index=True)
            else:
                st.success("🎉 Excelente! Nenhuma avaria registrada neste período.")
        else:
            st.info("Nenhuma avaria registrada no sistema ainda.")
            df_avarias_per = df_avarias[(df_avarias['Data'] >= ini) & (df_avarias['Data'] <= fim)]
            st.dataframe(df_avarias_per, use_container_width=True)
else:
    st.info("Sincronizando dados ou selecione um período de datas inicial e final para carregar o Dashboard.")
    st.info("Selecione um período.")
