import oracledb
import pandas as pd
from github import Github
import os, time, platform

# --- CONFIGURAÇÕES ---
DB_CONFIG = {"user": "NUTRICAO", "pass": "nutr1125mmf", "dsn": "192.168.222.20:1521/WINT"}
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI")
REPO_NAME = "hadassagarcia/RotiFluxo"

# --- ATIVANDO ORACLE CLIENT ---
try:
    if platform.system() == "Windows":
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        print("✅ Oracle Client Ativado!")
except Exception as e:
    print(f"⚠️ Erro Oracle Client: {e}")

def extrair(filial, arquivo):
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        
        # SQL que busca tudo desde o início do ano
        query = f"""
            SELECT 
                P.DESCRICAO AS "Produto", 
                TRUNC(M.DTMOV) AS "Data", 
                TO_CHAR(C.DTSAIDA, 'HH24') AS "Hora",
                M.CODOPER, 
                SUM(M.QT) AS "Qtd_KG", 
                SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            JOIN MMFRIOS.PCNFSAID C ON M.NUMTRANSVENDA = C.NUMTRANSVENDA
            WHERE P.CODEPTO = 105 
              AND M.CODFILIAL = {filial} 
              AND M.DTCANCEL IS NULL
              AND M.CODOPER = 'S'
              AND M.DTMOV >= TO_DATE('01/01/2026', 'DD/MM/YYYY') -- Começo do ano
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), TO_CHAR(C.DTSAIDA, 'HH24'), M.CODOPER
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
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        for nome in arquivos:
            with open(nome, "r", encoding='utf-8') as f:
                content = f.read()
            try:
                c = repo.get_contents(nome)
                repo.update_file(c.path, "Atualização de Performance", content, c.sha)
            except:
                repo.create_file(nome, "Início RotiFácil", content)
        return True
    except: return False

if __name__ == "__main__":
    print("🤖 RotiFácil: Monitorando Fluxo e Performance...")
    while True:
        f2 = extrair(2, "vendas_filial2.csv")
        f5 = extrair(5, "vendas_filial5.csv")
        if f2 or f5:
            if subir_github([f for f in ["vendas_filial2.csv", "vendas_filial5.csv"] if os.path.exists(f)]):
                print(f"✅ Sincronizado às {time.strftime('%H:%M:%S')}")
        time.sleep(300)