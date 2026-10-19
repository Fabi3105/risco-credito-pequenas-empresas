# -*- coding: utf-8 -*-
"""C2 (parte 2) — fechamento em 5 anos por faixa de saturação do setor no município, turmas 2016-2020.
Comparação dentro do mesmo setor (divisão CNAE) e porte: razão entre fechamentos observados e esperados (padronização indireta).
Também por porte de cidade, para checar se o efeito não é só cidade grande x pequena."""
import pandas as pd
from base import conectar, salvar, PROC
import metodos as M, os
N = int(os.environ.get('NIVEL', '2'))   # 2 = divisão CNAE; 3 = grupo CNAE (sensibilidade)
SUF = '' if N == 2 else f'_n{N}'
con = conectar()
a, b = M.TURMAS_CURTO
con.execute(f"""CREATE TEMP TABLE f AS
  SELECT t.grupo, substr(t.cnae_principal, 1, {N}) divisao, t.uf, t.municipio_rf, t.turma,
         (t.evento AND t.dur < 5) fechou5, (t.evento AND t.dur < 5 AND t.tem_pgfn) fechou5_divida, s.saturacao, s.saturacao_tabela, s.populacao, s.densidade_10mil
  FROM read_parquet('{PROC / 'q1_turmas.parquet'}') t
  JOIN read_parquet('{PROC / f'q2_saturacao{SUF}.parquet'}') s
    ON s.uf = t.uf AND s.municipio_rf = t.municipio_rf AND s.divisao = substr(t.cnae_principal, 1, {N}) AND s.ano = t.turma
  WHERE t.turma BETWEEN {a} AND {b} AND t.cnae_principal <> '4110700'""")
con.execute("""CREATE TEMP TABLE f2 AS SELECT *, avg(fechou5::INT) OVER (PARTITION BY divisao, grupo) esp5,
   avg(fechou5_divida::INT) OVER (PARTITION BY divisao, grupo) esp5d,
   CASE WHEN saturacao_tabela < 0.5 THEN '1' WHEN saturacao_tabela < 0.8 THEN '2' WHEN saturacao_tabela < 1.25 THEN '3'
        WHEN saturacao_tabela < 2 THEN '4' ELSE '5' END faixa_tabela,
   CASE WHEN saturacao < 0.5 THEN '1. menos da metade do esperado' WHEN saturacao < 0.8 THEN '2. 0,5 a 0,8'
        WHEN saturacao < 1.25 THEN '3. 0,8 a 1,25 (no esperado)' WHEN saturacao < 2 THEN '4. 1,25 a 2'
        ELSE '5. mais do dobro do esperado' END faixa,
   CASE WHEN populacao < 20000 THEN '1. até 20 mil' WHEN populacao < 100000 THEN '2. 20 a 100 mil'
        WHEN populacao < 500000 THEN '3. 100 a 500 mil' ELSE '4. mais de 500 mil' END cidade FROM f""")
q = lambda por: con.execute(f"""SELECT {por}, count(*) empresas, round(100*avg(fechou5::INT),1) fecha5_pct,
     round(sum(fechou5::INT)/sum(esp5), 3) razao_obs_esp, round(100*avg(fechou5_divida::INT),1) fecha5_divida_pct,
     round(sum(fechou5_divida::INT)/sum(esp5d), 3) razao_obs_esp_divida
   FROM f2 GROUP BY ALL ORDER BY ALL""").df()
r1 = salvar(q("faixa"), f"q2_fechamento_por_saturacao{SUF}.csv")
r2 = salvar(q("grupo, faixa"), f"q2_fechamento_por_saturacao_porte{SUF}.csv")
r4 = salvar(q("faixa_tabela"), f"q2_fechamento_por_saturacao_tabela{SUF}.csv")
print(r4.to_string())
r3 = salvar(q("cidade, faixa"), f"q2_fechamento_por_saturacao_cidade{SUF}.csv")
print(r1.to_string()); print(r2.to_string()); print(r3.to_string())
