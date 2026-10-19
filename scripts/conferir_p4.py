# -*- coding: utf-8 -*-
"""Conferências automáticas da nota v2 (rodar depois de p4_scorecard.py e gerar_anexo_p4.py)."""
import json, re, numpy as np, pandas as pd
from base import RAIZ
from p4_tabela import ORDENADAS
R = RAIZ / "resultados"; ok = []
def chk(nome, cond): ok.append(bool(cond)); print(('OK   ' if cond else 'FALHA'), nome)
for suf in ['', '_fechou']:
    k = pd.read_csv(R / f"p4_scorecard_constantes{suf}.csv").iloc[0]
    chk(f"fator = 20/ln2 {suf}", abs(k.fator - 20 / np.log(2)) < 1e-5); chk(f"offset {suf}", abs(k.offset - (600 - k.fator * np.log(20))) < 1e-5)
    chk(f"base por variável {suf}", abs(k.base_por_variavel - (k.offset - k.fator * k.constante_regressao) / k.n_variaveis) < 1e-5)
    pts = pd.read_csv(R / f"p4_scorecard_pontos{suf}.csv"); co = pd.read_csv(R / f"p4_scorecard_coeficientes{suf}.csv"); m = pts.merge(co, on=['variavel', 'faixa'])
    chk(f"pontos = base − fator × coeficiente ({len(m)} faixas) {suf}", np.allclose(m.pontos, k.base_por_variavel - k.fator * m.coeficiente, atol=1e-3))
    chk(f"15 variáveis {suf}", pts.variavel.nunique() == k.n_variaveis == 15)
    junta = json.load(open(R / f"p4_scorecard_juncoes{suf}.json", encoding='utf-8'))
    for v, ordem in ORDENADAS.items():
        g = dict(zip(pts[pts.variavel == v].faixa, pts[pts.variavel == v].pontos)); seq = []
        for c in ordem:
            cj = junta[v].get(c, c)
            if cj in g and (not seq or seq[-1][0] != cj): seq.append((cj, g[cj]))
        chk(f"ordem garantida em {v} {suf}", all(a[1] >= b[1] - 1e-9 for a, b in zip(seq, seq[1:])))
    ex = pd.read_csv(R / f"p4_exemplo_conta{suf}.csv"); nota = k.offset - k.fator * (k.constante_regressao + ex.coeficiente.sum())
    chk(f"exemplo: soma dos pontos = fórmula {suf}", abs(ex.pontos.sum() - nota) < 0.1)
    fx = pd.read_csv(R / f"p4_faixas{suf}.csv").sort_values('faixa'); chk(f"faixas A→E crescentes {suf}", fx.alvo_real_pct.is_monotonic_increasing)
    chk(f"previsto × real até 1,5 ponto {suf}", (fx.alvo_previsto_pct - fx.alvo_real_pct).abs().max() < 1.5)
    chk(f"curva crescente {suf}", pd.read_csv(R / f"p4_curva_aprovacao{suf}.csv").alvo_aprovados_pct.is_monotonic_increasing)
a = (RAIZ / "metodo/P4_nota_de_risco.md").read_text(encoding='utf-8'); k = pd.read_csv(R / "p4_scorecard_constantes.csv").iloc[0]
chk("anexo com a constante atual", f"{abs(k.constante_regressao):.6f}".replace('.', ',') in a); chk("anexo sem placeholders", not re.search(r'\{|\}|\bnan\b', a))
print(f"{sum(ok)}/{len(ok)} conferências OK")
