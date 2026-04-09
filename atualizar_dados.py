import oracledb
import pandas as pd
from github import Github
import platform
import time
import os

# --- 1. CONFIGURAÇÕES DO BANCO ---
DB_CONFIG = {
    "user": "NUTRICAO",
    "pass": "nutr1125mmf",
    "dsn": "192.168.222.20:1521/WINT"
}

# --- 2. CONFIGURAÇÕES DO GITHUB ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI") 
REPO_NAME = "hadassagarcia/RotiFluxo"
FILE_PATH = "vendas_filial2.csv"

# --- 3. ATIVANDO ORACLE CLIENT (WINDOWS) ---
try:
    if platform.system() == "Windows":
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        print("✅ Oracle Client Ativado!")
except Exception as e:
    print(f"⚠️ Aviso Client: {e}")

def sincronizar():
    try:
        print(f"\n🚀 [{time.strftime('%H:%M:%S')}] Conectando ao WinThor...")
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        
        # SQL que traz os dados dos últimos 60 dias (ajustado para suas colunas)
        query = """
            SELECT 
                P.DESCRICAO AS "Produto", 
                TRUNC(M.DTMOV) AS "Data",
                M.CODOPER,
                M.CODCLI,
                SUM(M.QT) AS "Qtd_KG", 
                SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105 
              AND M.CODFILIAL = 2 
              AND M.DTCANCEL IS NULL
              AND M.CODOPER IN ('S', 'ST', 'SM', 'E', 'ED') 
              AND M.DTMOV >= SYSDATE - 60
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), M.CODOPER, M.CODCLI
        """
        
        df = pd.read_sql(query, con=conn)
        conn.close()
        
        if df.empty:
            print("⚠️ Sem dados novos no período.")
            return

        # Salva o CSV local
        df.to_csv(FILE_PATH, index=False)
        print(f"✅ Extração: {len(df)} linhas extraídas.")

        # --- ENVIO PARA O GITHUB ---
        print("📤 Enviando para o GitHub...")
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        with open(FILE_PATH, "r", encoding='utf-8') as f:
            content = f.read()
            
        try:
            contents = repo.get_contents(FILE_PATH)
            repo.update_file(contents.path, "Auto-sync 30min", content, contents.sha)
            print("🚀 Dashboard atualizado na nuvem!")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar no GitHub: {e}")

    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")

# --- LOOP DE 30 MINUTOS ---
if __name__ == "__main__":
    print("🤖 MONITOR ROTIFLUXO ATIVADO")
    print("Mantenha esta janela aberta para atualizar a cada 30 minutos.")
    
    while True:
        sincronizar()
        proxima_carga = time.strftime('%H:%M:%S', time.localtime(time.time() + 1800))
        print(f"💤 Aguardando... Próxima carga às: {proxima_carga}")
        time.sleep(1800) # 1800 segundos = 30 minutos