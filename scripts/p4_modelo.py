# -*- coding: utf-8 -*-
"""P4 — comparação de modelos (amostra de 10%, treino 70% / teste 30% por empresa).
Alvos: y_nova_divida (nova inscrição em dívida ativa da União depois de mai/2023 — alvo principal, decisão do Fabian em 16/10/2026)
e y_fechou (fechou). Dívida de mai/2023 medida pelo arquivo PGFN 2023 T1 (posição de mar/2023).
Uso: python p4_modelo.py <alvo> <geral|scorecard|setor>
  geral: LightGBM com e sem as variáveis de dívida
  scorecard: regressão logística com as variáveis em faixas (quantis do treino)
  setor: modelo geral avaliado em cada seção CNAE x modelo próprio da seção
Saída: resultados/p4_comparacao_<alvo>_<etapa>.csv"""
import sys, gc, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import roc_auc_score
from base import RAIZ, salvar
from p4_features import CATEG, DIVIDA, limites_faixas
ALVO, ETAPA = sys.argv[1], sys.argv[2]
X = pd.read_parquet(RAIZ / "dados/processados_2023-05/p4_X.parquet")
for c in CATEG: X[c] = X[c].astype('category')
tr, te = X.parte.eq('treino').values, X.parte.eq('teste').values
y = X[ALVO].values.astype(int)
X = X.drop(columns=['cnpj_basico', 'parte', 'y_nova_divida', 'y_fechou', 'y_fechou_div']); gc.collect()
P = dict(objective='binary', learning_rate=0.08, num_leaves=63, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, verbose=-1, num_threads=2)
def ks(yy, p):
    o = np.argsort(p); yy = yy[o]; c1 = np.cumsum(yy) / yy.sum(); c0 = np.cumsum(1 - yy) / (1 - yy).sum(); return float(np.max(np.abs(c1 - c0)))
def linha(modelo, grupo, m, p): a = roc_auc_score(y[m], p); return dict(alvo=ALVO, modelo=modelo, grupo=grupo, n_teste=int(m.sum()), taxa=y[m].mean(), auc=a, gini=2*a-1, ks=ks(y[m], p))
TODAS = [c for c in X.columns if c != 'secao']
out = []
if ETAPA == 'geral':
    for nome, cols in [('LightGBM, com dívida de mar/2023', TODAS), ('LightGBM, sem dívida de mar/2023', [c for c in TODAS if c not in DIVIDA])]:
        m = lgb.train(P, lgb.Dataset(X.loc[tr, cols], y[tr]), 200)
        p = m.predict(X.loc[te, cols]); out.append(linha(nome, 'todos', te, p))
        if 'com' in nome:
            imp = pd.Series(m.feature_importance('gain'), index=cols); imp = (imp / imp.sum()).sort_values(ascending=False).round(3)
            salvar(imp.rename('importancia').reset_index().rename(columns={'index': 'variavel'}), f"p4_importancia_{ALVO}.csv")
            print('importância:', imp.head(12).to_dict())
        del m; gc.collect()
elif ETAPA == 'scorecard':
    # Scorecard: cada variável numérica em até 10 faixas (quantis do treino) + categorias; regressão logística com penalização leve
    from sklearn.linear_model import LogisticRegression
    from scipy import sparse
    cols_sc = [c for c in TODAS if c != 'qualificacao']
    F = np.empty((len(X), len(cols_sc)), dtype=np.int16)
    for j, c in enumerate(cols_sc):
        if c in CATEG:
            F[:, j] = X[c].cat.codes.values
        else:
            v = X[c].values.astype(np.float64)
            q = limites_faixas(v[tr])
            F[:, j] = np.where(np.isnan(v), -1, np.searchsorted(q, v, side='right'))
        X.drop(columns=c, inplace=True)
    gc.collect()
    # codificação 0/1 feita à mão (o OneHotEncoder converte para objeto e não cabe na memória da VM).
    # Cada linha tem exatamente uma faixa por variável, então a matriz esparsa é montada direto. Faixas raras (<200 no treino) viram "outras".
    from scipy import sparse
    n, k = F.shape; off = 0; offs = []
    for j in range(k):
        v = F[:, j].astype(np.int32); v -= v.min()
        cont = np.bincount(v[tr], minlength=v.max() + 1)
        ok = cont >= 200; nov = np.full(len(cont), ok.sum(), dtype=np.int32); nov[ok] = np.arange(ok.sum())
        F[:, j] = nov[v]; offs.append(off); off += ok.sum() + 1
    ind = (F.astype(np.int32) + np.array(offs, dtype=np.int32)).ravel(); del F; gc.collect()
    Z = sparse.csr_matrix((np.ones(len(ind), dtype=np.float32), ind, np.arange(0, n * k + 1, k, dtype=np.int64)), shape=(n, off)); del ind; gc.collect()
    X = None; gc.collect()
    lr = LogisticRegression(C=1.0, max_iter=300, solver='lbfgs').fit(Z[tr], y[tr])
    out.append(linha('Scorecard (logística em faixas)', 'todos', te, lr.predict_proba(Z[te])[:, 1]))
else:
    m = lgb.train(P, lgb.Dataset(X.loc[tr, TODAS], y[tr]), 200); pg = m.predict(X.loc[te, TODAS]); del m; gc.collect()
    sec = X.secao.astype(str).values
    for s in sorted(set(sec)):
        ms_tr, ms_te = tr & (sec == s), te & (sec == s)
        if ms_te.sum() < 3000 or y[ms_te].sum() < 200: continue
        out.append(linha('geral avaliado na seção', s, ms_te, pg[sec[te] == s]))
        mm = lgb.train(P, lgb.Dataset(X.loc[ms_tr, TODAS], y[ms_tr]), 150)
        out.append(linha('próprio da seção', s, ms_te, mm.predict(X.loc[ms_te, TODAS]))); del mm; gc.collect()
r = pd.DataFrame(out).round(4); salvar(r, f"p4_comparacao_{ALVO}_{ETAPA}.csv"); pd.set_option('display.width', 200); print(r.to_string())
