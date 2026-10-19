# -*- coding: utf-8 -*-
"""Tradução do código de município da Receita para o código do IBGE (UF + nome normalizado), mais população e PIB por ano.
Saídas: dados/processados/municipios_rf_ibge.csv e dados/processados/municipios_ano.parquet (população, PIB, PIB per capita)."""
import json, unicodedata, re, pandas as pd, numpy as np
from base import conectar, PROC, RAIZ, salvar
EXT = RAIZ / "dados/externos"
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]", "", s.replace("D'", "D").replace(" DO ", " ").replace(" DE ", " ").replace(" DA ", " "))
con = conectar()
rf = con.execute("""SELECT b.uf, b.municipio_rf, any_value(m.descricao) nome_rf, count(*) empresas
   FROM base b JOIN aux_municipios m ON lpad(b.municipio_rf::varchar,4,'0') = m.codigo WHERE b.uf <> 'EX' GROUP BY 1, 2""").df()
ib = pd.DataFrame(json.load(open(EXT / "ibge_municipios.json")))[["municipio-id", "municipio-nome", "UF-sigla"]]
ib.columns = ["cod_ibge", "nome_ibge", "uf"]
rf["k"] = rf.uf + "|" + rf.nome_rf.map(norm); ib["k"] = ib.uf + "|" + ib.nome_ibge.map(norm)
m = rf.merge(ib[["k", "cod_ibge", "nome_ibge"]], on="k", how="left")
# nomes que mudaram ou grafias diferentes: correspondência manual (conferida no IBGE)
MANUAL = {("RJ", 5875): 3303807, ("PA", 529): 1506500, ("MG", 4177): 3108909, ("PA", 377): 1502954, ("RN", 1623): 2401206,
          ("RR", 315): 1400605, ("BA", 3869): 2928505, ("TO", 9691): 1720499, ("RN", 1703): 2405306, ("TO", 345): 1708254}
for (uf, cod), ib_cod in MANUAL.items():
    i = (m.uf == uf) & (m.municipio_rf == cod)
    m.loc[i, "cod_ibge"] = ib_cod; m.loc[i, "nome_ibge"] = ib.set_index("cod_ibge").nome_ibge.get(ib_cod)
falta = m[m.cod_ibge.isna()].sort_values("empresas", ascending=False)
print("sem correspondência:", len(falta), "municípios,", int(falta.empresas.sum()), "empresas de", int(m.empresas.sum()))
print(falta.head(40)[["uf", "municipio_rf", "nome_rf", "empresas"]].to_string())
m.drop(columns="k").to_csv(PROC / "municipios_rf_ibge.csv", index=False)

# população por ano (estimativas; 2022 = Censo; 2023 interpolado) e PIB per capita
pop = pd.concat([pd.read_csv(EXT / "ibge_populacao_estimativas.csv"), pd.read_csv(EXT / "ibge_populacao_censo2022.csv")])
pop = pop[pd.to_numeric(pop.valor, errors="coerce").notna()].astype({"valor": float})
pop = pop.pivot_table(index="municipio", columns="ano", values="valor")
pop[2023] = (pop[2022] + pop[2024]) / 2
pib = pd.read_csv(EXT / "ibge_pib_municipios.csv"); pib = pib[pd.to_numeric(pib.valor, errors="coerce").notna()].astype({"valor": float})
pib = pib.pivot_table(index="municipio", columns="ano", values="valor")   # R$ mil, preços correntes
anos = range(2011, 2026)
long = []
for a in anos:
    p_ = pop[a] if a in pop else None
    b_ = pib[min(a, pib.columns.max())]
    long.append(pd.DataFrame({"cod_ibge": pop.index, "ano": a, "populacao": p_.values,
                              "pib_mil": b_.reindex(pop.index).values}))
mu = pd.concat(long); mu["pib_per_capita"] = 1000 * mu.pib_mil / mu.populacao
mu.to_parquet(PROC / "municipios_ano.parquet", index=False)
print("municípios x anos:", len(mu), "| sem população:", int(mu.populacao.isna().sum()), "| sem PIB:", int(mu.pib_mil.isna().sum()))
