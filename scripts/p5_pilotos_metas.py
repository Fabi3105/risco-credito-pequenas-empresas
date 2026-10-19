# -*- coding: utf-8 -*-
"""Soluções — dimensionamento dos pilotos e apoio das metas (fórmulas da skill do Fabian).
Casos por grupo (proporções, 80% de poder, 5% de alarme falso) = 7,84 x [p0(1-p0) + p1(1-p1)] / efeito².
Inadimplência de referência: SCR.data, porte Micro e Pequeno, carteira inadimplida ÷ carteira ativa, média dos 12 meses até ago/2026.
Efeito esperado: dois cenários. Otimista = redução da curva de aprovação (aprovar 80% contra aprovar todos); conservador = metade dela,
porque a política atual do banco já recusa parte dos maus. Supõe-se a mesma redução proporcional na inadimplência bancária.
Aviso: p0 do SCR é estoque em valor; no piloto, usar a taxa de contratos com atraso acima de 90 dias do próprio banco. O tamanho é em CONCESSÕES.
Saídas: resultados/p5_pilotos.csv, resultados/p5_metas.csv, resultados/p5_viabilidade.csv (meses mínimos do piloto 1)"""
import duckdb, pandas as pd
from base import PROC, RES, salvar
con = duckdb.connect()
scr = con.execute(f"""SELECT CASE porte WHEN 'PJ - Micro' THEN 'Micro' ELSE 'Pequeno' END porte, sum(carteira_inadimplida_arrastada) / sum(carteira_ativa) inad
  FROM read_parquet('{PROC}/scr/*.parquet') WHERE porte IN ('PJ - Micro', 'PJ - Pequeno') AND data_base > DATE '2025-08-31' GROUP BY 1""").df().set_index('porte').inad
cv = pd.read_csv(RES / "p4_curva_aprovacao.csv").set_index('aprovacao_pct')
base = cv.loc[100, 'alvo_aprovados_pct']
n = lambda p0, p1: 7.84 * (p0 * (1 - p0) + p1 * (1 - p1)) / (p0 - p1) ** 2
lin = []
for porte, p0 in scr.items():
    red_otim = 1 - cv.loc[80, 'alvo_aprovados_pct'] / base   # aprovar 80% contra aprovar todos: teto do ganho
    for nome, red in [('otimista: redução da curva de aprovação (80% aprovados contra 100%)', red_otim), ('conservador: metade dessa redução (a política atual já filtra parte dos maus)', red_otim / 2)]:
        p1 = p0 * (1 - red)
        lin.append(dict(piloto='1 nota no fluxo de concessão', porte=porte, cenario=nome, inad_hoje_pct=100 * p0, inad_esperada_pct=100 * p1,
                        reducao_relativa_pct=100 * red, concessoes_por_grupo=round(n(p0, p1))))
for c0, c1 in [(0.02, 0.03)]:
    lin.append(dict(piloto='2 oferta ativa (conversão)', porte='todos', cenario=f"conversão {str(round(100 * c0, 1)).replace('.', ',').replace(',0', '')}% → {str(round(100 * c1, 1)).replace('.', ',').replace(',0', '')}%",
                    inad_hoje_pct=None, inad_esperada_pct=None, reducao_relativa_pct=None, concessoes_por_grupo=round(n(c0, c1))))
p = pd.DataFrame(lin); salvar(p.round(2), "p5_pilotos.csv")
metas = pd.DataFrame([dict(meta='Propostas de micro e pequenas pontuadas pela nota', dono='Gerência de crédito', hoje='0%', em_12_meses='100% no piloto', referencia_final='100% da carteira após o piloto', de_onde_vem='decisão do piloto'),
    dict(meta='Inadimplência das concessões do piloto (grupo com nota × grupo atual)', dono='Diretoria de crédito', hoje='medir no banco', em_12_meses='leitura só ao fim do piloto',
         referencia_final=f"{round(100 * (1 - cv.loc[80, 'alvo_aprovados_pct'] / base) / 2)}% a {round(100 * (1 - cv.loc[80, 'alvo_aprovados_pct'] / base))}% menor", de_onde_vem='cenários conservador e otimista do piloto 1')])
salvar(metas, "p5_metas.csv")
pd.set_option('display.width', 220); print(scr.round(4)); print('base', base); print(p.round(2).to_string()); print(metas.round(2).to_string())
# viabilidade (2ª e 3ª revisões): meses de concessão até o GRUPO COM NOTA atingir o tamanho. O sorteio divide as PROPOSTAS ao meio;
# o grupo com nota só concede às que passam no corte dos 80% (APROV_CORTE; o banco deve trocar pela taxa real nas suas propostas).
# Volume = propostas por mês que a política atual aprovaria no porte. Os meses são MÍNIMOS: supõem que a análise manual aprova tudo o que
# recebe (cerca de 1 em 4 das não recusadas); cada recusa dela alonga o piloto.
APROV_CORTE = 0.8
vi = []
for vol in [500, 1000, 2000, 5000, 10000]:
    lin_v = dict(propostas_aprovaveis_por_mes_no_porte=vol)
    for _, r in p[p.piloto.str.startswith('1')].iterrows():
        lin_v[f"meses_minimos_{r.porte.lower()}_{r.cenario.split(':')[0]}"] = round(r.concessoes_por_grupo / (0.5 * APROV_CORTE * vol), 1)
    vi.append(lin_v)
salvar(pd.DataFrame(vi), "p5_viabilidade.csv"); print(pd.DataFrame(vi).to_string())
