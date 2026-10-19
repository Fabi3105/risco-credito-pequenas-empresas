# -*- coding: utf-8 -*-
"""P1 — Quanto tempo as empresas sobrevivem, por porte, setor e cidade; risco de fechar em cada ano de vida.
Tábua de vida anual (método atuarial) sobre as turmas maduras (2012-2021), universo e fechamento de metodos.py.
Saídas em resultados/: q1_tabua_grupo.csv, q1_sobrevivencia_secao.csv, q1_sobrevivencia_uf.csv, q1_sobrevivencia_municipio.csv,
q1_sobrevivencia_divisao.csv, q1_sobrevivencia_turma.csv, q1_sensibilidade.csv"""
import pandas as pd, numpy as np, sys
from base import conectar, salvar, PROC
PQ = PROC / 'q1_turmas.parquet'
import metodos as M
con = conectar()
SECAO = """CASE WHEN d BETWEEN 1 AND 3 THEN 'A' WHEN d BETWEEN 5 AND 9 THEN 'B' WHEN d BETWEEN 10 AND 33 THEN 'C' WHEN d = 35 THEN 'D'
 WHEN d BETWEEN 36 AND 39 THEN 'E' WHEN d BETWEEN 41 AND 43 THEN 'F' WHEN d BETWEEN 45 AND 47 THEN 'G' WHEN d BETWEEN 49 AND 53 THEN 'H'
 WHEN d BETWEEN 55 AND 56 THEN 'I' WHEN d BETWEEN 58 AND 63 THEN 'J' WHEN d BETWEEN 64 AND 66 THEN 'K' WHEN d = 68 THEN 'L'
 WHEN d BETWEEN 69 AND 75 THEN 'M' WHEN d BETWEEN 77 AND 82 THEN 'N' WHEN d = 84 THEN 'O' WHEN d = 85 THEN 'P' WHEN d BETWEEN 86 AND 88 THEN 'Q'
 WHEN d BETWEEN 90 AND 93 THEN 'R' WHEN d BETWEEN 94 AND 96 THEN 'S' WHEN d = 97 THEN 'T' WHEN d = 99 THEN 'U' END"""
if "--montar" in sys.argv:
    con.execute("SET threads=2; SET memory_limit='2200MB'")
    con.execute(f"""COPY (SELECT cnpj_basico, year(data_inicio) turma, {M.GRUPO} grupo, substr(cnae_principal,1,2)::INT d_,
        {M.DURACAO} dur, {M.FECHOU} evento, {M.BAIXA_VOLUNTARIA} ev_vol, {M.BAIXA_OFICIO_MASSA} ev_oficio,
        uf, municipio_rf, cnae_principal, situacao, motivo_situacao, natureza_juridica,
        n_inscricoes_pgfn > 0 tem_pgfn, primeira_inscricao_pgfn, data_inicio, data_situacao,
        capital_social, n_cnae_sec, tem_email, tem_telefone, tem_fantasia, qualificacao_responsavel,
        (data_opcao_simples IS NOT NULL AND data_opcao_simples <= data_inicio + INTERVAL 180 DAY) simples_na_abertura,
        n_socios, n_socios_pj, n_filiais
      FROM base WHERE {M.UNIVERSO} AND year(data_inicio) BETWEEN {M.TURMA_MIN} AND {M.TURMA_MAX})
      TO '{PQ}' (FORMAT parquet)""")
    print("montado", con.execute(f"select count(*) from '{PQ}'").fetchone()); sys.exit()

con.execute(f"CREATE VIEW t AS SELECT * EXCLUDE (d_), d_ AS d, {SECAO.replace('WHEN d', 'WHEN d_')} secao FROM read_parquet('{PQ}')")

def tabua(por, evento="evento", filtro="true", anos=12):
    """Tábua de vida atuarial: para cada grupo e ano de vida k, expostos, fechamentos e risco; sobrevivência acumulada."""
    g = ", ".join(por) if por else "'todos'"
    df = con.execute(f"""SELECT {g + ',' if por else ''} least(floor(dur), {anos})::INT k,
          count(*) FILTER (WHERE {evento}) d, count(*) FILTER (WHERE NOT {evento}) c, count(*) n_k
        FROM t WHERE {filtro} GROUP BY ALL""").df()
    chaves = por if por else []
    out = []
    for key, x in (df.groupby(chaves) if chaves else [(None, df)]):
        x = x.set_index("k").reindex(range(anos + 1), fill_value=0)
        total = x.n_k.sum()
        em_risco = total - x.n_k.cumsum().shift(fill_value=0)
        expostos = em_risco - x.c / 2
        h = (x.d / expostos.replace(0, np.nan)).fillna(0)
        S = (1 - h).cumprod()
        r = pd.DataFrame({"ano_de_vida": range(1, anos + 2), "em_risco_inicio": em_risco.values, "fecharam": x.d.values,
                          "risco_no_ano_pct": 100 * h.values, "sobrevivencia_fim_pct": 100 * S.values})
        if chaves:
            for i, c in enumerate(chaves):
                r.insert(i, c, key[i] if isinstance(key, tuple) else key)
        out.append(r[r.ano_de_vida <= anos])
    return pd.concat(out)

def resumo(tab, por, minimo=0):
    p = tab.pivot_table(index=por, columns="ano_de_vida", values="sobrevivencia_fim_pct")[[1, 2, 3, 5, 10]]
    p.columns = [f"sobrevive_{c}a_pct" for c in p.columns]
    n = tab[tab.ano_de_vida == 1].set_index(por).em_risco_inicio.rename("empresas")
    r = p.join(n).reset_index()
    return r[r.empresas >= minimo].round(1)

tg = tabua(["grupo"]); tt = tabua([])
salvar(pd.concat([tt.assign(grupo="Todas"), tg]).round(2), "q1_tabua_grupo.csv")
salvar(resumo(tabua(["secao", "grupo"]), ["secao", "grupo"], 1000), "q1_sobrevivencia_secao.csv")
salvar(resumo(tabua(["d", "grupo"]), ["d", "grupo"], 2000), "q1_sobrevivencia_divisao.csv")
salvar(resumo(tabua(["uf", "grupo"]), ["uf", "grupo"]), "q1_sobrevivencia_uf.csv")
salvar(resumo(tabua(["turma", "grupo"]), ["turma", "grupo"]), "q1_sobrevivencia_turma.csv")
# sensibilidade: só baixa voluntária; sem as baixas de ofício em massa (tratadas como censura na data)
sens = pd.concat([resumo(tabua(["grupo"]), ["grupo"]).assign(definicao="baixada ou inapta (principal)"),
                  resumo(tabua(["grupo"], evento="ev_vol"), ["grupo"]).assign(definicao="só baixa voluntária"),
                  resumo(tabua(["grupo"], filtro="NOT ev_oficio"), ["grupo"]).assign(definicao="sem baixas de ofício em massa")])
salvar(sens, "q1_sensibilidade.csv")
print(salvar(resumo(tg, ["grupo"]), "q1_resumo_grupo.csv").to_string())
print(sens.to_string())
