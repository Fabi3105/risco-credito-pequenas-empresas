# -*- coding: utf-8 -*-
"""Base "como estava em maio/2023" (uma linha por CNPJ básico), para o desenho de ponto no tempo (P2/P4).
Lê dados/processados_2023-05 (estab, empresas, simples, sócios). PGFN: só inscrições com data anterior a 2023-05-15
(atenção: dívidas quitadas antes de 2026 não aparecem no arquivo de 2026, então essa variável é um piso).
Uso: python montar_base_2023.py <digito 0-9> -> dados/processados_2023-05/base/base_<d>.parquet"""
import sys, pathlib, shutil, duckdb
from base import RAIZ, PROC
P23 = RAIZ / "dados/processados_2023-05"
CORTE = "2023-05-15"
d = sys.argv[1]
con = duckdb.connect()
tmpd = pathlib.Path.home() / "duck_tmp"; tmpd.mkdir(exist_ok=True)
con.execute(f"SET threads=2; SET memory_limit='2200MB'; SET enable_progress_bar=false; SET temp_directory='{tmpd}'; SET preserve_insertion_order=false")
for t in ["estab", "empresas", "simples", "socios"]:
    con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{P23 / t}/*.parquet')")
con.execute(f"CREATE VIEW pgfn AS SELECT * FROM read_parquet('{PROC / 'pgfn'}/*.parquet')")
f = f"cnpj_basico LIKE '{d}%'"
out = P23 / "base"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_base23_{d}.parquet"
con.execute(f"""COPY (
WITH m AS (SELECT * FROM estab WHERE {f} AND matriz_filial = 1),
fil AS (SELECT cnpj_basico, count(*) - 1 n_filiais FROM estab WHERE {f} GROUP BY 1),
emp AS (SELECT cnpj_basico, any_value(natureza_juridica) natureza_juridica, any_value(qualificacao_responsavel) qualificacao_responsavel, max(capital_social) capital_social, any_value(porte) porte FROM empresas WHERE {f} GROUP BY 1),
sim AS (SELECT * FROM simples WHERE {f}),
soc AS (SELECT cnpj_basico, count(*) n_socios, count(*) FILTER (WHERE tipo_socio = 2) n_socios_pf,
               count(*) FILTER (WHERE tipo_socio = 1) n_socios_pj, min(data_entrada) primeira_entrada_socio,
               max(data_entrada) ultima_entrada_socio
        FROM socios WHERE {f} GROUP BY 1),
pg AS (SELECT cnpj_basico, count(*) n_inscricoes_pgfn_23, min(data_inscricao) primeira_inscricao_pgfn_23, sum(valor) valor_pgfn_23
       FROM pgfn WHERE {f} AND upper(tipo_devedor) = 'PRINCIPAL' AND data_inscricao < DATE '{CORTE}' GROUP BY 1)
SELECT m.cnpj_basico, m.uf, m.municipio_rf, m.data_inicio, m.situacao situacao_23, m.data_situacao data_situacao_23, m.motivo_situacao motivo_23,
       m.cnae_principal, m.n_cnae_sec, m.tem_email, m.tem_telefone, m.tem_fantasia, m.tem_situacao_especial,
       coalesce(fil.n_filiais, 0) n_filiais,
       emp.natureza_juridica, emp.qualificacao_responsavel, emp.capital_social, emp.porte,
       sim.opcao_simples, sim.data_opcao_simples, sim.data_exclusao_simples, sim.opcao_mei, sim.data_opcao_mei, sim.data_exclusao_mei,
       coalesce(soc.n_socios, 0) n_socios, coalesce(soc.n_socios_pf, 0) n_socios_pf, coalesce(soc.n_socios_pj, 0) n_socios_pj,
       soc.primeira_entrada_socio, soc.ultima_entrada_socio,
       coalesce(pg.n_inscricoes_pgfn_23, 0) n_inscricoes_pgfn_23, pg.primeira_inscricao_pgfn_23, pg.valor_pgfn_23
FROM m LEFT JOIN fil USING (cnpj_basico) LEFT JOIN emp USING (cnpj_basico) LEFT JOIN sim USING (cnpj_basico)
       LEFT JOIN soc USING (cnpj_basico) LEFT JOIN pg USING (cnpj_basico)
) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)""")
n = con.execute(f"SELECT count(*) FROM '{tmp}'").fetchone()[0]
shutil.move(str(tmp), str(out / f"base_{d}.parquet")); print(d, n)
