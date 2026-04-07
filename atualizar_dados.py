import oracledb
import pandas as pd
from github import Github
import platform

# --- 1. CONFIGURAÇÕES (SÓ NO SEU PC) ---
DB_CONFIG = {
    "user": "NUTRICAO",
    "pass": "nutr1125mmf", # Senha que vimos no seu print
    "dsn": "192.168.222.20:1521/WINT" # IP que funcionou no seu print
}

import os
# Ele vai procurar uma variável no seu Windows chamada GITHUB_TOKEN
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI") 
REPO_NAME = "hadassagarcia/RotiFluxo"
FILE_PATH = "vendas_filial2.csv"

# --- 2. ATIVANDO MODO DE COMPATIBILIDADE ---
try:
    if platform.system() == "Windows":
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        print("✅ Oracle Client Ativado!")
except Exception as e:
    print(f"⚠️ Aviso Client: {e}")

def sincronizar():
    try:
        print("🔗 Conectando ao WinThor local...")
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        
        # SQL Atualizado com CODCLI para identificar a Filial 5
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
            print("⚠️ Sem dados no período.")
            return

        # Salva o CSV local
        df.to_csv(FILE_PATH, index=False)
        print(f"✅ Extração: {len(df)} linhas.")

        # --- 3. ENVIANDO PARA O GITHUB ---
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        with open(FILE_PATH, "r", encoding='utf-8') as f:
            content = f.read()
            
        try:
            contents = repo.get_contents(FILE_PATH)
            repo.update_file(contents.path, "Sync Filial 5 Update", content, contents.sha)
            print("🚀 Dashboard atualizado no GitHub!")
        except:
            repo.create_file(FILE_PATH, "Carga inicial", content)
            print("🆕 Arquivo criado!")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    sincronizar()