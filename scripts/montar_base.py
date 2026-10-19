# -*- coding: utf-8 -*-
"""Monta a tabela de empresas (uma linha por CNPJ básico) juntando matriz, empresa, Simples/MEI, sócios e PGFN.
Roda por partição (primeiro dígito do CNPJ) para caber no limite de memória e de tempo.
Uso: python montar_base.py <digito 0-9>   ->  dados/processados/base/base_<d>.parquet"""
import sys, pathlib, shutil
from base import conectar, PROC
d = sys.argv[1]
con = conectar()
con.execute("SET threads=2; SET memory_limit='2200MB'")
f = f"cnpj_basico LIKE '{d}%'"
out = PROC / "base"; out.mkdir(exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_base_{d}.parquet"
con.execute(f"""COPY (
WITH m AS (SELECT * FROM estab WHERE {f} AND matriz_filial = 1),
fil AS (SELECT cnpj_basico, count(*) - 1 n_filiais FROM estab WHERE {f} GROUP BY 1),
emp AS (SELECT cnpj_basico, any_value(natureza_juridica) natureza_juridica, any_value(qualificacao_responsavel) qualificacao_responsavel, max(capital_social) capital_social, any_value(porte) porte FROM empresas WHERE {f} GROUP BY 1),
sim AS (SELECT * FROM simples WHERE {f}),
soc AS (SELECT cnpj_basico, count(*) n_socios, count(*) FILTER (WHERE tipo_socio = 2) n_socios_pf,
               count(*) FILTER (WHERE tipo_socio = 1) n_socios_pj, min(data_entrada) primeira_entrada_socio
        FROM socios WHERE {f} GROUP BY 1),
pg AS (SELECT cnpj_basico, count(*) n_inscricoes_pgfn, min(data_inscricao) primeira_inscricao_pgfn, sum(valor) valor_pgfn,
              bool_or(ajuizado) pgfn_ajuizado,
              min(data_inscricao) FILTER (WHERE sistema = 'nao_previdenciaria') primeira_inscricao_nao_prev,
              min(data_inscricao) FILTER (WHERE sistema = 'previdenciaria') primeira_inscricao_prev,
              min(data_inscricao) FILTER (WHERE sistema = 'FGTS') primeira_inscricao_fgts
       FROM pgfn WHERE {f} AND upper(tipo_devedor) = 'PRINCIPAL' GROUP BY 1)
SELECT m.cnpj_basico, m.uf, m.municipio_rf, m.data_inicio, m.situacao, m.data_situacao, m.motivo_situacao,
       m.cnae_principal, m.n_cnae_sec, m.tem_email, m.tem_telefone, m.tem_fantasia, m.tem_situacao_especial,
       coalesce(fil.n_filiais, 0) n_filiais,
       emp.natureza_juridica, emp.qualificacao_responsavel, emp.capital_social, emp.porte,
       sim.opcao_simples, sim.data_opcao_simples, sim.data_exclusao_simples, sim.opcao_mei, sim.data_opcao_mei, sim.data_exclusao_mei,
       coalesce(soc.n_socios, 0) n_socios, coalesce(soc.n_socios_pf, 0) n_socios_pf, coalesce(soc.n_socios_pj, 0) n_socios_pj,
       soc.primeira_entrada_socio,
       coalesce(pg.n_inscricoes_pgfn, 0) n_inscricoes_pgfn, pg.primeira_inscricao_pgfn, pg.valor_pgfn, coalesce(pg.pgfn_ajuizado, false) pgfn_ajuizado,
       pg.primeira_inscricao_nao_prev, pg.primeira_inscricao_prev, pg.primeira_inscricao_fgts
FROM m LEFT JOIN fil USING (cnpj_basico) LEFT JOIN emp USING (cnpj_basico) LEFT JOIN sim USING (cnpj_basico)
       LEFT JOIN soc USING (cnpj_basico) LEFT JOIN pg USING (cnpj_basico)
) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)""")
n = con.execute(f"SELECT count(*) FROM '{tmp}'").fetchone()[0]
shutil.move(str(tmp), str(out / f"base_{d}.parquet")); print(d, n)
