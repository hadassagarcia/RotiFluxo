import oracledb
import pandas as pd
from github import Github
import os
import time
import platform

# --- 1. CONFIGURAÇÕES DE ACESSO ---
DB_CONFIG = {
    "user": "NUTRICAO",
    "pass": "nutr1125mmf",
    "dsn": "192.168.222.20:1521/WINT"
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI") 
REPO_NAME = "hadassagarcia/RotiFluxo"

# --- 2. ATIVANDO ORACLE CLIENT ---
try:
    if platform.system() == "Windows":
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        print("✅ Oracle Client Ativado!")
except Exception as e:
    print(f"⚠️ Aviso Client: {e}")

def extrair_vendas(filial, nome_arquivo):
    try:
        print(f"🔗 Extraindo dados da Filial {filial}...")
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        
        # SQL DE PRECISÃO: Focado em capturar 100% das saídas (S) e devoluções (E, ED)
        query = f"""
            SELECT 
                P.DESCRICAO AS "Produto", 
                TRUNC(M.DTMOV) AS "Data",
                M.CODOPER,
                M.CODCLI,
                SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105 
              AND M.CODFILIAL = {filial} 
              AND M.DTCANCEL IS NULL
              AND M.CODOPER IN ('S', 'E', 'ED') 
              AND M.DTMOV >= TRUNC(SYSDATE, 'MM')
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), M.CODOPER, M.CODCLI
        """
        
        df = pd.read_sql(query, con=conn)
        conn.close()
        
        if not df.empty:
            df.to_csv(nome_arquivo, index=False)
            return True
        return False
    except Exception as e:
        print(f"❌ Erro na Filial {filial}: {e}")
        return False

def subir_github(arquivos):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        for nome in arquivos:
            with open(nome, "r", encoding='utf-8') as f:
                content = f.read()
            try:
                contents = repo.get_contents(nome)
                repo.update_file(contents.path, "RotiFácil Sync", content, contents.sha)
            except:
                repo.create_file(nome, "RotiFácil Init", content)
        print("🚀 GitHub atualizado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao subir para o GitHub: {e}")

if __name__ == "__main__":
    print("🤖 SISTEMA ROTIFÁCIL - SINCRONIZADOR ATIVO")
    while True:
        # Extrai as duas filiais de forma independente
        f2 = extrair_vendas(2, "vendas_filial2.csv")
        f5 = extrair_vendas(5, "vendas_filial5.csv")
        
        lista_envio = []
        if f2: lista_envio.append("vendas_filial2.csv")
        if f5: lista_envio.append("vendas_filial5.csv")
        
        if lista_envio:
            subir_github(lista_envio)
            
        print(f"💤 Aguardando 30 minutos... Próxima carga: {time.strftime('%H:%M:%S', time.localtime(time.time() + 1800))}")
        time.sleep(1800)