# -*- coding: utf-8 -*-
"""P1 por cidade — Sobrevivência em 5 anos das empresas abertas de 2016 a 2020 (medida direta), por município.
Para comparar cidades com misturas diferentes de porte e setor, cada cidade é comparada com o esperado para a sua mistura
(taxa nacional de cada porte x divisão CNAE) -> razão de fechamento observado/esperado (1 = igual ao Brasil; 0,9 = fecha 10% menos).
Margem de 95% da razão (aproximação binomial pelo esperado): 1,96 × raiz(soma e(1−e)) ÷ soma e.
Também a baixa voluntária (comparável entre regiões, sem depender do ritmo de fiscalização).
Saídas: resultados/q1c_municipios.csv (municípios com 500+ empresas na amostra de turmas), q1c_rs_municipios.csv, q1c_uf.csv"""
import duckdb, pandas as pd
from base import PROC, salvar
import metodos as M
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='2000MB'; SET enable_progress_bar=false")
a, b = M.TURMAS_CURTO
con.execute(f"""CREATE TABLE t AS SELECT uf, municipio_rf, grupo, substr(cnae_principal, 1, 2) divisao,
  (evento AND dur < 5)::INT f5, (ev_vol AND dur < 5)::INT v5
  FROM read_parquet('{PROC}/q1_turmas.parquet') WHERE turma BETWEEN {a} AND {b} AND grupo IN ('MEI','ME','EPP') AND cnae_principal <> '4110700'""")
con.execute("CREATE TABLE e AS SELECT grupo, divisao, avg(f5) e5, avg(v5) ev5 FROM t GROUP BY ALL")
q = """SELECT {k}, count(*) empresas, 100 * (1 - avg(f5)) sobrevive_5a_pct, 100 * avg(f5) fechou_5a_pct, sum(f5) / sum(e5) razao_fechamento, 1.96 * sqrt(sum(e5 * (1 - e5))) / sum(e5) margem_95_razao,
  100 * avg(v5) baixa_vol_5a_pct, sum(v5) / sum(ev5) razao_baixa_vol, avg((grupo = 'MEI')::INT) pct_mei
  FROM t JOIN e USING (grupo, divisao) GROUP BY ALL"""
uf = con.execute(q.format(k='uf')).df().sort_values('razao_fechamento'); salvar(uf.round(3), "q1c_uf.csv")
m = con.execute(f"""WITH r AS ({q.format(k='uf, municipio_rf')}),
  nm AS (SELECT lpad(column0, 4, '0') cod, column1 municipio FROM read_csv('{PROC}/aux/Municipios.csv', delim=';', header=false, all_varchar=true)),
  mp AS (SELECT uf, municipio_rf, cod_ibge FROM read_csv('{PROC}/municipios_rf_ibge.csv')),
  pop AS (SELECT cod_ibge, populacao FROM read_parquet('{PROC}/municipios_ano.parquet') WHERE ano = 2025)
  SELECT r.*, nm.municipio, mp.cod_ibge, pop.populacao FROM r LEFT JOIN nm ON nm.cod = lpad(r.municipio_rf::VARCHAR, 4, '0')
  LEFT JOIN mp USING (uf, municipio_rf) LEFT JOIN pop USING (cod_ibge) WHERE r.empresas >= 500""").df()
salvar(m.round(3), "q1c_municipios.csv")
rs = m[m.uf == 'RS'].sort_values('razao_fechamento'); salvar(rs.round(3), "q1c_rs_municipios.csv")
pd.set_option('display.width', 220)
print(uf.round(3).to_string())
print(len(m), 'municípios;', len(rs), 'no RS')
c = ['municipio', 'empresas', 'sobrevive_5a_pct', 'razao_fechamento', 'razao_baixa_vol', 'pct_mei', 'populacao']
print(rs[c].head(12).round(3).to_string()); print(rs[c].tail(8).round(3).to_string())
big = rs[rs.empresas >= 10000].sort_values('razao_fechamento'); print(big[c].round(3).to_string())
print(rs[rs.municipio == 'GARIBALDI'][c].round(3).to_string())
