# -*- coding: utf-8 -*-
"""P3 por município, todos os estados (decisão do Fabian, 16/10/2026): empresas ativas hoje (MEI, ME, EPP; amostra de 10% x10),
bons clientes (A/B nas duas notas e fora das regras de política), bons por mil habitantes, nota média e a sobrevivência em 5 anos (q1c).
O SCR não existe por município: o crédito fica no nível da UF. Saída: resultados/p3_municipios.csv"""
import duckdb, pandas as pd, json
from base import PROC, RAIZ, RES, salvar
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'; SET enable_progress_bar=false")
m = con.execute(f"""SELECT cod_ibge::BIGINT cod_ibge, any_value(uf) uf, 10 * count(*) empresas_ativas,
  10 * count(*) FILTER (WHERE faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL) bons,
  avg(p_divida) risco_divida_medio, avg(p_fechamento) risco_fechamento_medio
  FROM read_parquet('{PROC}/p3/p3_notas_*.parquet') WHERE grupo IN ('MEI','ME','EPP') AND cod_ibge IS NOT NULL GROUP BY 1""").df()
nomes = pd.DataFrame([dict(cod_ibge=x['municipio-id'], municipio=x['municipio-nome']) for x in json.load(open(RAIZ / 'dados/externos/ibge_municipios.json', encoding='utf-8'))])
pop = con.execute(f"SELECT cod_ibge::BIGINT cod_ibge, populacao, pib_per_capita FROM read_parquet('{PROC}/municipios_ano.parquet') WHERE ano = 2025").df()
q = pd.read_csv(RES / "q1c_municipios.csv")[['cod_ibge', 'empresas', 'sobrevive_5a_pct', 'razao_fechamento', 'margem_95_razao', 'razao_baixa_vol']].rename(columns={'empresas': 'empresas_turmas_2016_2020'})
q['cod_ibge'] = q.cod_ibge.astype('Int64')
r = m.merge(nomes, on='cod_ibge', how='left').merge(pop, on='cod_ibge', how='left').merge(q, on='cod_ibge', how='left')
r['bons_pct'] = r.bons / r.empresas_ativas; r['bons_por_mil_hab'] = 1000 * r.bons / r.populacao
r.loc[r.empresas_ativas < 300, ['bons_pct', 'bons_por_mil_hab', 'risco_divida_medio', 'risco_fechamento_medio']] = None   # base pequena (< 30 empresas na amostra)
salvar(r.round(4), "p3_municipios.csv")
print(len(r), 'municípios;', r.municipio.isna().sum(), 'sem nome;', r.bons_pct.notna().sum(), 'com base suficiente;', r.sobrevive_5a_pct.notna().sum(), 'com sobrevivência')
