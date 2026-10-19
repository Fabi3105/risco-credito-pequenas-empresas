# -*- coding: utf-8 -*-
"""C1 — Histórico dos sócios (pessoa física) na data de abertura da empresa. Só cálculos agregados; nenhum nome é usado.
Pessoa = código (hash de nome + CPF mascarado) gerado na conversão. Rodar por partição (1º caractere do código, 0-f):
  python c1_socios.py <p>   ->  dados/processados/c1/socios_hist_<p>.parquet
Para cada empresa e cada sócio PF, olha as OUTRAS empresas do mesmo sócio abertas antes dela:
  anteriores, fechadas antes da abertura, fechadas com dívida ativa, ativas na data da abertura."""
import sys, pathlib, shutil
from base import conectar, PROC
import metodos as M
p = sys.argv[1]
con = conectar(); con.execute("SET threads=2; SET memory_limit='2200MB'")
out = PROC / "c1"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_c1_{p}.parquet"
con.execute(f"""COPY (
WITH l AS (
  SELECT s.pessoa, s.cnpj_basico, s.faixa_etaria, b.data_inicio,
         CASE WHEN b.situacao IN (4, 8) AND coalesce(b.motivo_situacao, 0) NOT IN {M.MOTIVOS_REORGANIZACAO} THEN b.data_situacao END data_fechou,
         coalesce(b.n_inscricoes_pgfn, 0) > 0 tem_pgfn
  FROM socios s JOIN base b USING (cnpj_basico)
  WHERE s.tipo_socio = 2 AND s.pessoa LIKE '{p}%' AND b.uf <> 'EX'),
alvo AS (SELECT * FROM l WHERE year(data_inicio) BETWEEN 2012 AND 2020)
SELECT a.cnpj_basico,
  count(DISTINCT a.pessoa) n_socios_pf,
  max(a.faixa_etaria) faixa_etaria_max, min(a.faixa_etaria) faixa_etaria_min,
  count(o.cnpj_basico) n_empresas_anteriores_socios,
  count(o.cnpj_basico) FILTER (WHERE o.data_fechou < a.data_inicio) n_fechadas_antes,
  count(o.cnpj_basico) FILTER (WHERE o.data_fechou < a.data_inicio AND o.tem_pgfn) n_fechadas_com_divida_antes,
  count(o.cnpj_basico) FILTER (WHERE o.data_fechou IS NULL OR o.data_fechou >= a.data_inicio) n_ativas_na_abertura
FROM alvo a LEFT JOIN l o ON o.pessoa = a.pessoa AND o.cnpj_basico <> a.cnpj_basico AND o.data_inicio < a.data_inicio
GROUP BY a.cnpj_basico) TO '{tmp}' (FORMAT parquet)""")
n = con.execute(f"select count(*) from '{tmp}'").fetchone()[0]
shutil.move(str(tmp), str(out / f"socios_hist_{p}.parquet")); print(p, n)
