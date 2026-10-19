# -*- coding: utf-8 -*-
"""P4 — Calibragem da nota contra a inadimplência bancária real (SCR.data, Banco Central).
SCR: inadimplência = carteira inadimplida arrastada / carteira ativa (em valor), média mensal de jan/2024 até o último mês,
porte Micro (MEI + ME) e Pequeno (EPP), por seção CNAE e por UF.
Nota: nova dívida ativa prevista pelo scorecard (média no teste) nos mesmos segmentos.
Mede se a nota ordena os segmentos como o SCR e estima o fator para converter "chance de nova dívida ativa" em
"chance de inadimplência bancária". Saída: resultados/p4_calibragem_scr_<recorte>.csv"""
import duckdb, pandas as pd, numpy as np
from scipy.stats import spearmanr, pearsonr
from base import RAIZ, PROC, salvar
P23 = RAIZ / "dados/processados_2023-05"
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'; SET enable_progress_bar=false")
SEC = {'A': 'Agricultura', 'B': 'Indústrias extrativas', 'C': 'Indústrias de transformação', 'F': 'Construção', 'G': 'Comércio',
       'H': 'Transporte', 'I': 'Alojamento', 'J': 'Informação', 'K': 'Atividades financeiras', 'L': 'Atividades imobiliárias',
       'M': 'Atividades profissionais', 'N': 'Atividades administrativas', 'P': 'Educação', 'Q': 'Saúde', 'R': 'Artes', 'S': 'Outras atividades'}
case_sec = "CASE " + " ".join(f"WHEN cnae_secao LIKE 'PJ - {v}%' THEN '{k}'" for k, v in SEC.items()) + " END"
con.execute(f"""CREATE TABLE scr AS SELECT {case_sec} secao, uf, CASE porte WHEN 'PJ - Micro' THEN 'Micro' ELSE 'Pequeno' END porte,
  data_base, sum(carteira_inadimplida_arrastada) inad, sum(carteira_ativa) cart
  FROM read_parquet('{PROC}/scr/*.parquet') WHERE porte IN ('PJ - Micro', 'PJ - Pequeno') GROUP BY ALL""")
con.execute(f"""CREATE TABLE nota AS SELECT CASE WHEN substr(a.cnae_principal,1,2) <= '03' THEN 'A' WHEN substr(a.cnae_principal,1,2) <= '09' THEN 'B' WHEN substr(a.cnae_principal,1,2) <= '33' THEN 'C' WHEN substr(a.cnae_principal,1,2) <= '39' THEN 'DE' WHEN substr(a.cnae_principal,1,2) <= '43' THEN 'F' WHEN substr(a.cnae_principal,1,2) <= '47' THEN 'G' WHEN substr(a.cnae_principal,1,2) <= '53' THEN 'H' WHEN substr(a.cnae_principal,1,2) <= '56' THEN 'I' WHEN substr(a.cnae_principal,1,2) <= '63' THEN 'J' WHEN substr(a.cnae_principal,1,2) <= '66' THEN 'K' WHEN substr(a.cnae_principal,1,2) <= '68' THEN 'L' WHEN substr(a.cnae_principal,1,2) <= '75' THEN 'M' WHEN substr(a.cnae_principal,1,2) <= '82' THEN 'N' WHEN substr(a.cnae_principal,1,2) <= '84' THEN 'O' WHEN substr(a.cnae_principal,1,2) <= '85' THEN 'P' WHEN substr(a.cnae_principal,1,2) <= '88' THEN 'Q' WHEN substr(a.cnae_principal,1,2) <= '93' THEN 'R' ELSE 'S' END secao, a.uf, CASE WHEN a.grupo_23 = 'EPP' THEN 'Pequeno' ELSE 'Micro' END porte,
  n.pd_prevista, n.y_nova_divida FROM read_parquet('{P23}/p4_notas_teste.parquet') n JOIN read_parquet('{P23}/p4_amostra.parquet') a USING (cnpj_basico)
  WHERE a.grupo_23 IN ('MEI', 'ME', 'EPP')""")
print(con.execute("select min(data_base), max(data_base) from scr").fetchall())
for nome, chave in [('secao_porte', 'secao, porte'), ('uf_porte', 'uf, porte'), ('secao', 'secao'), ('uf', 'uf')]:
    df = con.execute(f"""WITH s AS (SELECT {chave}, data_base, sum(inad) / sum(cart) taxa FROM scr WHERE secao IS NOT NULL GROUP BY ALL),
      s2 AS (SELECT {chave}, 100 * avg(taxa) inad_scr_pct FROM s GROUP BY ALL),
      n2 AS (SELECT {chave}, count(*) empresas_teste, 100 * avg(pd_prevista) nova_divida_prevista_pct, 100 * avg(y_nova_divida) nova_divida_real_pct FROM nota GROUP BY ALL)
      SELECT * FROM n2 JOIN s2 USING ({chave}) WHERE empresas_teste >= 500 ORDER BY ALL""").df()
    df['fator_scr_sobre_nota'] = df.inad_scr_pct / df.nova_divida_prevista_pct
    rs, ps = spearmanr(df.nova_divida_prevista_pct, df.inad_scr_pct); rp, pp = pearsonr(df.nova_divida_prevista_pct, df.inad_scr_pct)
    print(f"{nome}: {len(df)} segmentos, Spearman {rs:.2f} (p={ps:.3g}), Pearson {rp:.2f}; fator mediano {df.fator_scr_sobre_nota.median():.3f}")
    salvar(df.round(3), f"p4_calibragem_scr_{nome}.csv")
    if nome in ('secao', 'secao_porte'): print(df.round(2).to_string())
