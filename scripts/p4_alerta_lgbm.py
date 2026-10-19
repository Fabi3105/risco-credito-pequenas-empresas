# -*- coding: utf-8 -*-
"""P4 — Alerta de discordância: o LightGBM (referência, AUC 0,740) é comparado ao scorecard (nota oficial) no teste.
Cada empresa recebe a faixa A-E nos dois modelos (mesmos quintis do treino em cada um). Discordância forte = 2 ou mais faixas
de diferença. Mede se a taxa real de nova dívida nesses casos segue mais o LightGBM ou o scorecard.
Saídas: resultados/p4_alerta_discordancia.csv, resultados/p4_matriz_faixas_scorecard_lgbm.csv, dados/processados_2023-05/p4_divergencia_teste.parquet"""
import gc, numpy as np, pandas as pd, lightgbm as lgb
from base import RAIZ, salvar
from p4_features import CATEG
P23 = RAIZ / "dados/processados_2023-05"
X = pd.read_parquet(P23 / "p4_X.parquet")
for c in CATEG: X[c] = X[c].astype('category')
tr, te = X.parte.eq('treino').values, X.parte.eq('teste').values
y = X.y_nova_divida.values.astype(int); cnpj = X.cnpj_basico.values
cols = [c for c in X.columns if c not in ('cnpj_basico', 'parte', 'y_nova_divida', 'y_fechou', 'y_fechou_div', 'secao')]
P = dict(objective='binary', learning_rate=0.08, num_leaves=63, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, verbose=-1, num_threads=2, seed=7)
m = lgb.train(P, lgb.Dataset(X.loc[tr, cols], y[tr]), 200)
p_tr = m.predict(X.loc[tr, cols]); p_te = m.predict(X.loc[te, cols]); cnpj_te = cnpj[te]; del X, m; gc.collect()
cortes = np.quantile(p_tr, [0.2, 0.4, 0.6, 0.8])   # probabilidade: maior = pior
fx_l = np.array(['A', 'B', 'C', 'D', 'E'])[np.searchsorted(cortes, p_te, side='right')]
s = pd.read_parquet(P23 / "p4_notas_teste.parquet").set_index('cnpj_basico').loc[cnpj_te]
d = pd.DataFrame(dict(faixa_scorecard=s.faixa.values, faixa_lgbm=fx_l, y=s.y_nova_divida.values, p_sc=s.pd_prevista.values, p_lgbm=p_te))
mat = d.pivot_table(index='faixa_scorecard', columns='faixa_lgbm', values='y', aggfunc=['size', 'mean'])
salvar(mat.reset_index(), "p4_matriz_faixas_scorecard_lgbm.csv")
num = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}; dif = d.faixa_lgbm.map(num) - d.faixa_scorecard.map(num)
d['caso'] = np.select([dif >= 2, dif <= -2, dif.abs() == 1], ['LightGBM vê risco bem maior (2+ faixas)', 'LightGBM vê risco bem menor (2+ faixas)', 'diferença de 1 faixa'], 'mesma faixa')
r = d.groupby('caso').agg(empresas=('y', 'size'), nova_divida_real_pct=('y', lambda v: 100 * v.mean()),
      prevista_scorecard_pct=('p_sc', lambda v: 100 * v.mean()), prevista_lgbm_pct=('p_lgbm', lambda v: 100 * v.mean())).reset_index()
r['participacao_pct'] = 100 * r.empresas / len(d)
salvar(r.round(2), "p4_alerta_discordancia.csv")
import pathlib, shutil
tmp = pathlib.Path.home() / "tmp_div.parquet"; pd.DataFrame(dict(cnpj_basico=cnpj_te, divergencia_forte=(dif.abs() >= 2).values)).to_parquet(tmp)
shutil.move(str(tmp), str(P23 / "p4_divergencia_teste.parquet"))   # por empresa: usado no fluxo de decisão (p4_matriz_duas_notas.py)
pd.set_option("display.width", 200); print(r.round(2).to_string())
print((mat['size'] / len(d) * 100).round(1)); print((mat['mean'] * 100).round(1))
