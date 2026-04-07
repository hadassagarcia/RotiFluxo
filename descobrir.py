import oracledb
import pandas as pd
from streamlit import secrets

# Conexão segura
user = secrets["winthor"]["usuario"]
password = secrets["winthor"]["senha"]
host = secrets["winthor"]["ip"]
port = secrets["winthor"]["porta"]
service = secrets["winthor"]["servico"]

def rastro_detalhado():
    dsn = f"{host}:{port}/{service}"
    try:
        oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_9")
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
        
        # SQL para ver os detalhes de cada venda e achar os R$ 104
        query = """
            SELECT 
                P.DESCRICAO,
                M.QT,
                M.PUNIT,
                (M.QT * M.PUNIT) as VALOR_BRUTO,
                NVL(M.VLDESCONTO, 0) as DESCONTO,
                M.PTABELA, -- Preço de tabela (para ver se há diferença)
                M.NUMTRANSVENDA -- Número da transação para auditoria
            FROM MMFRIOS.PCMOV M
            JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
            WHERE P.CODEPTO = 105
              AND M.CODFILIAL = 2
              AND M.DTCANCEL IS NULL
              AND M.CODOPER = 'S'
              AND M.DTMOV BETWEEN TO_DATE('01/04/2026', 'DD/MM/YYYY') 
                              AND TO_DATE('05/04/2026', 'DD/MM/YYYY')
            ORDER BY VALOR_BRUTO DESC
        """
        
        df = pd.read_sql(query, con=conn)
        conn.close()
        
        if not df.empty:
            print("\n--- 🔍 TOP 10 VENDAS PARA AUDITORIA ---")
            print(df.head(10).to_string(index=False))
            
            total_calculado = (df['VALOR_BRUTO'] - df['DESCONTO']).sum()
            print(f"\n💵 TOTAL LÍQUIDO NO DASHBOARD: R$ {total_calculado:,.2f}")
            print(f"🎯 ALVO NO WINTHOR (322):    R$ 6,670.00")
            print(f"⚠️ DIFERENÇA A LOCALIZAR:     R$ {total_calculado - 6670:,.2f}")
        else:
            print("Nenhum dado encontrado.")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    rastro_detalhado()