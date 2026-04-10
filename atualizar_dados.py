import oracledb
import pandas as pd
from github import Github
import os
import time
import platform

# --- CONFIGURAÇÕES DE ACESSO ---
DB_CONFIG = {
    "user": "NUTRICAO",
    "pass": "nutr1125mmf",
    "dsn": "192.168.222.20:1521/WINT"
}

# O Token deve estar nas variáveis de ambiente do Windows
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI") 
REPO_NAME = "hadassagarcia/RotiFluxo"

# --- ATIVANDO ORACLE CLIENT ---
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
        
        # SQL que garante pegar desde o dia 01 do mês atual
        query = f"""
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
              AND M.CODFILIAL = {filial} 
              AND M.DTCANCEL IS NULL
              AND M.CODOPER IN ('S', 'ST', 'SM', 'E', 'ED') 
              AND M.DTMOV >= TRUNC(SYSDATE, 'MM')
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), M.CODOPER, M.CODCLI
        """
        
        df = pd.read_sql(query, con=conn)
        conn.close()
        
        if not df.empty:
            df.to_csv(nome_arquivo, index=False)
            print(f"✅ Arquivo {nome_arquivo} gerado ({len(df)} linhas).")
            return True
        else:
            print(f"⚠️ Filial {filial} sem vendas no mês.")
            return False
    except Exception as e:
        print(f"❌ Erro na extração da Filial {filial}: {e}")
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
                repo.update_file(contents.path, f"Auto-sync {nome}", content, contents.sha)
            except:
                repo.create_file(nome, f"Criação de {nome}", content)
        print("🚀 GitHub atualizado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao subir para o GitHub: {e}")

if __name__ == "__main__":
    print("🤖 MONITOR ROTIVISION INICIADO")
    while True:
        # Tenta extrair das duas filiais
        sucesso_f2 = extrair_vendas(2, "vendas_filial2.csv")
        sucesso_f5 = extrair_vendas(5, "vendas_filial5.csv")
        
        # Se ao menos uma teve dados, sobe para o Git
        arquivos_para_subir = []
        if sucesso_f2: arquivos_para_subir.append("vendas_filial2.csv")
        if sucesso_f5: arquivos_para_subir.append("vendas_filial5.csv")
        
        if arquivos_para_subir:
            subir_github(arquivos_para_subir)
            
        print(f"💤 Aguardando 30 minutos... Próxima carga: {time.strftime('%H:%M:%S', time.localtime(time.time() + 1800))}")
        time.sleep(1800)