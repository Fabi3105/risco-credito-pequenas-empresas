# -*- coding: utf-8 -*-
"""P3 — Aplica as duas notas (tabela de pontos v2 publicada) às empresas ativas hoje (amostra de 10%, out/2026).
Saída: dados/processados/p3/p3_notas_<d>.parquet"""
import sys, duckdb, pathlib, shutil
from base import PROC
from p4_tabela import sql_tabela
from p4_pontuar import pontuar
d = sys.argv[1]
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1200MB'")
SEC = "CASE WHEN substr(cnae_principal,1,2) <= '03' THEN 'A' WHEN substr(cnae_principal,1,2) <= '09' THEN 'B' WHEN substr(cnae_principal,1,2) <= '33' THEN 'C' WHEN substr(cnae_principal,1,2) <= '39' THEN 'DE' WHEN substr(cnae_principal,1,2) <= '43' THEN 'F' WHEN substr(cnae_principal,1,2) <= '47' THEN 'G' WHEN substr(cnae_principal,1,2) <= '53' THEN 'H' WHEN substr(cnae_principal,1,2) <= '56' THEN 'I' WHEN substr(cnae_principal,1,2) <= '63' THEN 'J' WHEN substr(cnae_principal,1,2) <= '66' THEN 'K' WHEN substr(cnae_principal,1,2) <= '68' THEN 'L' WHEN substr(cnae_principal,1,2) <= '75' THEN 'M' WHEN substr(cnae_principal,1,2) <= '82' THEN 'N' WHEN substr(cnae_principal,1,2) <= '84' THEN 'O' WHEN substr(cnae_principal,1,2) <= '85' THEN 'P' WHEN substr(cnae_principal,1,2) <= '88' THEN 'Q' WHEN substr(cnae_principal,1,2) <= '93' THEN 'R' ELSE 'S' END"
X = con.execute(sql_tabela(f"read_parquet('{PROC}/p3/p3_base_{d}.parquet')", extras=f"cod_ibge, municipio_rf, grupo_23 grupo, {SEC} secao, substr(cnae_principal, 1, 2) divisao, coalesce(t1_inscricoes, 0) n_inscricoes_pgfn,")).df()
nd, pdv, fd = pontuar(X, ''); nf, pf, ff = pontuar(X, '_fechou')
o = X[['cnpj_basico', 'uf', 'cod_ibge', 'municipio_rf', 'secao', 'divisao', 'grupo', 'n_inscricoes_pgfn', 'regra_politica']].assign(
    nota_divida=nd.astype('float32'), p_divida=pdv.astype('float32'), faixa_divida=fd, nota_fechamento=nf.astype('float32'), p_fechamento=pf.astype('float32'), faixa_fechamento=ff)
tmp = pathlib.Path.home() / f"tmp_p3n_{d}.parquet"; o.to_parquet(tmp); shutil.move(str(tmp), str(PROC / "p3" / f"p3_notas_{d}.parquet"))
print(d, len(o), o.faixa_divida.value_counts(normalize=True).sort_index().round(3).to_dict())
