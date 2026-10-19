# -*- coding: utf-8 -*-
"""Teste de hipótese: as enchentes de maio/2024 no RS explicam parte do fechamento acima do esperado em cidades como
Lajeado, Venâncio Aires e Eldorado do Sul? Compara as baixas voluntárias (data da situação) de jun/2024 a mai/2025 com as de
jun/2022 a mai/2023, por município, e com a mesma relação no restante do Brasil. Só baixa voluntária: a inaptidão depende do
calendário da Receita. Saída: resultados/q1d_rs_baixas_pos_enchente.csv"""
import duckdb, pandas as pd
from base import PROC, salvar
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='2000MB'; SET enable_progress_bar=false")
r = con.execute(f"""WITH b AS (SELECT uf, municipio_rf, data_situacao FROM read_parquet('{PROC}/base/*.parquet')
     WHERE situacao = 8 AND motivo_situacao IN (1, 54, 9) AND substr(lpad(natureza_juridica::varchar, 4, '0'), 1, 1) = '2'
       AND data_situacao BETWEEN DATE '2022-06-01' AND DATE '2025-05-31'),
  g AS (SELECT uf = 'RS' rs, uf, municipio_rf, count(*) FILTER (WHERE data_situacao BETWEEN DATE '2022-06-01' AND DATE '2023-05-31') antes,
                 count(*) FILTER (WHERE data_situacao BETWEEN DATE '2024-06-01' AND DATE '2025-05-31') depois FROM b GROUP BY ALL),
  nm AS (SELECT lpad(column0, 4, '0') cod, column1 municipio FROM read_csv('{PROC}/aux/Municipios.csv', delim=';', header=false, all_varchar=true))
  SELECT g.*, nm.municipio FROM g LEFT JOIN nm ON nm.cod = lpad(g.municipio_rf::VARCHAR, 4, '0')""").df()
fora = r[~r.rs]; base_br = fora.depois.sum() / fora.antes.sum()
rs = r[r.rs].copy(); rs['razao_depois_antes'] = rs.depois / rs.antes; rs['relativo_ao_brasil'] = rs.razao_depois_antes / base_br
rs = rs[rs.antes >= 100].sort_values('relativo_ao_brasil', ascending=False)
print('Brasil sem RS: depois/antes =', round(base_br, 3), '| RS:', round(r[r.rs].depois.sum() / r[r.rs].antes.sum(), 3))
salvar(rs.round(3), "q1d_rs_baixas_pos_enchente.csv")
pd.set_option('display.width', 200); print(rs[['municipio', 'antes', 'depois', 'razao_depois_antes', 'relativo_ao_brasil']].head(20).round(2).to_string())
print(rs[rs.municipio.isin(['LAJEADO', 'VENANCIO AIRES', 'ELDORADO DO SUL', 'SAO JERONIMO', 'BUTIA', 'CANOAS', 'PORTO ALEGRE', 'GARIBALDI', 'CAXIAS DO SUL'])][['municipio', 'antes', 'depois', 'relativo_ao_brasil']].round(2).to_string())
