# -*- coding: utf-8 -*-
"""C4 — MEIs que cresceram: MEIs ativos em mai/2023 que em out/2026 estão ativos, saíram do MEI e continuam no Simples
(saída por faturamento acima do teto; quem sai por dívida costuma ser excluído do Simples também).
Compara com quem continuou MEI e com quem saiu do MEI e do Simples. Mede nova dívida ativa (alvo da nota) em cada grupo.
Saídas: resultados/c4_mei_destino.csv, c4_mei_cresce_setor.csv, c4_mei_cresce_uf.csv"""
import duckdb, pandas as pd
from base import RAIZ, PROC, salvar
P23 = RAIZ / "dados/processados_2023-05"
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='2000MB'; SET enable_progress_bar=false")
partes = []
for d in range(10):
    partes.append(con.execute(f"""SELECT p.uf, substr(p.cnae_principal, 1, 2) divisao,
      CASE WHEN p.y_fechou THEN '4 fechou' WHEN b.situacao <> 2 THEN '5 outra situação'
           WHEN b.opcao_mei = 'S' THEN '1 continua MEI' WHEN b.opcao_simples = 'S' THEN '2 cresceu (saiu do MEI, segue no Simples)'
           ELSE '3 saiu do MEI e do Simples' END destino,
      count(*) n, sum(p.y_nova_divida::INT) nova_divida, sum((b.porte = 3)::INT) virou_epp
      FROM read_parquet('{P23}/p4/p4_{d}.parquet') p JOIN read_parquet('{PROC}/base/base_{d}.parquet') b USING (cnpj_basico)
      WHERE p.mei_23 AND p.cnae_principal <> '4110700' GROUP BY ALL""").df())
t = pd.concat(partes).groupby(['uf', 'divisao', 'destino'], as_index=False).sum()
de = t.groupby('destino', as_index=False)[['n', 'nova_divida', 'virou_epp']].sum()
de['pct'] = 100 * de.n / de.n.sum(); de['nova_divida_pct'] = 100 * de.nova_divida / de.n
salvar(de.round(2), "c4_mei_destino.csv"); print(de.round(2).to_string())
SEC = lambda d: next(s for lim, s in [(3,'A'),(9,'B'),(33,'C'),(39,'DE'),(43,'F'),(47,'G'),(53,'H'),(56,'I'),(63,'J'),(66,'K'),(68,'L'),(75,'M'),(82,'N'),(84,'O'),(85,'P'),(88,'Q'),(93,'R'),(99,'S')] if int(d) <= lim)
t['secao'] = t.divisao.map(lambda d: SEC(d) if str(d).isdigit() else 'S')
def resumo(chave, nome):
    g = t.groupby([chave, 'destino'], as_index=False)[['n', 'nova_divida']].sum()
    tot = g.groupby(chave).n.sum(); ativos = g[g.destino.str[0].isin(['1', '2', '3'])].groupby(chave).n.sum()
    cr = g[g.destino.str.startswith('2')].set_index(chave)
    r = pd.DataFrame({'meis_mai2023': tot, 'cresceram': cr.n, 'cresceram_pct_do_total': 100 * cr.n / tot,
                      'cresceram_pct_dos_ativos': 100 * cr.n / ativos, 'nova_divida_cresceram_pct': 100 * cr.nova_divida / cr.n}).reset_index()
    salvar(r.round(2), nome); return r
s = resumo('secao', "c4_mei_cresce_setor.csv"); u = resumo('uf', "c4_mei_cresce_uf.csv")
pd.set_option('display.width', 200)
print(s.sort_values('cresceram_pct_dos_ativos', ascending=False).round(2).to_string()); print(u.sort_values('cresceram_pct_dos_ativos', ascending=False).round(2).to_string())
