# No seu arquivo atualizar_dados.py
query = f"""
    SELECT 
        P.DESCRICAO AS "Produto", 
        TRUNC(M.DTMOV) AS "Data", 
        TO_CHAR(M.DTMOV, 'HH24') AS "Hora", -- Nova Coluna
        M.CODOPER, 
        SUM(M.QT) AS "Qtd_KG", 
        SUM(ROUND(M.QT * M.PUNIT, 2)) AS "Valor_Final" 
    FROM MMFRIOS.PCMOV M
    JOIN MMFRIOS.PCPRODUT P ON M.CODPROD = P.CODPROD
    WHERE P.CODEPTO = 105 
      AND M.CODFILIAL = {filial} 
      AND M.DTCANCEL IS NULL
      AND M.CODOPER = 'S' -- Foco apenas em vendas para Ruptura
      AND M.DTMOV >= TRUNC(SYSDATE, 'MM')
    GROUP BY P.DESCRICAO, TRUNC(M.DTMOV), TO_CHAR(M.DTMOV, 'HH24'), M.CODOPER
"""