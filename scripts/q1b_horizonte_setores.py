# -*- coding: utf-8 -*-
"""P1 — revisão pedida pelo Fabian (15/10/2026).
(1) Base de cada horizonte: quantas turmas e empresas sustentam a sobrevivência em 1, 3, 5 e 10 anos, e a sobrevivência
    medida direto em cada turma (sem tábua de vida), para mostrar a faixa entre turmas.
(2) Agropecuária e construção: tipo de fechamento (voluntário x abandono/inapta), tempo até fechar e quanto dos fechamentos
    deixou dívida ativa (sinal de fechamento com problema) contra fechamentos limpos (encerramento planejado)."""
import pandas as pd
from base import conectar, salvar, PROC
import metodos as M
con = conectar()
con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{PROC / 'q1_turmas.parquet'}')")
EXT = f"date_diff('day', make_date(turma, 12, 31), DATE '{M.DATA_BASE}') / 365.25"   # acompanhamento mínimo da turma

# (1) sobrevivência direta por turma: só turmas em que todas as empresas já tiveram o horizonte completo
linhas = []
for h in (1, 3, 5, 10):
    df = con.execute(f"""SELECT turma, grupo, count(*) n, 100 * avg((NOT (evento AND dur < {h}))::INT) sobrevive
        FROM t WHERE {EXT} >= {h} GROUP BY ALL""").df()
    for g, x in df.groupby("grupo"):
        linhas.append({"horizonte_anos": h, "grupo": g, "turmas": f"{x.turma.min()}-{x.turma.max()}", "n_turmas": len(x),
                       "empresas": int(x.n.sum()), "sobrevive_pct_media": round((x.sobrevive * x.n).sum() / x.n.sum(), 1),
                       "pior_turma_pct": round(x.sobrevive.min(), 1), "melhor_turma_pct": round(x.sobrevive.max(), 1)})
salvar(pd.DataFrame(linhas).sort_values(["grupo", "horizonte_anos"]), "q1b_base_horizontes.csv")

# (2) setores: agropecuária (divisões 01-03) e construção (41-43), com subclasses de destaque
CL = """CASE WHEN cnae_principal = '4110700' THEN '41.10-7 Incorporação imobiliária'
  WHEN substr(cnae_principal,1,2) IN ('01','02','03') THEN 'Agropecuária (01-03)'
  WHEN substr(cnae_principal,1,2) = '41' THEN 'Construção de edifícios (41, sem incorporação)'
  WHEN substr(cnae_principal,1,2) = '42' THEN 'Obras de infraestrutura (42)'
  WHEN substr(cnae_principal,1,2) = '43' THEN 'Serviços especializados de construção (43)'
  ELSE 'Demais setores' END"""
s = con.execute(f"""SELECT {CL} setor, grupo, count(*) empresas,
     100 * avg((evento AND dur < 5)::INT) FILTER (WHERE {EXT} >= 5) fecha_5a_pct,
     100 * avg((situacao = 4 OR motivo_situacao IN (63, 67, 71, 73))::INT) FILTER (WHERE evento) abandono_pct_dos_fechamentos,
     median(dur) FILTER (WHERE evento) anos_ate_fechar_mediana,
     100 * avg(tem_pgfn::INT) FILTER (WHERE evento) fechadas_com_divida_ativa_pct,
     100 * avg(tem_pgfn::INT) FILTER (WHERE NOT evento) abertas_com_divida_ativa_pct
   FROM t GROUP BY ALL HAVING count(*) >= 1000 ORDER BY grupo, setor""").df().round(1)
salvar(s, "q1b_agro_construcao.csv")
# incorporação: natureza jurídica e duração (SPE fecha ao fim da obra)
inc = con.execute(f"""SELECT floor(dur)::INT anos_ate_fechar, count(*) n FROM t WHERE cnae_principal = '4110700' AND evento AND grupo <> 'MEI'
   GROUP BY 1 ORDER BY 1""").df()
salvar(inc, "q1b_incorporacao_duracao.csv")
print(pd.DataFrame(linhas).sort_values(["grupo","horizonte_anos"]).to_string()); print(s.to_string()); print(inc.T.to_string())
