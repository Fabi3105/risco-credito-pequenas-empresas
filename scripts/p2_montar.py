# -*- coding: utf-8 -*-
"""Tabela de características na abertura (P2 e P4), turmas 2012-2020: q1_turmas + histórico dos sócios (C1) +
população e PIB per capita do município no ano de abertura + saturação do setor (C2, anos 2016-2020).
Saída: dados/processados/p2/p2_<a>_<b>.parquet"""
import sys, pathlib, shutil
from base import conectar, PROC
a, b = int(sys.argv[1]), int(sys.argv[2])   # faixa de turmas
out = PROC / "p2"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_p2_{a}.parquet"
con = conectar(); con.execute("SET threads=2; SET memory_limit='2200MB'")
con.execute(f"""COPY (
WITH c1 AS (SELECT cnpj_basico, sum(n_socios_pf) n_socios_pf, max(faixa_etaria_max) faixa_etaria_max, min(faixa_etaria_min) faixa_etaria_min,
                   sum(n_empresas_anteriores_socios) n_emp_ant, sum(n_fechadas_antes) n_fech_ant,
                   sum(n_fechadas_com_divida_antes) n_fech_div_ant, sum(n_ativas_na_abertura) n_ativas_ab
            FROM read_parquet('{PROC}/c1/*.parquet') GROUP BY 1),
mp AS (SELECT uf, municipio_rf, cod_ibge FROM read_csv('{PROC}/municipios_rf_ibge.csv')),
mu AS (SELECT * FROM read_parquet('{PROC}/municipios_ano.parquet')),
sat AS (SELECT uf, municipio_rf, divisao, ano, saturacao, saturacao_tabela FROM read_parquet('{PROC}/q2_saturacao.parquet'))
SELECT t.*, c1.n_socios_pf, c1.faixa_etaria_max, c1.faixa_etaria_min, coalesce(c1.n_emp_ant, 0) n_emp_ant,
       coalesce(c1.n_fech_ant, 0) n_fech_ant, coalesce(c1.n_fech_div_ant, 0) n_fech_div_ant, coalesce(c1.n_ativas_ab, 0) n_ativas_ab,
       mp.cod_ibge, mu.populacao, mu.pib_per_capita, sat.saturacao, sat.saturacao_tabela
FROM (SELECT * FROM read_parquet('{PROC}/q1_turmas.parquet') WHERE turma BETWEEN {a} AND {b}) t
LEFT JOIN c1 USING (cnpj_basico)
LEFT JOIN mp ON mp.uf = t.uf AND mp.municipio_rf = t.municipio_rf
LEFT JOIN mu ON mu.cod_ibge = mp.cod_ibge AND mu.ano = t.turma
LEFT JOIN sat ON sat.uf = t.uf AND sat.municipio_rf = t.municipio_rf AND sat.divisao = substr(t.cnae_principal, 1, 2) AND sat.ano = t.turma
) TO '{tmp}' (FORMAT parquet)""")
shutil.move(str(tmp), str(out / f'p2_{a}_{b}.parquet'))
print(con.execute(f"select count(*), count(n_socios_pf), count(populacao), count(saturacao) from '{out}/p2_{a}_{b}.parquet'").fetchall())
