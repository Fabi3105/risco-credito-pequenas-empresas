# -*- coding: utf-8 -*-
"""P3 — Zoom no RS. O SCR só existe por UF, então dentro do RS a medida é a concentração de bons clientes por município
(faixa A/B nas duas notas e fora das regras de política, empresas ativas hoje, amostra de 10% x10), com população de 2025.
Saídas: resultados/p3_rs_segmentos.csv (setor x porte no RS, com SCR), p3_rs_municipios.csv"""
import duckdb, pandas as pd
from base import PROC, RES, salvar
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'; SET enable_progress_bar=false")
seg = pd.read_csv(RES / "p3_segmentos.csv"); rs = seg[seg.uf == 'RS'].copy()
salvar(rs, "p3_rs_segmentos.csv")
m = con.execute(f"""WITH n AS (SELECT * FROM read_parquet('{PROC}/p3/p3_notas_*.parquet') WHERE uf = 'RS' AND grupo IN ('MEI','ME','EPP')),
  nm AS (SELECT codigo, descricao FROM read_csv('{PROC}/aux/Municipios.csv', delim=';', header=false, all_varchar=true, names=['codigo','descricao'])),
  pop AS (SELECT cod_ibge, populacao FROM read_parquet('{PROC}/municipios_ano.parquet') WHERE ano = 2025)
  SELECT n.cod_ibge, any_value(nm.descricao) municipio, any_value(pop.populacao) populacao, 10 * count(*) empresas,
    10 * count(*) FILTER (WHERE faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL) bons,
    10 * count(*) FILTER (WHERE faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL AND grupo = 'EPP') bons_epp,
    10 * count(*) FILTER (WHERE faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL AND grupo = 'ME') bons_me
  FROM n LEFT JOIN nm ON lpad(nm.codigo, 4, '0') = lpad(n.municipio_rf::VARCHAR, 4, '0') LEFT JOIN pop USING (cod_ibge)
  GROUP BY 1 ORDER BY bons DESC""").df()
m['bons_pct'] = m.bons / m.empresas; m['bons_por_mil_hab'] = 1000 * m.bons / m.populacao
salvar(m.round(4), "p3_rs_municipios.csv")
pd.set_option('display.width', 200)
print(rs[['secao', 'porte_scr', 'empresas', 'bons', 'bons_pct', 'bons_pct_esperado', 'indice_atendimento', 'inad_scr', 'inad_br']].sort_values('bons', ascending=False).head(16).round(3).to_string())
print(m.head(15).round(3).to_string()); print(m[m.empresas >= 3000].sort_values('bons_por_mil_hab', ascending=False).head(12).round(3).to_string())
print(m[m.municipio.str.contains('GARIBALDI', na=False)].round(3).to_string())
