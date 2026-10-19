# -*- coding: utf-8 -*-
"""Aplica a tabela de pontos publicada (p4_scorecard_pontos + junções) a uma tabela com as variáveis de p4_tabela.py.
Mesma conta do anexo e da calculadora: faixa de cada variável → pontos → nota → probabilidade → faixa A–E.
Conferência (python p4_pontuar.py): refaz a nota das empresas do teste só com as tabelas e compara com o modelo."""
import json, numpy as np, pandas as pd
from base import RAIZ
from p4_tabela import VARIAVEIS
R = RAIZ / "resultados"
def pontuar(V, suf=''):
    pts = pd.read_csv(R / f"p4_scorecard_pontos{suf}.csv"); k = pd.read_csv(R / f"p4_scorecard_constantes{suf}.csv").iloc[0]
    cortes = pd.read_csv(R / f"p4_cortes_faixas{suf}.csv", float_precision='round_trip').nota.values
    junta = json.load(open(R / f"p4_scorecard_juncoes{suf}.json", encoding='utf-8'))
    nota = np.zeros(len(V))
    for v in VARIAVEIS:
        g = pts[pts.variavel == v]; mapa = dict(zip(g.faixa, g.pontos)); raro = mapa['outras (raras)']
        x = V[v].astype(object).where(V[v].notna(), 'sem dado').astype(str).map(lambda c: junta[v].get(c, c))
        nota += x.map(mapa).fillna(raro).values
    chance = k.ODDS_BASE * 2 ** ((nota - k.BASE) / k.PDO)
    return nota, 1 / (1 + chance), np.array(['E', 'D', 'C', 'B', 'A'])[np.searchsorted(cortes, nota, side='right')]
if __name__ == "__main__":
    P23 = RAIZ / "dados/processados_2023-05"
    for suf in ['', '_fechou']:
        X = pd.read_parquet(P23 / "p4_X2.parquet"); X = X[X.parte == 'teste'].sample(200000, random_state=1)
        n = pd.read_parquet(P23 / f"p4_notas_teste{suf}.parquet").set_index('cnpj_basico').loc[X.cnpj_basico]
        nota, p, fx = pontuar(X, suf); dif = np.abs(nota - n.nota.values)
        print(suf or 'divida', 'diferença máx', round(dif.max(), 4), 'mesma faixa', round((fx == n.faixa.values).mean() * 100, 3), '%')
