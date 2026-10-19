# -*- coding: utf-8 -*-
"""P1 — números oficiais do relatório (revisão aprovada pelo Fabian em 15/10/2026).
Medida direta por turma: 1, 3 e 5 anos nas turmas de 2016 a 2020 (todas com 5 anos completos e no mesmo regime de
fiscalização); 10 anos nas turmas de 2012 a 2015 (com aviso). Fora incorporação imobiliária (encerramento planejado).
Também: fechamento limpo x com dívida ativa em 5 anos, e risco anual de baixa voluntária por ano de vida.
Saídas: resultados/q1_oficial_grupo.csv, q1_oficial_secao.csv, q1_oficial_risco_anual.csv"""
import pandas as pd
from base import conectar, salvar, PROC
import metodos as M
con = conectar()
a, b = M.TURMAS_CURTO; c, d = M.TURMAS_10A
SEC = """CASE WHEN substr(cnae_principal,1,2) <= '03' THEN 'A' WHEN substr(cnae_principal,1,2) <= '09' THEN 'B' WHEN substr(cnae_principal,1,2) <= '33' THEN 'C'
 WHEN substr(cnae_principal,1,2) <= '39' THEN 'DE' WHEN substr(cnae_principal,1,2) <= '43' THEN 'F' WHEN substr(cnae_principal,1,2) <= '47' THEN 'G'
 WHEN substr(cnae_principal,1,2) <= '53' THEN 'H' WHEN substr(cnae_principal,1,2) = '55' THEN 'I1' WHEN substr(cnae_principal,1,2) = '56' THEN 'I2' WHEN substr(cnae_principal,1,2) <= '63' THEN 'J'
 WHEN substr(cnae_principal,1,2) <= '66' THEN 'K' WHEN substr(cnae_principal,1,2) <= '68' THEN 'L' WHEN substr(cnae_principal,1,2) <= '75' THEN 'M'
 WHEN substr(cnae_principal,1,2) <= '82' THEN 'N' WHEN substr(cnae_principal,1,2) <= '84' THEN 'O' WHEN substr(cnae_principal,1,2) <= '85' THEN 'P'
 WHEN substr(cnae_principal,1,2) <= '88' THEN 'Q' WHEN substr(cnae_principal,1,2) <= '93' THEN 'R' ELSE 'S' END"""
con.execute(f"""CREATE VIEW t AS SELECT *, {SEC} secao FROM read_parquet('{PROC / 'q1_turmas.parquet'}')
  WHERE NOT {M.PLANEJADO} AND grupo IN ('MEI', 'ME', 'EPP')""")
def tab(chave):
    curto = con.execute(f"""SELECT {chave}, count(*) empresas_2016_2020,
      100 * (1 - avg((evento AND dur < 1)::INT)) sobrevive_1a, 100 * (1 - avg((evento AND dur < 3)::INT)) sobrevive_3a,
      100 * (1 - avg((evento AND dur < 5)::INT)) sobrevive_5a, 100 * (1 - avg((ev_vol AND dur < 5)::INT)) sobrevive_5a_so_baixa_voluntaria,
      100 * avg((evento AND dur < 5 AND tem_pgfn)::INT) fechou_com_divida_5a, 100 * avg((evento AND dur < 5 AND NOT tem_pgfn)::INT) fechou_limpo_5a
      FROM t WHERE turma BETWEEN {a} AND {b} GROUP BY ALL""").df()
    dez = con.execute(f"""SELECT {chave}, count(*) empresas_2012_2015, 100 * (1 - avg((evento AND dur < 10)::INT)) sobrevive_10a,
      100 * (1 - avg((ev_vol AND dur < 10)::INT)) sobrevive_10a_so_baixa_voluntaria FROM t WHERE turma BETWEEN {c} AND {d} GROUP BY ALL""").df()
    return curto.merge(dez, on=chave.split(', '), how='left')
g = tab('grupo'); salvar(g.round(1), "q1_oficial_grupo.csv")
s = tab('secao, grupo'); salvar(s.round(1), "q1_oficial_secao.csv")
r = con.execute(f"""WITH x AS (SELECT grupo, ev_vol, dur FROM t WHERE turma BETWEEN {a} AND {b})
  SELECT grupo, k + 1 ano_de_vida, count(*) FILTER (WHERE dur >= k) em_risco, count(*) FILTER (WHERE ev_vol AND dur >= k AND dur < k + 1) baixas
  FROM x, range(0, 5) r(k) GROUP BY ALL ORDER BY ALL""").df()
r['risco_baixa_voluntaria_pct'] = 100 * r.baixas / r.em_risco; salvar(r.round(2), "q1_oficial_risco_anual.csv")
pd.set_option('display.width', 220); print(g.round(1).to_string()); print(r.pivot(index='ano_de_vida', columns='grupo', values='risco_baixa_voluntaria_pct').round(1))
print(s[s.grupo == 'ME'].sort_values('sobrevive_5a')[['secao', 'empresas_2016_2020', 'sobrevive_5a', 'fechou_com_divida_5a']].round(1).to_string())
