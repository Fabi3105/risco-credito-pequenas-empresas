# -*- coding: utf-8 -*-
"""P4 — Nota oficial v2: tabela de pontos com as variáveis de p4_tabela.py (todas em faixas fixas ou categorias).
Regressão logística com uma coluna 0/1 por faixa (faixas com menos de 200 empresas no treino viram "outras (raras)").
Nas variáveis ordenadas (perfil de dívida e histórico dos sócios), se duas faixas vizinhas saem fora de ordem, elas são
juntadas e o modelo é refeito (garante que mais risco nunca dá mais pontos).
Escala: 600 pontos = 20 bons para 1 mau; +20 pontos dobram a chance de ser bom. Faixas A–E: quintis da nota no treino.
Uso: python p4_scorecard.py [y_nova_divida|y_fechou]   (sufixo _fechou nos arquivos da segunda nota)"""
import sys, gc, json, numpy as np, pandas as pd, pathlib, shutil
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from base import RAIZ, salvar
from p4_tabela import VARIAVEIS, ORDENADAS
P23 = RAIZ / "dados/processados_2023-05"
ALVO = sys.argv[1] if len(sys.argv) > 1 else 'y_nova_divida'; SUF = '' if ALVO == 'y_nova_divida' else '_fechou'
PDO, BASE, ODDS_BASE = 20, 600, 20
X = pd.read_parquet(P23 / "p4_X2.parquet", columns=['cnpj_basico', 'parte', 'y_nova_divida', 'y_fechou', *VARIAVEIS])
tr = X.parte.eq('treino').values; te = ~tr; y = X[ALVO].values.astype(int)
yn, yf, cnpj = X.y_nova_divida.values.astype(np.int8), X.y_fechou.values.astype(np.int8), X.cnpj_basico.values
V = pd.DataFrame({v: X[v].astype(object).where(X[v].notna(), 'sem dado').astype(str).astype('category') for v in VARIAVEIS}); del X; gc.collect()   # categorias: cabe na memória da VM
juntar = {v: {} for v in VARIAVEIS}   # faixa -> faixa juntada
def serie(v):   # faixa de cada empresa já com as junções
    c = V[v].cat; return pd.Series(np.array([juntar[v].get(x, x) for x in c.categories], dtype=object)[c.codes.values])
def montar():
    cats, cols, idx = {}, [], []
    off = 0
    for v in VARIAVEIS:
        s = serie(v)
        cont = s[tr].value_counts(); ok = sorted(cont[cont >= 200].index)
        mapa = {c: i for i, c in enumerate(ok)}; rara = len(ok)
        idx.append(s.map(mapa).fillna(rara).astype(np.int32).values + off)
        cats[v] = (off, ok); off += len(ok) + 1
    ind = np.stack(idx, axis=1).ravel(); n, k = len(V), len(VARIAVEIS)
    Z = sparse.csr_matrix((np.ones(len(ind), dtype=np.float64), ind, np.arange(0, n * k + 1, k, dtype=np.int64)), shape=(n, off))
    return Z, cats
for rodada in range(10):
    Z, cats = montar()
    lr = LogisticRegression(C=1.0, max_iter=500).fit(Z[tr], y[tr]); coef = lr.coef_[0]
    mudou = False
    if True:   # mesma regra para as duas notas
        for v, ordem in ORDENADAS.items():
            off, ok = cats[v]; ordem_atual = []
            for c in ordem:
                cj = juntar[v].get(c, c)
                if cj in ok and cj not in ordem_atual: ordem_atual.append(cj)
            for a, b in zip(ordem_atual, ordem_atual[1:]):
                if coef[off + ok.index(b)] < coef[off + ok.index(a)]:   # faixa de mais risco com coeficiente menor: juntar
                    novo = f"{a} / {b}"
                    for c, cj in list(juntar[v].items()) + [(a, a), (b, b)]:
                        if cj in (a, b): juntar[v][c] = novo
                    mudou = True; print('juntando', v, ':', a, '+', b); break
    if not mudou: break
json.dump(juntar, open(RAIZ / f"resultados/p4_scorecard_juncoes{SUF}.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
fator = PDO / np.log(2); offset = BASE - fator * np.log(ODDS_BASE); k = len(VARIAVEIS)
pts = -coef * fator; base_var = (offset - lr.intercept_[0] * fator) / k
linhas, coefs = [], []
for v in VARIAVEIS:
    off, ok = cats[v]; cont = serie(v)[tr].value_counts()
    for i, c in enumerate(ok + ['outras (raras)']):
        n_tr = int(cont.get(c, 0)) if c != 'outras (raras)' else None
        linhas.append(dict(variavel=v, faixa=c, pontos=round(base_var + pts[off + i], 4), empresas_treino=n_tr)); coefs.append(dict(variavel=v, faixa=c, coeficiente=round(coef[off + i], 10)))
tab = pd.DataFrame(linhas); amp = tab[tab.faixa != 'outras (raras)'].groupby('variavel').pontos.agg(lambda s: s.max() - s.min())
tab['amplitude_variavel'] = tab.variavel.map(amp).round(2)
salvar(tab, f"p4_scorecard_pontos{SUF}.csv"); salvar(pd.DataFrame(coefs), f"p4_scorecard_coeficientes{SUF}.csv")
salvar(pd.DataFrame([dict(constante_regressao=lr.intercept_[0], fator=fator, offset=offset, n_variaveis=k, base_por_variavel=base_var,
       PDO=PDO, BASE=BASE, ODDS_BASE=ODDS_BASE, empresas_treino=int(tr.sum()))]).round(6), f"p4_scorecard_constantes{SUF}.csv")
logit = Z @ coef + lr.intercept_[0]; nota = offset - fator * logit; prob = 1 / (1 + np.exp(-logit))
auc = roc_auc_score(y[te], prob[te]); print('AUC teste', round(auc, 4))
cortes = np.quantile(nota[tr], [0.2, 0.4, 0.6, 0.8]); faixa = np.array(['E', 'D', 'C', 'B', 'A'])[np.searchsorted(cortes, nota, side='right')]
pd.DataFrame(dict(corte=['E|D', 'D|C', 'C|B', 'B|A'], nota=cortes)).to_csv(RAIZ / f"resultados/p4_cortes_faixas{SUF}.csv", index=False, float_format='%.17g')
d = pd.DataFrame(dict(cnpj_basico=cnpj, nota=nota.astype(np.float32), pd_prevista=prob.astype(np.float32), faixa=faixa, y_nova_divida=yn, y_fechou=yf, y_alvo=y.astype(np.int8)))
t = d[te]
fx = t.groupby('faixa').agg(empresas=('nota', 'size'), nota_min=('nota', 'min'), nota_max=('nota', 'max'), alvo_previsto_pct=('pd_prevista', lambda s: 100 * s.mean()),
     alvo_real_pct=('y_alvo', lambda s: 100 * s.mean()), nova_divida_pct=('y_nova_divida', lambda s: 100 * s.mean()), fechou_pct=('y_fechou', lambda s: 100 * s.mean())).reset_index()
fx['participacao_maus_pct'] = 100 * t.groupby('faixa').y_alvo.sum().values / t.y_alvo.sum()
salvar(fx.round(4), f"p4_faixas{SUF}.csv"); print(fx.round(2).to_string())   # 4 casas: evita arredondamento duplo no texto
o = t.sort_values('nota', ascending=False); cm = np.cumsum(o.y_alvo.values); cn = np.cumsum(o.y_nova_divida.values); cf = np.cumsum(o.y_fechou.values)
def ponto(a):
    i = int(len(o) * a / 100) - 1
    return dict(aprovacao_pct=a, nota_corte=round(float(o.nota.values[i]), 1), alvo_aprovados_pct=100 * cm[i] / (i + 1), nova_divida_aprovados_pct=100 * cn[i] / (i + 1),
                fechou_aprovados_pct=100 * cf[i] / (i + 1), maus_evitados_pct=100 * (1 - cm[i] / cm[-1]))
salvar(pd.DataFrame([ponto(a) for a in range(10, 101, 10)]).round(4), f"p4_curva_aprovacao{SUF}.csv")
salvar(pd.DataFrame([dict(alvo=ALVO, modelo='Scorecard v2 (tabela simplificada)', grupo='todos', n_teste=int(te.sum()), taxa=y[te].mean(), auc=auc, gini=2 * auc - 1)]).round(4), f"p4_comparacao_{ALVO}_scorecard.csv")
tmp = pathlib.Path.home() / "tmp_notas.parquet"; t.to_parquet(tmp); shutil.move(str(tmp), str(P23 / f"p4_notas_teste{SUF}.parquet"))
# exemplo conta a conta (empresa do teste com nota mais próxima da mediana da faixa C), sem identificação
alvo_c = np.median(nota[te & (faixa == 'C')]); i = int(np.where(te)[0][np.argmin(np.abs(nota[te] - alvo_c))])
ex = []
for v in VARIAVEIS:
    off, ok = cats[v]; c = juntar[v].get(V[v].values[i], V[v].values[i]); j = ok.index(c) if c in ok else len(ok)
    ex.append(dict(variavel=v, faixa=c if c in ok else 'outras (raras)', coeficiente=round(coef[off + j], 6), pontos=round(base_var + pts[off + j], 2)))
ex = pd.DataFrame(ex); salvar(ex, f"p4_exemplo_conta{SUF}.csv"); print('exemplo', round(ex.pontos.sum(), 2), round(float(nota[i]), 2), round(float(prob[i]), 4), faixa[i])
