# -*- coding: utf-8 -*-
"""C2 — Concorrência local ajustada por população e renda (pedido do Fabian).
Passo 1 (--contar): empresas ativas por município, divisão CNAE e ano (1º de janeiro), universo empresarial.
Passo 2 (padrão): densidade por 10 mil habitantes; densidade esperada para cidades de mesma população e PIB per capita
  (regressão de Poisson por divisão, com efeito de ano); saturação = ativas observadas ÷ esperadas.
  Depois liga cada empresa das turmas 2016-2020 à saturação do seu município e setor no ano de abertura e compara o
  fechamento em 5 anos por faixa de saturação, dentro do mesmo setor e porte (razão observado/esperado)."""
import sys, numpy as np, pandas as pd
from base import conectar, salvar, PROC
import metodos as M, os
N = int(os.environ.get('NIVEL', '2'))   # 2 = divisão CNAE; 3 = grupo CNAE (sensibilidade)
SUF = '' if N == 2 else f'_n{N}'
con = conectar()
CONT = PROC / f"q2_ativas_mun_div_ano{SUF}.parquet"
if "--contar" in sys.argv:
    con.execute("SET threads=2; SET memory_limit='2200MB'")
    con.execute(f"""COPY (
      WITH e AS (SELECT uf, municipio_rf, substr(cnae_principal,1,{N}) divisao, greatest(year(data_inicio), 2010) a_ab,
                        CASE WHEN {M.FECHOU} THEN year(data_situacao) END a_fe
                 FROM base WHERE {M.UNIVERSO}),
      ab AS (SELECT uf, municipio_rf, divisao, a_ab ano, count(*) n FROM e GROUP BY ALL),
      fe AS (SELECT uf, municipio_rf, divisao, greatest(a_fe, 2010) ano, count(*) n FROM e WHERE a_fe IS NOT NULL GROUP BY ALL)
      SELECT coalesce(ab.uf, fe.uf) uf, coalesce(ab.municipio_rf, fe.municipio_rf) municipio_rf, coalesce(ab.divisao, fe.divisao) divisao,
             coalesce(ab.ano, fe.ano) ano, coalesce(ab.n, 0) aberturas, coalesce(fe.n, 0) fechamentos
      FROM ab FULL JOIN fe USING (uf, municipio_rf, divisao, ano)) TO '{CONT}' (FORMAT parquet)""")
    print(con.execute(f"select count(*) from '{CONT}'").fetchone()); sys.exit()

c = pd.read_parquet(CONT).sort_values(["uf", "municipio_rf", "divisao", "ano"])
mp = pd.read_csv(PROC / "municipios_rf_ibge.csv")[["uf", "municipio_rf", "cod_ibge"]]
mu = pd.read_parquet(PROC / "municipios_ano.parquet")
# ativas em 1º de janeiro do ano t = aberturas até t-1 menos fechamentos até t-1 (fechamentos de 2010 e antes juntos)
g = c.groupby(["uf", "municipio_rf", "divisao"])
c["ativas_inicio"] = g.aberturas.cumsum() - c.aberturas - (g.fechamentos.cumsum() - c.fechamentos)
grade = c[c.ano.between(2016, 2020)][["uf", "municipio_rf", "divisao", "ano", "ativas_inicio"]]
# por setor: completa as combinações sem empresa (zero ativas) e ajusta o esperado
#   Poisson por setor: log(E[ativas]) = a + b·log(pop) + c·log(pib pc) + efeito de ano
import statsmodels.api as sm
mun = mp.dropna(subset=["cod_ibge"])
base_mun = mun.assign(k=1).merge(pd.DataFrame({"ano": range(2016, 2021), "k": 1}), on="k").drop(columns="k")
base_mun = base_mun.merge(mu, on=["cod_ibge", "ano"], how="left").dropna(subset=["populacao", "pib_per_capita"])
base_mun["log_pop"] = np.log(base_mun.populacao); base_mun["log_pibpc"] = np.log(base_mun.pib_per_capita)
partes, coefs = [], []
# método de conferência (tabela): faixas de população x quintil de PIB per capita no ano
base_mun["faixa_pop"] = pd.cut(base_mun.populacao, [0, 10e3, 20e3, 50e3, 100e3, 500e3, 1e9],
    labels=["até 10 mil", "10 a 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "mais de 500 mil"]).astype(str)
base_mun["quintil_pibpc"] = base_mun.groupby("ano").pib_per_capita.transform(lambda v: pd.qcut(v, 5, labels=False) + 1)
for div, gx in grade.groupby("divisao"):
    if gx.ativas_inicio.sum() < 500:
        continue
    x = base_mun.merge(gx[["uf", "municipio_rf", "ano", "ativas_inicio"]], on=["uf", "municipio_rf", "ano"], how="left").fillna({"ativas_inicio": 0})
    X = sm.add_constant(pd.concat([pd.get_dummies(x.ano.astype(str), drop_first=True, dtype=float), x[["log_pop", "log_pibpc"]]], axis=1))
    r = sm.GLM(x.ativas_inicio, X, family=sm.families.Poisson()).fit()
    coefs.append({"setor": div, "celulas": len(x), "ativas_total": int(x.ativas_inicio.sum()),
                  "constante": r.params["const"], "coef_log_populacao": r.params["log_pop"], "coef_log_pib_per_capita": r.params["log_pibpc"],
                  **{f"efeito_ano_{c}": r.params[c] for c in r.params.index if c.isdigit()},
                  "desvio_explicado_pct": 100 * (1 - r.deviance / r.null_deviance),
                  "correlacao_obs_esp": np.corrcoef(x.ativas_inicio, r.predict(X))[0, 1]})
    # conferência: taxa por habitante da célula (faixa de população x quintil de renda x ano) vezes a população
    tx = x.groupby(["faixa_pop", "quintil_pibpc", "ano"]).agg(a=("ativas_inicio", "sum"), p=("populacao", "sum")).eval("a / p").rename("taxa_celula")
    x = x.join(tx, on=["faixa_pop", "quintil_pibpc", "ano"])
    x = x[["uf", "municipio_rf", "cod_ibge", "ano", "populacao", "pib_per_capita", "ativas_inicio", "faixa_pop", "quintil_pibpc", "taxa_celula"]].assign(
        divisao=div, esperadas=r.predict(X), elast_pop=r.params["log_pop"], elast_pibpc=r.params["log_pibpc"])
    x["densidade_10mil"] = 1e4 * x.ativas_inicio / x.populacao
    x["esperadas_tabela"] = x.taxa_celula * x.populacao
    partes.append(x.astype({"esperadas": "float32", "densidade_10mil": "float32", "ativas_inicio": "int32", "uf": "category",
                            "faixa_pop": "category", "divisao": "category", "populacao": "float32", "pib_per_capita": "float32",
                            "taxa_celula": "float32", "esperadas_tabela": "float32", "elast_pop": "float32", "elast_pibpc": "float32",
                            "quintil_pibpc": "int8", "ano": "int16"}))
d = pd.concat(partes)
d["saturacao"] = (d.ativas_inicio + 0.5) / (d.esperadas + 0.5)
d["saturacao_tabela"] = (d.ativas_inicio + 0.5) / (d.esperadas_tabela + 0.5)
salvar(pd.DataFrame(coefs).round(5), f"q2_coeficientes_setor{SUF}.csv")
# exemplo de cálculo verificável: Garibaldi-RS (IBGE 4308607), 2020
ex = d[(d.cod_ibge == 4308607) & (d.ano == 2020) & d.divisao.isin(["47", "56", "471", "561"])].merge(
    pd.DataFrame(coefs).rename(columns={"setor": "divisao"}), on="divisao")
if len(ex):
    ex["conta_esperadas"] = np.exp(ex.constante + ex.coef_log_populacao * np.log(ex.populacao)
                                   + ex.coef_log_pib_per_capita * np.log(ex.pib_per_capita) + ex.get("efeito_ano_2020", 0))
    salvar(ex[["divisao", "ano", "populacao", "pib_per_capita", "ativas_inicio", "constante", "coef_log_populacao",
               "coef_log_pib_per_capita", "efeito_ano_2020", "conta_esperadas", "esperadas", "saturacao",
               "faixa_pop", "quintil_pibpc", "taxa_celula", "esperadas_tabela", "saturacao_tabela"]].round(6), f"q2_exemplo_garibaldi{SUF}.csv")
    print(ex[["divisao", "ativas_inicio", "conta_esperadas", "esperadas", "esperadas_tabela"]].round(1).to_string())
d.to_parquet(PROC / f"q2_saturacao{SUF}.parquet", index=False)
salvar(d.groupby("divisao")[["elast_pop", "elast_pibpc"]].first().round(3).reset_index(), f"q2_elasticidades_divisao{SUF}.csv")
print("células município x setor x ano:", len(d), "| saturação mediana:", round(d.saturacao.median(), 2))
