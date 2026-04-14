import oracledb
import pandas as pd
from github import Github
import os, time, platform

# --- CONFIGURAÇÕES ---
DB_CONFIG = {"user": "NUTRICAO", "pass": "nutr1125mmf", "dsn": "192.168.222.20:1521/WINT"}
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_ROTI")
REPO_NAME = "hadassagarcia/RotiFluxo"

# --- ATIVANDO ORACLE CLIENT (IMPORTANTE PARA O ERRO DPY-3010) ---
try:
    if platform.system() == "Windows":
        # Apontando para a sua pasta do Instant Client
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        print("✅ Oracle Client Ativado com Sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao ativar Oracle Client: {e}")

def extrair(filial, arquivo):
    try:
        conn = oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["pass"], dsn=DB_CONFIG["dsn"])
        
        # SQL revisado: sem ponto e vírgula no final e com espaços garantidos
        query = f"""
            SELECT 
                P.DESCRICAO AS "Produto", 
                TRUNC(M.DTMOV) AS "Data", 
                TO_CHAR(M.DTMOV, 'HH24') AS "Hora",
                M.CODOPER, 
                SUM(M.QT) AS "Qtd_KG", 
                SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105 
              AND M.CODFILIAL = {filial} 
              AND M.DTCANCEL IS NULL
              AND M.CODOPER = 'S'
              AND M.DTMOV >= TRUNC(SYSDATE, 'MM')
            GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), TO_CHAR(M.DTMOV, 'HH24'), M.CODOPER
        """
        
        df = pd.read_sql(query, con=conn)
        conn.close()
        
        if not df.empty:
            df.to_csv(arquivo, index=False)
            return True
        return False
    except Exception as e:
        print(f"❌ Erro na extração da F{filial}: {e}")
        return False
        df = pd.read_sql(query, con=conn)
        conn.close()
        if not df.empty:
            df.to_csv(arquivo, index=False)
            return True
        return False
    except Exception as e:
        print(f"❌ Erro na extração da F{filial}: {e}")
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
                repo.update_file(c.path, "RotiFácil Precisão", content, c.sha)
            except:
                repo.create_file(nome, "RotiFácil Init", content)
        print("🚀 GitHub atualizado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao subir para o GitHub: {e}")

if __name__ == "__main__":
    print("🤖 RotiFácil: Ajustando precisão de checkout...")
    while True:
        # Extrai os dados
        f2_ok = extrair(2, "vendas_filial2.csv")
        f5_ok = extrair(5, "vendas_filial5.csv")
        
        # Sobe os arquivos que deram certo
        lista_envio = []
        if f2_ok: lista_envio.append("vendas_filial2.csv")
        if f5_ok: lista_envio.append("vendas_filial5.csv")
        
        if lista_envio:
            subir_github(lista_envio)
            print(f"✅ Sincronizado às {time.strftime('%H:%M:%S')}")
        
        print(f"💤 Aguardando 30 minutos...")
        time.sleep(1800)