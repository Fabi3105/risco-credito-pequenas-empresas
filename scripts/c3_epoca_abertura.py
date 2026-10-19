# -*- coding: utf-8 -*-
"""C3 — Época da abertura: pandemia e juros. Empresas abertas de 2016 a 2021, por semestre de abertura.
Medidas: fechou em 1 e 3 anos (total e só baixa voluntária) e fechou com dívida ativa em 3 anos.
Para separar a época da mistura de empresas (no auge da pandemia abriram muito mais MEIs), cada semestre é comparado
com o esperado para a sua mistura de porte x setor (taxa média 2016-2021 de cada porte x setor) -> razão observado/esperado.
Juros: Selic do mês de abertura e média dos 12 meses seguintes (BCB SGS 4189).
Saídas: resultados/c3_semestres.csv, c3_correlacoes.csv"""
import duckdb, pandas as pd, numpy as np
from scipy.stats import spearmanr
from base import PROC, RAIZ, salvar
import metodos as M
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='2000MB'; SET enable_progress_bar=false")
selic = pd.read_csv(RAIZ / "dados/externos/bcb_selic_sgs4189.csv")
con.register('selic', selic)
con.execute(f"""CREATE TABLE t AS SELECT year(data_inicio) || '-S' || (CASE WHEN month(data_inicio) <= 6 THEN 1 ELSE 2 END) semestre,
  strftime(data_inicio, '%Y-%m') mes, grupo, CASE WHEN substr(cnae_principal,1,2) IN ('55','56') THEN 'I' WHEN substr(cnae_principal,1,2) BETWEEN '45' AND '47' THEN 'G'
   WHEN substr(cnae_principal,1,2) BETWEEN '41' AND '43' THEN 'F' WHEN substr(cnae_principal,1,2) BETWEEN '10' AND '33' THEN 'C'
   WHEN substr(cnae_principal,1,2) BETWEEN '49' AND '53' THEN 'H' WHEN substr(cnae_principal,1,2) BETWEEN '69' AND '82' THEN 'MN'
   WHEN substr(cnae_principal,1,2) BETWEEN '85' AND '88' THEN 'PQ' ELSE 'outros' END setor,
  (evento AND dur < 1)::INT f1, (evento AND dur < 3)::INT f3, (ev_vol AND dur < 3)::INT v3, (evento AND dur < 3 AND tem_pgfn)::INT d3
  FROM read_parquet('{PROC}/q1_turmas.parquet') WHERE turma BETWEEN 2016 AND 2021 AND grupo IN ('MEI','ME','EPP') AND cnae_principal <> '4110700'""")
con.execute("""CREATE TABLE e AS SELECT grupo, setor, avg(f1) e1, avg(f3) e3, avg(v3) ev3, avg(d3) ed3 FROM t GROUP BY ALL""")
s = con.execute("""SELECT semestre, count(*) empresas, avg((grupo = 'MEI')::INT) pct_mei,
  100*avg(f1) fechou_1a, 100*avg(f3) fechou_3a, 100*avg(v3) baixa_vol_3a, 100*avg(d3) fechou_divida_3a,
  sum(f1)/sum(e1) razao_1a, sum(f3)/sum(e3) razao_3a, sum(v3)/sum(ev3) razao_vol_3a, sum(d3)/sum(ed3) razao_divida_3a
  FROM t JOIN e USING (grupo, setor) GROUP BY 1 ORDER BY 1""").df()
# Selic: média do semestre de abertura e dos 12 meses depois do meio do semestre
sel = selic.assign(data=pd.to_datetime(selic.mes + '-01'))
def selic_sem(sm):
    a, h = int(sm[:4]), int(sm[-1]); ini = pd.Timestamp(a, 1 if h == 1 else 7, 1)
    no = sel[(sel.data >= ini) & (sel.data < ini + pd.DateOffset(months=6))].selic_anualizada_pct.mean()
    dep = sel[(sel.data >= ini + pd.DateOffset(months=3)) & (sel.data < ini + pd.DateOffset(months=15))].selic_anualizada_pct.mean()
    return pd.Series({'selic_abertura': no, 'selic_12m_seguintes': dep})
s = pd.concat([s, s.semestre.apply(selic_sem)], axis=1)
s['epoca'] = np.select([s.semestre.isin(['2020-S1']), s.semestre.isin(['2020-S2', '2021-S1', '2021-S2'])], ['início da pandemia', 'pandemia'], 'antes')
salvar(s.round(3), "c3_semestres.csv")
cor = []
for medida in ['razao_1a', 'razao_3a', 'razao_vol_3a', 'razao_divida_3a']:
    for j in ['selic_abertura', 'selic_12m_seguintes']:
        r, p = spearmanr(s[j], s[medida]); cor.append(dict(medida=medida, juros=j, spearman=r, p_valor=p, semestres=len(s)))
salvar(pd.DataFrame(cor).round(3), "c3_correlacoes.csv")
pd.set_option('display.width', 250); print(s.round(3).to_string()); print(pd.DataFrame(cor).round(3).to_string())
