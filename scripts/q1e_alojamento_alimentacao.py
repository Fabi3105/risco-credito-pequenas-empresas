# -*- coding: utf-8 -*-
"""Alojamento e alimentação aberto por atividade (pedido do Fabian, 16/10/2026): hotéis e pousadas sofreram com a queda do
turismo na pandemia, enquanto comida para entrega cresceu. A seção CNAE "I" junta tudo isso; aqui ela é separada pela subclasse.
Medidas (turmas de 2012 a 2021, MEI/ME/EPP):
 1. aberturas por ano (2016 a 2021);
 2. sobrevivência em 5 anos (turmas 2016-2020) e fechamento comparado ao das OUTRAS atividades do mesmo porte (amostra de 10%; corrigido na 11ª revisão: antes o esperado incluía 55 e 56 inteiros e puxava a razão para 1);
 3. turmas da pandemia (2º sem. 2020 e 2021) x turmas de 2016-2019: encerramento voluntário em 3 anos, padronizado pelo porte;
 4. empresas já abertas: encerramento voluntário em cada ano civil (2017 a 2025) dividido pelo esperado para o mesmo porte e a
    mesma idade nas demais atividades (1 = igual ao resto da economia). Mostra o choque de 2020-2021 em quem já existia.
Outras atividades (esperado): amostra fixa de 10% por hash do CNPJ. Uso: python q1e_alojamento_alimentacao.py a|b
Saídas: resultados/q1e_atividades.csv, q1e_aberturas.csv, q1e_pandemia_turmas.csv, q1e_ano_civil.csv"""
import duckdb, pandas as pd
from base import PROC, salvar
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'; SET enable_progress_bar=false")
ATV = """CASE WHEN substr(cnae_principal,1,3) IN ('551','559') THEN '1 Hotéis, pousadas e outros alojamentos'
  WHEN cnae_principal = '5611201' THEN '2 Restaurantes' WHEN cnae_principal = '5611203' THEN '3 Lanchonetes, casas de chá e de sucos'
  WHEN cnae_principal IN ('5611204','5611205') THEN '4 Bares' WHEN cnae_principal = '5612100' THEN '5 Ambulantes de alimentação'
  WHEN cnae_principal = '5620104' THEN '6 Comida preparada para consumo em casa (marmitas, entrega)'
  WHEN substr(cnae_principal,1,4) = '5620' THEN '7 Alimentação para empresas e eventos (bufê, cantinas)' END"""
import sys
PASSO = sys.argv[1] if len(sys.argv) > 1 else 'todos'   # 'a' = medidas 1 a 3; 'b' = medida 4 (rodar em separado na VM)
# outras atividades: amostra fixa de 10% (por hash do CNPJ) basta para as taxas esperadas; alojamento e alimentação entram inteiros
con.execute(f"""CREATE TABLE t AS SELECT {ATV} atividade, grupo, turma, data_inicio, dur, evento, ev_vol,
  date_add(data_inicio, INTERVAL (CAST(round(dur * 365.25) AS INTEGER)) DAY) data_fim
  FROM read_parquet('{PROC}/q1_turmas.parquet') WHERE grupo IN ('MEI','ME','EPP') AND cnae_principal <> '4110700'
    AND (substr(cnae_principal,1,2) IN ('55','56') OR hash(cnpj_basico) % 10 = 0)""")
if PASSO in ('a', 'todos'):
 # 1. aberturas
 ab = con.execute("SELECT atividade, turma, count(*) aberturas FROM t WHERE atividade IS NOT NULL AND turma >= 2016 GROUP BY ALL ORDER BY ALL").df()
 ab = ab.pivot(index='atividade', columns='turma', values='aberturas').reset_index(); ab['cresc_2021_vs_2019_pct'] = 100 * (ab[2021] / ab[2019] - 1)
 salvar(ab.round(1), "q1e_aberturas.csv")
 # 2. sobrevivência em 5 anos e fechamento contra o esperado para o porte (taxa de todas as atividades do mesmo porte)
 con.execute("CREATE TABLE e5 AS SELECT grupo, avg((evento AND dur < 5)::INT) e FROM t WHERE turma BETWEEN 2016 AND 2020 AND atividade IS NULL GROUP BY 1")
 s5 = con.execute("""SELECT atividade, count(*) empresas_2016_2020, 100*avg((grupo='MEI')::INT) pct_mei, 100*(1-avg((evento AND dur<5)::INT)) sobrevive_5a,
   sum((evento AND dur<5)::INT)/sum(e) razao_fechamento_5a FROM t JOIN e5 USING (grupo) WHERE turma BETWEEN 2016 AND 2020 AND atividade IS NOT NULL GROUP BY 1 ORDER BY 1""").df()
 salvar(s5.round(3), "q1e_atividades.csv")
 # 3. turmas da pandemia x anteriores (encerramento voluntário em 3 anos, padronizado pelo porte das turmas de 2016-2019)
 pt = con.execute("""WITH x AS (SELECT atividade, grupo, CASE WHEN turma <= 2019 THEN 'antes' WHEN data_inicio >= DATE '2020-07-01' THEN 'pandemia' END epoca,
     (ev_vol AND dur < 3)::INT v3 FROM t WHERE atividade IS NOT NULL AND turma >= 2016),
   r AS (SELECT atividade, grupo, avg(v3) FILTER (WHERE epoca='antes') r_antes FROM x GROUP BY ALL)
   SELECT atividade, count(*) FILTER (WHERE epoca='pandemia') empresas_pandemia, 100*avg(v3) FILTER (WHERE epoca='antes') vol3_antes_pct,
     100*avg(v3) FILTER (WHERE epoca='pandemia') vol3_pandemia_pct,
     sum(v3) FILTER (WHERE epoca='pandemia') / sum(r_antes) FILTER (WHERE epoca='pandemia') razao_pandemia_vs_antes
   FROM x JOIN r USING (atividade, grupo) GROUP BY 1 ORDER BY 1""").df()
 salvar(pt.round(3), "q1e_pandemia_turmas.csv")
if PASSO in ('b', 'todos'):
 # 4. ano civil: empresas ativas em 1º de janeiro, com 1 a 9 anos de idade; encerramento voluntário no ano x esperado (outras atividades, mesmo porte e idade)
 con.execute("""CREATE TABLE a AS SELECT coalesce(atividade, 'outras') atividade, grupo, y ano, CAST(floor(date_diff('day', data_inicio, make_date(y,1,1)) / 365.25) AS INT) idade,
     (ev_vol AND data_fim >= make_date(y,1,1) AND data_fim < make_date(y+1,1,1))::INT v
   FROM t, range(2017, 2026) r(y) WHERE data_inicio < make_date(y-1,1,1) AND (NOT evento OR data_fim >= make_date(y,1,1))""")
 ac = con.execute("""WITH e AS (SELECT grupo, ano, idade, avg(v) e FROM a WHERE atividade = 'outras' GROUP BY ALL)
   SELECT atividade, ano, count(*) ativas_1jan, 100*avg(v) encerramento_vol_pct, sum(v)/sum(e) razao_vs_resto
   FROM a JOIN e USING (grupo, ano, idade) WHERE atividade <> 'outras' AND idade BETWEEN 1 AND 9 GROUP BY ALL ORDER BY ALL""").df()
 salvar(ac.round(3), "q1e_ano_civil.csv")
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 40)
if PASSO in ('a', 'todos'): print(ab.round(1).to_string()); print(s5.round(2).to_string()); print(pt.round(3).to_string())
if PASSO in ('b', 'todos'): print(ac.pivot(index='atividade', columns='ano', values='razao_vs_resto').round(2).to_string())
