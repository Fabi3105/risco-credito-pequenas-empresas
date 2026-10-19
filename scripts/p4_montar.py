# -*- coding: utf-8 -*-
"""Tabela do modelo de risco (P4), desenho de ponto no tempo.
Universo: empresas de natureza empresarial ATIVAS na extração de mai/2023 (data de corte 2023-05-15).
Características: como estavam em mai/2023 (cadastro, Simples/MEI, sócios, dívida ativa inscrita até o corte,
histórico dos sócios em mai/2023, dívida ativa na posição de mar/2023 (PGFN 2023 T1, colunas t1_*), população e PIB per capita do município, saturação do setor em 2020).
Resultados até out/2026 (extração 2026-10 e PGFN 2026 T2):
  y_fechou      = baixada (menos reorganização) ou inapta, com data de situação depois do corte
  y_fechou_div  = y_fechou e com dívida ativa da União (devedor principal)
  y_nova_divida = primeira inscrição em dívida ativa depois do corte (fechando ou não) — alvo C6
Uso: python p4_montar.py <digito>  ->  dados/processados_2023-05/p4/p4_<d>.parquet"""
import sys, pathlib, shutil, duckdb
from base import RAIZ, PROC
import metodos as M
P23 = RAIZ / "dados/processados_2023-05"; CORTE = "2023-05-15"
d = sys.argv[1]
con = duckdb.connect(); tmpd = pathlib.Path.home() / "duck_tmp"
con.execute(f"SET threads=2; SET memory_limit='2200MB'; SET enable_progress_bar=false; SET temp_directory='{tmpd}'; SET preserve_insertion_order=false")
out = P23 / "p4"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_p4_{d}.parquet"
con.execute(f"""COPY (
WITH a AS (SELECT * FROM read_parquet('{P23}/base/base_{d}.parquet')
           WHERE situacao_23 = 2 AND substr(lpad(natureza_juridica::varchar, 4, '0'), 1, 1) = '2' AND uf <> 'EX'
             AND data_inicio >= DATE '1900-01-01' AND data_inicio < DATE '{CORTE}'),
h AS (SELECT cnpj_basico, situacao, data_situacao, motivo_situacao, n_inscricoes_pgfn, primeira_inscricao_pgfn, porte porte_26
      FROM read_parquet('{PROC}/base/base_{d}.parquet')),
pgn AS (SELECT cnpj_basico, min(data_inscricao) FILTER (WHERE data_inscricao >= DATE '{CORTE}') nova_inscricao,
               sum(valor) FILTER (WHERE data_inscricao >= DATE '{CORTE}') valor_nova
        FROM read_parquet('{PROC}/pgfn/*.parquet') WHERE cnpj_basico LIKE '{d}%' AND upper(tipo_devedor) = 'PRINCIPAL' GROUP BY 1),
pg1 AS (SELECT cnpj_basico, count(*) t1_inscricoes, sum(valor) t1_valor, bool_or(ajuizado) t1_ajuizado,
               count(*) FILTER (WHERE tipo_situacao = 'Em cobrança') t1_em_cobranca,
               count(*) FILTER (WHERE tipo_situacao = 'Benefício Fiscal') t1_beneficio_fiscal,
               count(*) FILTER (WHERE tipo_situacao IN ('Garantia', 'Suspenso por decisão judicial')) t1_garantia_suspensa,
               count(*) FILTER (WHERE sistema = 'previdenciaria') t1_previdenciaria, count(*) FILTER (WHERE sistema = 'FGTS') t1_fgts,
               min(data_inscricao) t1_primeira_inscricao
        FROM read_parquet('{P23}/pgfn_2023T1/*.parquet') WHERE cnpj_basico LIKE '{d}%' AND upper(tipo_devedor) = 'PRINCIPAL' GROUP BY 1),
c1 AS (SELECT cnpj_basico, sum(n_socios_pf) c1_socios_pf, max(faixa_etaria_max) faixa_etaria_max, min(faixa_etaria_min) faixa_etaria_min,
              sum(n_outras) n_outras, sum(n_outras_fechadas) n_outras_fechadas, sum(n_outras_fechadas_divida) n_outras_fechadas_divida,
              sum(n_outras_ativas) n_outras_ativas, sum(n_outras_ativas_divida) n_outras_ativas_divida
       FROM read_parquet('{P23}/c1/*.parquet') WHERE cnpj_basico LIKE '{d}%' GROUP BY 1),
mp AS (SELECT uf, municipio_rf, cod_ibge FROM read_csv('{PROC}/municipios_rf_ibge.csv')),
mu AS (SELECT cod_ibge, populacao, pib_per_capita FROM read_parquet('{PROC}/municipios_ano.parquet') WHERE ano = 2023),
sat AS (SELECT uf, municipio_rf, divisao, saturacao saturacao_2020 FROM read_parquet('{PROC}/q2_saturacao.parquet') WHERE ano = 2020)
SELECT a.*, date_diff('day', a.data_inicio, DATE '{CORTE}') / 365.25 idade_anos,
  (a.opcao_mei = 'S') mei_23, (a.opcao_simples = 'S') simples_23,
  CASE WHEN a.opcao_mei = 'S' THEN 'MEI' WHEN a.porte = 1 THEN 'ME' WHEN a.porte = 3 THEN 'EPP' ELSE 'Demais' END grupo_23,
  (a.ultima_entrada_socio >= DATE '{CORTE}' - INTERVAL 365 DAY) mudou_socio_12m,
  c1.* EXCLUDE (cnpj_basico), coalesce(pg1.t1_inscricoes, 0) t1_inscricoes, pg1.* EXCLUDE (cnpj_basico, t1_inscricoes), mp.cod_ibge, mu.populacao, mu.pib_per_capita, sat.saturacao_2020,
  h.cnpj_basico IS NOT NULL achada_2026, h.situacao situacao_26, h.data_situacao data_situacao_26, h.motivo_situacao motivo_26, h.porte_26,
  coalesce(h.situacao IN (4, 8) AND coalesce(h.motivo_situacao, 0) NOT IN {M.MOTIVOS_REORGANIZACAO} AND h.data_situacao >= DATE '{CORTE}', false) y_fechou,
  coalesce(h.situacao IN (4, 8) AND coalesce(h.motivo_situacao, 0) NOT IN {M.MOTIVOS_REORGANIZACAO} AND h.data_situacao >= DATE '{CORTE}'
           AND h.n_inscricoes_pgfn > 0, false) y_fechou_div,
  (pgn.nova_inscricao IS NOT NULL) y_nova_divida, pgn.valor_nova,
  coalesce(h.situacao = 8 AND h.motivo_situacao IN {M.MOTIVOS_REORGANIZACAO}, false) reorganizada
FROM a LEFT JOIN h USING (cnpj_basico) LEFT JOIN pgn USING (cnpj_basico) LEFT JOIN c1 USING (cnpj_basico) LEFT JOIN pg1 USING (cnpj_basico)
LEFT JOIN mp ON mp.uf = a.uf AND mp.municipio_rf = a.municipio_rf LEFT JOIN mu ON mu.cod_ibge = mp.cod_ibge
LEFT JOIN sat ON sat.uf = a.uf AND sat.municipio_rf = a.municipio_rf AND sat.divisao = substr(a.cnae_principal, 1, 2)
) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)""")
r = con.execute(f"select count(*), avg(achada_2026::int), avg(y_fechou::int), avg(y_fechou_div::int), avg(y_nova_divida::int), avg(mei_23::int) from '{tmp}'").fetchone()
shutil.move(str(tmp), str(out / f"p4_{d}.parquet")); print(d, r)
