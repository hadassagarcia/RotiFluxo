import oracledb
import pandas as pd
from github import Github
import platform
import time
import os

# --- 1. CONFIGURAÇÕES DE ACESSO ---
DB_CONFIG = {
    "user": "NUTRICAO",
    "pass": "nutr1125mmf",
    "dsn": "192.168.222.20:1521/WINT"
}

# O Token deve estar configurado nas variáveis de ambiente do seu Windows
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI") 
REPO_NAME = "hadassagarcia/RotiFluxo"
FILE_PATH = "vendas_geral.csv" # Alterado para 'geral' pois agora teremos dados amplos

# --- 2. ATIVANDO ORACLE CLIENT (WINDOWS) ---
try:
    if platform.system() == "Windows":
        # Caminho da sua pasta Instant Client
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        print("✅ Oracle Client Ativado!")
except Exception as e:
    print(f"⚠️ Aviso Client: {e}")

def sincronizar():
    try:
        print(f"\n🚀 [{time.strftime('%H:%M:%S')}] Conectando ao WinThor...")
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        
        # SQL OTIMIZADO:
        # Puxamos os dados desde o dia 01 do mês anterior para garantir que o 
        # cálculo de "Total Acumulado Mês" no site sempre tenha dados suficientes.
        query = """
            SELECT 
                P.DESCRICAO AS "Produto", 
                TRUNC(M.DTMOV) AS "Data",
                M.CODOPER,
                M.CODCLI,
                M.CODFILIAL,
                SUM(M.QT) AS "Qtd_KG", 
                SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105 
              AND M.CODFILIAL IN (2, 5) 
              AND M.DTCANCEL IS NULL
              AND M.CODOPER IN ('S', 'ST', 'SM', 'E', 'ED') 
              AND M.DTMOV >= TRUNC(SYSDATE, 'MM') - 5 -- Pega desde o dia 1 do mês atual com margem
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), M.CODOPER, M.CODCLI, M.CODFILIAL
        """
        
        df = pd.read_sql(query, con=conn)
        conn.close()
        
        if df.empty:
            print("⚠️ Sem dados novos encontrados no WinThor.")
            return

        # Salva o arquivo CSV localmente
        df.to_csv(FILE_PATH, index=False)
        print(f"✅ Extração concluída: {len(df)} linhas processadas.")

        # --- ENVIO PARA O GITHUB ---
        print("📤 Sincronizando com GitHub...")
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        with open(FILE_PATH, "r", encoding='utf-8') as f:
            content = f.read()
            
        try:
            # Tenta atualizar o arquivo se ele já existir
            contents = repo.get_contents(FILE_PATH)
            repo.update_file(contents.path, "Update Automático RotiVision", content, contents.sha)
            print("✨ Dashboard atualizado na nuvem com sucesso!")
        except Exception as e:
            # Se o arquivo não existir, ele cria um novo
            repo.create_file(FILE_PATH, "Carga Inicial RotiVision", content)
            print("🆕 Novo arquivo de dados criado no GitHub!")

    except Exception as e:
        print(f"❌ ERRO NA SINCRONIZAÇÃO: {e}")

# --- LOOP DE AUTOMAÇÃO (30 MINUTOS) ---
if __name__ == "__main__":
    print("="*40)
    print("🤖 MONITOR DE VENDAS ROTIVISION")
    print("STATUS: ATIVO E AGUARDANDO...")
    print("="*40)
    
    while True:
        sincronizar()
        proxima = time.strftime('%H:%M:%S', time.localtime(time.time() + 1800))
        print(f"💤 Ciclo finalizado. Próxima carga programada para: {proxima}")
        time.sleep(1800) # Pausa de 30 minutos