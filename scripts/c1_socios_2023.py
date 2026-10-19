# -*- coding: utf-8 -*-
"""C1 no retrato de mai/2023 (P4): para cada empresa ativa em mai/2023 e cada sócio PF do quadro de mai/2023,
as OUTRAS empresas do mesmo sócio na extração de 2023: fechadas até mai/2023, fechadas com dívida ativa na posição de mar/2023
(PGFN 2023 T1, sem informação do futuro), e ativas em mai/2023. Só agregados; nenhum nome. Uso: python c1_socios_2023.py <p 0-f>"""
import sys, pathlib, shutil, duckdb
from base import RAIZ
import metodos as M
P23 = RAIZ / "dados/processados_2023-05"
p = sys.argv[1]
con = duckdb.connect(); tmpd = pathlib.Path.home() / "duck_tmp"
con.execute(f"SET threads=2; SET memory_limit='2200MB'; SET enable_progress_bar=false; SET temp_directory='{tmpd}'; SET preserve_insertion_order=false")
out = P23 / "c1"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_c123_{p}.parquet"
con.execute(f"""COPY (
WITH d1 AS (SELECT cnpj_basico FROM read_parquet('{P23}/pgfn_2023T1_devedores.parquet')),
l AS (
  SELECT s.pessoa, s.cnpj_basico, s.faixa_etaria, s.data_entrada, b.situacao_23,
         b.situacao_23 IN (4, 8) AND coalesce(b.motivo_23, 0) NOT IN {M.MOTIVOS_REORGANIZACAO} fechada,
         d1.cnpj_basico IS NOT NULL tem_pgfn
  FROM read_parquet('{P23}/socios/*.parquet') s JOIN read_parquet('{P23}/base/*.parquet') b USING (cnpj_basico) LEFT JOIN d1 USING (cnpj_basico)
  WHERE s.tipo_socio = 2 AND s.pessoa LIKE '{p}%' AND b.uf <> 'EX'),
alvo AS (SELECT * FROM l WHERE situacao_23 = 2)
SELECT a.cnpj_basico, count(DISTINCT a.pessoa) n_socios_pf, max(a.faixa_etaria) faixa_etaria_max, min(a.faixa_etaria) faixa_etaria_min,
  count(o.cnpj_basico) n_outras, count(o.cnpj_basico) FILTER (WHERE o.fechada) n_outras_fechadas,
  count(o.cnpj_basico) FILTER (WHERE o.fechada AND o.tem_pgfn) n_outras_fechadas_divida,
  count(o.cnpj_basico) FILTER (WHERE o.situacao_23 = 2) n_outras_ativas,
  count(o.cnpj_basico) FILTER (WHERE o.situacao_23 = 2 AND o.tem_pgfn) n_outras_ativas_divida
FROM alvo a LEFT JOIN l o ON o.pessoa = a.pessoa AND o.cnpj_basico <> a.cnpj_basico
GROUP BY a.cnpj_basico) TO '{tmp}' (FORMAT parquet)""")
n = con.execute(f"select count(*) from '{tmp}'").fetchone()[0]
shutil.move(str(tmp), str(out / f"socios_hist_{p}.parquet")); print(p, n)
