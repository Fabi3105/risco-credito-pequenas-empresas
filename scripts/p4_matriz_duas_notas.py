# -*- coding: utf-8 -*-
"""P4 — Cruzamento das duas notas no teste: faixa de dívida (oficial) x faixa de fechamento.
Saídas: resultados/p4_matriz_divida_fechamento.csv (participação, nova dívida real e fechamento real por célula)
        resultados/p4_fluxo_decisao.csv (recusa, análise manual, aprovação), resultados/p4_bons_clientes.csv (bom cliente = A/B nas duas notas, antes e depois das regras de política de p4_tabela.REGRAS)"""
import pandas as pd
from base import RAIZ, salvar
P23 = RAIZ / "dados/processados_2023-05"
a = pd.read_parquet(P23 / "p4_notas_teste.parquet")[['cnpj_basico', 'faixa', 'y_nova_divida', 'y_fechou']]
b = pd.read_parquet(P23 / "p4_notas_teste_fechou.parquet")[['cnpj_basico', 'faixa']].rename(columns={'faixa': 'faixa_fechamento'})
g = pd.read_parquet(P23 / "p4_X2.parquet", columns=['cnpj_basico', 'regra_politica'])
d = a.merge(b, on='cnpj_basico').merge(g, on='cnpj_basico', how='left').rename(columns={'faixa': 'faixa_divida'})
r = d.groupby(['faixa_divida', 'faixa_fechamento']).agg(empresas=('y_fechou', 'size'), nova_divida_pct=('y_nova_divida', lambda v: 100 * v.mean()),
      fechou_pct=('y_fechou', lambda v: 100 * v.mean())).reset_index()
r['participacao_pct'] = 100 * r.empresas / len(d)
salvar(r.round(2), "p4_matriz_divida_fechamento.csv")
ab = d.faixa_divida.isin(['A', 'B']) & d.faixa_fechamento.isin(['A', 'B'])
lin = []
for nome, m in [('A/B nas duas notas', ab), ('A/B nas duas notas e fora das regras de política (definição oficial)', ab & d.regra_politica.isna()),
                ('A/B nas duas notas, mas barrada por regra de política', ab & d.regra_politica.notna()), ('todas as empresas do teste', d.faixa_divida.notna())]:
    lin.append(dict(grupo=nome, empresas=int(m.sum()), participacao_pct=100 * m.mean(), nova_divida_pct=100 * d.y_nova_divida[m].mean(), fechou_pct=100 * d.y_fechou[m].mean()))
for regra, q in d[d.regra_politica.notna()].groupby('regra_politica'):
    lin.append(dict(grupo='regra: ' + regra, empresas=len(q), participacao_pct=100 * len(q) / len(d), nova_divida_pct=100 * q.y_nova_divida.mean(), fechou_pct=100 * q.y_fechou.mean()))
bc = pd.DataFrame(lin); salvar(bc.round(2), "p4_bons_clientes.csv"); print(bc.round(2).to_string())
# fluxo de decisão proposto (3ª e 4ª revisões): faixa E da nota de dívida = abaixo do corte dos 80% (recusa), salvo divergência forte
# (na faixa E, divergência só pode ser o modelo de referência vendo risco menor) ; regra de política ou divergência forte = análise manual;
# o resto = aprovação pela nota. Também mede a fila se empresas com menos de 1 ano tiverem regra automática (limite baixo e prazo curto).
dv = pd.read_parquet(P23 / "p4_divergencia_teste.parquet"); d = d.merge(dv, on='cnpj_basico', how='left'); div = d.divergencia_forte.fillna(False)
rec = d.faixa_divida.eq('E') & ~div; man = ~rec & (d.regra_politica.notna() | div); rg = d.regra_politica
etapas = [('recusa: faixa E da nota de dívida (abaixo do corte dos 80%)', rec), ('análise manual: regra de política ou divergência forte', man),
          ('  motivo: aberta há menos de 1 ano', man & rg.eq('aberta há menos de 1 ano')), ('  motivo: excluída do Simples', man & rg.eq('excluída do Simples')),
          ('  motivo: dívida ativa em cobrança', man & rg.eq('dívida ativa em cobrança')), ('  motivo: só divergência forte', man & rg.isna()),
          ('  fila sem as empresas novas (se elas tiverem regra automática)', man & ~rg.eq('aberta há menos de 1 ano')),
          ('aprovação pela nota (sem análise manual)', ~rec & ~man)]
fl = pd.DataFrame([dict(etapa=n, empresas=int(m.sum()), participacao_pct=100 * m.mean(), nova_divida_pct=100 * d.y_nova_divida[m].mean(), fechou_pct=100 * d.y_fechou[m].mean()) for n, m in etapas])
fl['pct_das_aprovaveis'] = 100 * fl.empresas / (~rec).sum()
salvar(fl.round(4), "p4_fluxo_decisao.csv"); print(fl.round(2).to_string())
for c in ['participacao_pct', 'nova_divida_pct', 'fechou_pct']: print(c); print(r.pivot(index='faixa_divida', columns='faixa_fechamento', values=c).round(1))
