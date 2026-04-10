import oracledb
import pandas as pd
from github import Github
import os
import time

# --- CONFIGURAÇÕES ---
DB_CONFIG = {"user": "NUTRICAO", "pass": "nutr1125mmf", "dsn": "192.168.222.20:1521/WINT"}
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI")
REPO_NAME = "hadassagarcia/RotiFluxo"

def extrair_vendas(filial, nome_arquivo):
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        query = f"""
            SELECT P.DESCRICAO AS "Produto", TRUNC(M.DTMOV) AS "Data", M.CODOPER, M.CODCLI,
                   SUM(M.QT) AS "Qtd_KG", SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105 AND M.CODFILIAL = {filial} AND M.DTCANCEL IS NULL
              AND M.CODOPER IN ('S', 'ST', 'SM', 'E', 'ED') AND M.DTMOV >= TRUNC(SYSDATE, 'MM') - 5
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), M.CODOPER, M.CODCLI
        """
        df = pd.read_sql(query, con=conn)
        conn.close()
        df.to_csv(nome_arquivo, index=False)
        return True
    except Exception as e:
        print(f"❌ Erro Filial {filial}: {e}")
        return False

def subir_github(arquivos):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    for nome in arquivos:
        with open(nome, "r", encoding='utf-8') as f:
            content = f.read()
        try:
            contents = repo.get_contents(nome)
            repo.update_file(contents.path, f"Auto-sync {nome}", content, contents.sha)
        except:
            repo.create_file(nome, f"Criação {nome}", content)

if __name__ == "__main__":
    while True:
        print(f"\n🚀 [{time.strftime('%H:%M:%S')}] Iniciando...")
        if extrair_vendas(2, "vendas_filial2.csv") and extrair_vendas(5, "vendas_filial5.csv"):
            subir_github(["vendas_filial2.csv", "vendas_filial5.csv"])
            print("✅ Sucesso! Filial 2 e Filial 5 atualizadas.")
        time.sleep(1800)