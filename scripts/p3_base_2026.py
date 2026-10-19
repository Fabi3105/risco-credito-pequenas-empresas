# -*- coding: utf-8 -*-
"""P3 — Retrato atual (extração de out/2026) para aplicar a nota de risco às empresas ativas hoje.
Amostra fixa de 10% das empresas de natureza empresarial ativas em out/2026 (sorteio pelo hash do CNPJ), fora incorporação.
Variáveis montadas igual às de mai/2023 (p4_montar + c1_socios_2023), mas com os dados de hoje:
cadastro 2026-10, dívida ativa PGFN 2026 T2 (posição de jun/2026), sócios 2026-10, população e PIB per capita 2025.
Uso: python p3_base_2026.py <digito 0-9>  ->  dados/processados/p3/p3_base_<d>.parquet"""
import sys, pathlib, shutil, duckdb
from base import PROC, DATA_BASE
import metodos as M
d = sys.argv[1]
con = duckdb.connect(); tmpd = pathlib.Path.home() / "duck_tmp"
con.execute(f"SET threads=2; SET memory_limit='2200MB'; SET enable_progress_bar=false; SET temp_directory='{tmpd}'; SET preserve_insertion_order=false")
out = PROC / "p3"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_p3_{d}.parquet"
B = f"read_parquet('{PROC}/base/*.parquet')"
con.execute(f"""COPY (
WITH a AS (SELECT * FROM read_parquet('{PROC}/base/base_{d}.parquet')
           WHERE situacao = 2 AND substr(lpad(natureza_juridica::varchar, 4, '0'), 1, 1) = '2' AND uf <> 'EX'
             AND data_inicio >= DATE '1900-01-01' AND cnae_principal <> '4110700' AND hash(cnpj_basico) % 10 = 0),
s AS (SELECT s.* FROM read_parquet('{PROC}/socios/*.parquet') s SEMI JOIN a USING (cnpj_basico) WHERE s.tipo_socio = 2),
pes AS (SELECT DISTINCT pessoa FROM s),
l AS (SELECT so.pessoa, so.cnpj_basico, b.situacao IN (4, 8) AND coalesce(b.motivo_situacao, 0) NOT IN {M.MOTIVOS_REORGANIZACAO} fechada,
             b.situacao = 2 ativa, b.n_inscricoes_pgfn > 0 tem_pgfn
      FROM read_parquet('{PROC}/socios/*.parquet') so SEMI JOIN pes USING (pessoa) JOIN {B} b USING (cnpj_basico)
      WHERE so.tipo_socio = 2 AND b.uf <> 'EX'),
c1 AS (SELECT s.cnpj_basico, count(DISTINCT s.pessoa) c1_socios_pf, max(s.faixa_etaria) faixa_etaria_max, min(s.faixa_etaria) faixa_etaria_min,
              max(s.data_entrada) ultima_entrada_socio,
              count(o.cnpj_basico) n_outras, count(o.cnpj_basico) FILTER (WHERE o.fechada) n_outras_fechadas,
              count(o.cnpj_basico) FILTER (WHERE o.fechada AND o.tem_pgfn) n_outras_fechadas_divida,
              count(o.cnpj_basico) FILTER (WHERE o.ativa) n_outras_ativas, count(o.cnpj_basico) FILTER (WHERE o.ativa AND o.tem_pgfn) n_outras_ativas_divida
       FROM s LEFT JOIN l o ON o.pessoa = s.pessoa AND o.cnpj_basico <> s.cnpj_basico GROUP BY 1),
pg AS (SELECT cnpj_basico, count(*) t1_inscricoes, sum(valor) t1_valor, bool_or(ajuizado) t1_ajuizado,
              count(*) FILTER (WHERE tipo_situacao = 'Em cobrança') t1_em_cobranca, count(*) FILTER (WHERE tipo_situacao = 'Benefício Fiscal') t1_beneficio_fiscal,
              count(*) FILTER (WHERE sistema = 'previdenciaria') t1_previdenciaria, min(data_inscricao) t1_primeira_inscricao
       FROM read_parquet('{PROC}/pgfn/*.parquet') WHERE cnpj_basico LIKE '{d}%' AND upper(tipo_devedor) = 'PRINCIPAL' GROUP BY 1),
mp AS (SELECT uf, municipio_rf, cod_ibge FROM read_csv('{PROC}/municipios_rf_ibge.csv')),
mu AS (SELECT cod_ibge, populacao, pib_per_capita FROM read_parquet('{PROC}/municipios_ano.parquet') WHERE ano = 2025),
sat AS (SELECT uf, municipio_rf, divisao, saturacao saturacao_2020 FROM read_parquet('{PROC}/q2_saturacao.parquet') WHERE ano = 2020)
SELECT a.cnpj_basico, a.uf, a.municipio_rf, mp.cod_ibge, a.cnae_principal, a.natureza_juridica, a.qualificacao_responsavel, a.porte,
  date_diff('day', a.data_inicio, DATE '{DATA_BASE}') / 365.25 idade_anos,
  CASE WHEN a.opcao_mei = 'S' THEN 'MEI' WHEN a.porte = 1 THEN 'ME' WHEN a.porte = 3 THEN 'EPP' ELSE 'Demais' END grupo_23,
  a.opcao_simples, a.opcao_mei, a.data_opcao_mei, a.capital_social, a.n_cnae_sec, a.tem_email, a.tem_telefone, a.tem_fantasia,
  a.n_filiais, a.n_socios_pf, a.n_socios_pj, mu.populacao, mu.pib_per_capita, sat.saturacao_2020,
  c1.c1_socios_pf, c1.faixa_etaria_max, c1.faixa_etaria_min, c1.n_outras, c1.n_outras_fechadas, c1.n_outras_fechadas_divida,
  c1.n_outras_ativas, c1.n_outras_ativas_divida, (c1.ultima_entrada_socio >= DATE '{DATA_BASE}' - INTERVAL 365 DAY) mudou_socio_12m,
  coalesce(pg.t1_inscricoes, 0) t1_inscricoes, pg.* EXCLUDE (cnpj_basico, t1_inscricoes)
FROM a LEFT JOIN c1 USING (cnpj_basico) LEFT JOIN pg USING (cnpj_basico)
LEFT JOIN mp ON mp.uf = a.uf AND mp.municipio_rf = a.municipio_rf LEFT JOIN mu ON mu.cod_ibge = mp.cod_ibge
LEFT JOIN sat ON sat.uf = a.uf AND sat.municipio_rf = a.municipio_rf AND sat.divisao = substr(a.cnae_principal, 1, 2)
) TO '{tmp}' (FORMAT parquet)""")
n = con.execute(f"select count(*), count(c1_socios_pf), avg((t1_inscricoes>0)::int) from '{tmp}'").fetchone()
shutil.move(str(tmp), str(out / f"p3_base_{d}.parquet")); print(d, n)
