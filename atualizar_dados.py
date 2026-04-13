import oracledb
import pandas as pd
from github import Github
import os, time, platform

# --- CONFIGURAÇÕES ---
DB_CONFIG = {"user": "NUTRICAO", "pass": "nutr1125mmf", "dsn": "192.168.222.20:1521/WINT"}
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI")
REPO_NAME = "hadassagarcia/RotiFluxo"

def extrair(filial, arquivo):
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        # SQL PARA BATER COM A 322 (Venda Bruta)
        query = f"""
            SELECT P.DESCRICAO AS "Produto", TRUNC(M.DTMOV) AS "Data", M.CODOPER, M.CODCLI,
                   SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105 AND M.CODFILIAL = {filial} AND M.DTCANCEL IS NULL
              AND M.CODOPER = 'S' 
              AND M.DTMOV >= TRUNC(SYSDATE, 'MM')
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), M.CODOPER, M.CODCLI
        """
        df = pd.read_sql(query, con=conn)
        conn.close()
        if not df.empty:
            df.to_csv(arquivo, index=False)
            return True
        return False
    except Exception as e:
        print(f"❌ Erro F{filial}: {e}")
        return False

def subir_github(arquivos):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    for nome in arquivos:
        with open(nome, "r", encoding='utf-8') as f:
            content = f.read()
        try:
            c = repo.get_contents(nome)
            repo.update_file(c.path, "RotiFácil Sync", content, c.sha)
        except:
            repo.create_file(nome, "RotiFácil Init", content)

if __name__ == "__main__":
    print("🚀 SISTEMA ROTIFÁCIL - SINCRONIZADOR")
    while True:
        # Extrai os dois arquivos
        if extrair(2, "vendas_filial2.csv") and extrair(5, "vendas_filial5.csv"):
            subir_github(["vendas_filial2.csv", "vendas_filial5.csv"])
            print(f"✅ Sincronizado às {time.strftime('%H:%M:%S')}")
        time.sleep(1800)